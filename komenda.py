#!/usr/bin/env python3
"""Stan ostatniej komendy z pilota (zegarka).

Pilot zleca render i nie czeka na wynik: odświeżenie e-papieru trwa kilkadziesiąt
sekund, a zegarek zdąży w tym czasie zgasnąć. Wynik musi więc gdzieś poczekać –
leży w `output/komenda.json`, skąd czyta go `GET /stan` przy następnym wejściu
na ekran ramki.

Podział ról jest taki sam jak w całym projekcie: **serwis webowy nie rysuje**.
Zapisuje „zlecone" i odpala takt; takt dopisuje „gotowe" albo „blad".

Ten sam plik niesie limit tempa. Każde zlecenie to pełne odświeżenie panelu,
a pilot kusi do klikania – `za_wczesnie()` pilnuje odstępu z `config`.

Moduł nie importuje `inky` ani `PIL`, więc uruchomi się i na PC.
"""

import json
from datetime import datetime
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent
PLIK = BASE_DIR / "output" / "komenda.json"

ZLECONE = "zlecone"      # przyjęte, render w drodze
GOTOWE = "gotowe"        # narysowane
BLAD = "blad"            # render się nie udał
PRZEPADLO = "przepadlo"  # nigdy nie zapisywane – wyliczane, gdy wynik nie przyszedł


def wczytaj():
    """Ostatni zapis albo None. Uszkodzony plik nie może wywrócić serwisu."""
    try:
        dane = json.loads(PLIK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dane if isinstance(dane, dict) else None


def _zapisz(dane):
    """Zapis atomowy – takt i serwis czytają ten plik bez żadnej blokady."""
    PLIK.parent.mkdir(parents=True, exist_ok=True)
    tymczasowy = PLIK.with_suffix(".json.tmp")
    tymczasowy.write_text(
        json.dumps(dane, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tymczasowy.replace(PLIK)


def zapisz_zlecenie(co, teraz=None):
    """Serwis przyjął komendę i odpala takt."""
    teraz = (teraz or datetime.now()).isoformat(timespec="seconds")
    _zapisz({"co": co, "stan": ZLECONE, "opis": "", "zlecono": teraz,
             "zmieniono": teraz})


def zapisz_wynik(stan, opis="", teraz=None):
    """Takt dopisuje, czym się skończyło – `zlecono` zostaje nietknięte,
    bo od niego liczy się limit tempa."""
    dane = wczytaj() or {}
    teraz = (teraz or datetime.now()).isoformat(timespec="seconds")
    _zapisz({"co": dane.get("co", ""), "stan": stan, "opis": opis,
             "zlecono": dane.get("zlecono", teraz), "zmieniono": teraz})


def _wiek_s(dane, pole, teraz=None):
    try:
        kiedy = datetime.fromisoformat(dane[pole])
    except (KeyError, TypeError, ValueError):
        return None
    return int(((teraz or datetime.now()) - kiedy).total_seconds())


def trwa(teraz=None):
    """Czy render z pilota jest w drodze. Stare „zlecone" nie liczy się –
    takt zabity w połowie nie ma prawa zablokować pilota na zawsze."""
    dane = wczytaj()
    if not dane or dane.get("stan") != ZLECONE:
        return False
    wiek = _wiek_s(dane, "zmieniono", teraz)
    return wiek is not None and wiek < config.POKAZ_MAX_CZAS_S


def za_wczesnie(teraz=None):
    """Ile sekund zostało do końca limitu tempa (0 = można zlecać).

    Wynik jest przycięty do samego odstępu, żeby cofnięty zegar systemowy nie
    zamknął pilota na wiele godzin.
    """
    dane = wczytaj()
    if not dane:
        return 0
    minelo = _wiek_s(dane, "zlecono", teraz)
    if minelo is None:
        return 0
    return min(config.POKAZ_ODSTEP_S, max(0, config.POKAZ_ODSTEP_S - minelo))


def podsumowanie(teraz=None):
    """Co powiedzieć pytającemu o `/stan`. None, gdy pilot jeszcze nic nie zlecał."""
    dane = wczytaj()
    if not dane:
        return None
    stan = dane.get("stan", "")
    wiek = _wiek_s(dane, "zmieniono", teraz)
    if stan == ZLECONE and (wiek is None or wiek >= config.POKAZ_MAX_CZAS_S):
        # wynik nigdy nie przyszedł – mówimy to wprost, zamiast udawać, że render trwa
        stan, dane = PRZEPADLO, {**dane, "opis": "render nie zgłosił wyniku"}
    return {"co": dane.get("co", ""), "stan": stan, "opis": dane.get("opis", ""),
            "wiek_s": wiek}
