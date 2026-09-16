#!/usr/bin/env python3
"""Harmonogram wyświetlania: co ma być na ekranie i jak długo.

Model jest jeden – **sekwencja kroków**, którą ramka przechodzi w kółko.
Preset to nazwana, gotowa sekwencja; tryb własny to sekwencja edytowalna przez
serwis webowy. Dzięki temu interfejs nie rozdwaja się na dwa osobne tryby.

Podział na dwa źródła jest celowy:

- **presety żyją w tym pliku**, więc przyjeżdżają na ramkę razem z `git pull`;
- **wybór użytkownika żyje w `schedule.json`**, który jest wyłączony z gita.
  Gdyby ten plik był śledzony, pierwsza zmiana ustawień w przeglądarce
  zatrzymałaby `git pull --ff-only` i zepsuła automatyczną aktualizację.

Krok ze zdjęciem może mieć pole `zmieniaj_co` (minuty). Bez niego przez cały krok
wisi jedno zdjęcie; z nim krok rozwija się na kilka krótszych i przy każdym losuje
się nowe. Rozwinięcie dzieje się w jednym miejscu, więc reszta logiki nic o tym
nie wie – widzi po prostu dłuższą sekwencję.

Moduł nie importuje `inky` ani `PIL` – można go uruchomić i przetestować na PC.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "schedule.json"          # wybór użytkownika (poza gitem)
STATE_FILE = BASE_DIR / "output" / "display_state.json"   # gdzie jesteśmy w sekwencji

# Odświeżenie e-papieru trwa kilkadziesiąt sekund, więc krótsze kroki nie mają sensu.
MIN_MINUTY = 2

# Typy kroków rozumiane przez tick.py
TYPY = ("zdjecie", "prognoza")

PRESETY = {
    "glownie_zdjecia": {
        "nazwa": "Głównie zdjęcia",
        "opis": "Zdjęcia zmieniają się co 10 minut, pogoda wchodzi na chwilę.",
        "kroki": [{"typ": "zdjecie", "minuty": 30, "zmieniaj_co": 10},
                  {"typ": "prognoza", "minuty": 5}],
    },
    "po_rowno": {
        "nazwa": "Po równo",
        "opis": "Zdjęcia i prognoza dostają tyle samo czasu.",
        "kroki": [{"typ": "zdjecie", "minuty": 15}, {"typ": "prognoza", "minuty": 15}],
    },
    "tylko_zdjecia": {
        "nazwa": "Tylko zdjęcia",
        "opis": "Ramka na zdjęcia, bez pogody – nowe zdjęcie co 10 minut.",
        "kroki": [{"typ": "zdjecie", "minuty": 30, "zmieniaj_co": 10}],
    },
    "tylko_pogoda": {
        "nazwa": "Tylko pogoda",
        "opis": "Stacja pogodowa, bez zdjęć.",
        "kroki": [{"typ": "prognoza", "minuty": 15}],
    },
    "oszczedny": {
        "nazwa": "Oszczędny",
        "opis": "Najrzadsze odświeżanie – jedno zdjęcie na godzinę, najmniej zużywa panel.",
        "kroki": [{"typ": "zdjecie", "minuty": 60}, {"typ": "prognoza", "minuty": 10}],
    },
    "jak_dotad": {
        "nazwa": "Jak dotąd",
        "opis": "Odtwarza rytm sprzed zmiany: prognoza 8 minut, zdjęcie 2.",
        "kroki": [{"typ": "prognoza", "minuty": 8}, {"typ": "zdjecie", "minuty": 2}],
    },
}

DOMYSLNY_PRESET = "glownie_zdjecia"

USTAWIENIA_AWARYJNE = {
    "aktywny": DOMYSLNY_PRESET,
    "wlasny": [{"typ": "zdjecie", "minuty": 20}, {"typ": "prognoza", "minuty": 5}],
}


def rozwin(kroki):
    """Zamienia kroki ze `zmieniaj_co` na ciąg krótszych kroków.

    Reszta z dzielenia dokleja się do ostatniej części, żeby nie powstawał ogon
    krótszy od `MIN_MINUTY` – przy 30 minutach zmienianych co 7 wychodzi
    7, 7, 7, 9, a nie 7, 7, 7, 7, 2.
    """
    wynik = []
    for krok in kroki:
        co = krok.get("zmieniaj_co")
        if krok["typ"] != "zdjecie" or not co or co >= krok["minuty"]:
            wynik.append({"typ": krok["typ"], "minuty": krok["minuty"]})
            continue
        czesci = [co] * (krok["minuty"] // co)
        reszta = krok["minuty"] - co * len(czesci)
        if not czesci:
            czesci = [krok["minuty"]]
        elif reszta:
            czesci[-1] += reszta
        wynik += [{"typ": "zdjecie", "minuty": m} for m in czesci]
    return wynik


def odswiezen_na_dobe(kroki):
    """Ile razy panel odświeży się w ciągu doby przy tej sekwencji.

    Panel ma skończoną liczbę cykli, więc to realny parametr wyboru presetu –
    serwis webowy pokaże go przy każdej opcji.
    """
    rozwiniete = rozwin(kroki)
    cykl = sum(k["minuty"] for k in rozwiniete)
    if cykl <= 0:
        return 0
    return round(len(rozwiniete) * 24 * 60 / cykl)


def _popraw_kroki(kroki):
    """Odsiewa śmieci z sekwencji. Zwraca None, jeśli nic sensownego nie zostało."""
    if not isinstance(kroki, list):
        return None
    czyste = []
    for krok in kroki:
        if not isinstance(krok, dict) or krok.get("typ") not in TYPY:
            continue
        try:
            minuty = int(krok["minuty"])
        except (KeyError, TypeError, ValueError):
            continue
        czysty = {"typ": krok["typ"], "minuty": max(MIN_MINUTY, minuty)}
        try:
            zmieniaj = int(krok["zmieniaj_co"])
        except (KeyError, TypeError, ValueError):
            zmieniaj = None
        if krok["typ"] == "zdjecie" and zmieniaj:
            czysty["zmieniaj_co"] = max(MIN_MINUTY, zmieniaj)
        czyste.append(czysty)
    return czyste or None


def wczytaj_ustawienia():
    """Zwraca ustawienia użytkownika, uzupełnione o brakujące pola.

    Uszkodzony albo nieistniejący plik nie może zatrzymać ramki – w takim
    wypadku wracamy do ustawień awaryjnych.
    """
    ustawienia = dict(USTAWIENIA_AWARYJNE)
    try:
        zapisane = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ustawienia

    if isinstance(zapisane, dict):
        aktywny = zapisane.get("aktywny")
        if aktywny in PRESETY or aktywny == "wlasny":
            ustawienia["aktywny"] = aktywny
        wlasny = _popraw_kroki(zapisane.get("wlasny"))
        if wlasny:
            ustawienia["wlasny"] = wlasny
    return ustawienia


def zapisz_ustawienia(ustawienia):
    """Zapisuje ustawienia atomowo, żeby tick nigdy nie trafił na połowę pliku."""
    tymczasowy = SETTINGS_FILE.with_suffix(".json.tmp")
    tymczasowy.write_text(
        json.dumps(ustawienia, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tymczasowy.replace(SETTINGS_FILE)


def aktywna_sekwencja(ustawienia=None):
    """Lista kroków wskazana przez bieżące ustawienia.

    Sekwencja własna jest tu walidowana jeszcze raz, bo ustawienia mogą
    przyjść prosto z serwisu webowego, z pominięciem `wczytaj_ustawienia`.
    """
    ustawienia = ustawienia or wczytaj_ustawienia()
    if ustawienia.get("aktywny") == "wlasny":
        return _popraw_kroki(ustawienia.get("wlasny")) or list(
            PRESETY[DOMYSLNY_PRESET]["kroki"]
        )
    preset = PRESETY.get(ustawienia.get("aktywny"), PRESETY[DOMYSLNY_PRESET])
    return list(preset["kroki"])


def _podpis(sekwencja):
    """Stabilny odcisk sekwencji – zmiana ustawień ma natychmiast przerwać krok."""
    return json.dumps(sekwencja, sort_keys=True, ensure_ascii=False)


def _wczytaj_stan():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def zapisz_stan(indeks, sekwencja, teraz=None):
    teraz = teraz or datetime.now()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(
            {"indeks": indeks, "od": teraz.isoformat(timespec="seconds"),
             "podpis": _podpis(sekwencja)},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )


def co_teraz(teraz=None, ustawienia=None):
    """Decyduje, czy trzeba coś przerysować.

    Zwraca `(krok, indeks, sekwencja, powod)`, gdzie `krok` jest `None`, jeśli
    bieżący krok jeszcze się nie wyczerpał i nie ma nic do roboty.
    """
    teraz = teraz or datetime.now()
    sekwencja = rozwin(aktywna_sekwencja(ustawienia))
    stan = _wczytaj_stan()

    if stan is None:
        return sekwencja[0], 0, sekwencja, "pierwsze uruchomienie"

    if stan.get("podpis") != _podpis(sekwencja):
        return sekwencja[0], 0, sekwencja, "zmiana ustawień"

    indeks = stan.get("indeks", 0) % len(sekwencja)
    try:
        od = datetime.fromisoformat(stan["od"])
    except (KeyError, TypeError, ValueError):
        return sekwencja[indeks], indeks, sekwencja, "nieczytelny stan"

    koniec = od + timedelta(minutes=sekwencja[indeks]["minuty"])
    if teraz >= koniec:
        nastepny = (indeks + 1) % len(sekwencja)
        return sekwencja[nastepny], nastepny, sekwencja, "koniec kroku"

    return None, indeks, sekwencja, "krok trwa"
