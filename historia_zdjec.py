#!/usr/bin/env python3
"""Pamięć ostatnio pokazanych zdjęć, żeby losowanie się nie powtarzało.

Bez niej naciśnięcie kafelka „zdjęcie" na pilocie potrafi po kilkudziesięciu
sekundach renderu pokazać dokładnie to samo zdjęcie – a z drugiego pokoju
wygląda to jak zepsuty pilot. Z harmonogramem jest tak samo, tylko rzadziej
boli, więc pamięć działa dla obu dróg.

Wykluczamy ostatnie `config.ZDJECIA_BEZ_POWTORKI` nazw, ale nigdy wszystkich
kandydatów: przy galerii mniejszej niż pamięć zostaje przynajmniej jedno
zdjęcie do wylosowania.

Moduł nie importuje `inky` ani `PIL`, więc da się go sprawdzić na PC.
"""

import json
import random
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent
PLIK = BASE_DIR / "output" / "ostatnie_zdjecia.json"


def wczytaj(plik=PLIK):
    """Lista nazw, od najstarszej. Uszkodzony plik to po prostu pusta pamięć."""
    try:
        dane = json.loads(Path(plik).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [n for n in dane if isinstance(n, str)] if isinstance(dane, list) else []


def zapamietaj(nazwa, plik=PLIK, pamiec=None):
    """Dopisuje pokazane zdjęcie i przycina pamięć do zadanej długości."""
    pamiec = config.ZDJECIA_BEZ_POWTORKI if pamiec is None else pamiec
    historia = [n for n in wczytaj(plik) if n != nazwa]
    historia.append(nazwa)
    plik = Path(plik)
    plik.parent.mkdir(parents=True, exist_ok=True)
    tymczasowy = plik.with_suffix(".json.tmp")
    tymczasowy.write_text(
        json.dumps(historia[-max(1, pamiec):], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tymczasowy.replace(plik)
    return historia


def wybierz(kandydaci, historia=None, pamiec=None):
    """Losuje spośród kandydatów (lista ścieżek), omijając ostatnio pokazane.

    Funkcja czysta – nic nie czyta z dysku, więc testuje się ją jedną linijką.
    """
    kandydaci = list(kandydaci)
    if not kandydaci:
        return None
    pamiec = config.ZDJECIA_BEZ_POWTORKI if pamiec is None else pamiec
    historia = list(historia or [])

    # Nigdy nie wykluczamy wszystkiego: przy dwóch zdjęciach pamiętamy jedno.
    limit = max(0, min(pamiec, len(kandydaci) - 1))
    if limit:
        ostatnie = set(historia[-limit:])
        swieze = [k for k in kandydaci if Path(k).name not in ostatnie]
        if swieze:
            return random.choice(swieze)
    return random.choice(kandydaci)
