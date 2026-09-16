#!/usr/bin/env python3
"""Jeden takt harmonogramu – uruchamiany z crona co minutę.

Skrypt sprawdza, czy bieżący krok sekwencji się wyczerpał. Jeśli nie, kończy się
po ułamku sekundy, nie dotykając ekranu ani nie importując ciężkich modułów.
Jeśli tak – rysuje następny krok.

Dlaczego takt z crona, a nie demon żyjący non stop: proces, który kończy się po
każdym takcie, nie ma jak spuchnąć na 512 MB pamięci, a gdy raz padnie, następna
minuta i tak go naprawi. Demon, który padłby w nocy, zostawiłby zamrożoną ramkę
do rana. Czasy trwania i tak nie mieszczą się w składni crontaba (cykl 35 minut
nie da się zapisać jako `*/35`), więc decyzja siedzi tutaj, a cron tylko tyka.

Uruchomienie z crona:
    * * * * * /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/tick.py >> /tmp/tick.log 2>&1

Wymuszenie natychmiastowego przerysowania (użyje tego serwis webowy):
    python tick.py --force
"""

import sys
from datetime import datetime
from pathlib import Path

import display_schedule as ds

BASE_DIR = Path(__file__).resolve().parent
LOCK_FILE = BASE_DIR / "output" / ".tick.lock"


def log(message):
    text = f"[tick] {datetime.now():%Y-%m-%d %H:%M:%S} {message}"
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        # konsola bez UTF-8 nie może wywrócić skryptu
        print(text.encode("ascii", "replace").decode("ascii"), flush=True)


class Blokada:
    """Gwarantuje, że tylko jeden takt naraz rysuje po ekranie.

    Render pogody bywa dłuższy niż minuta, a serwis webowy może wywołać takt
    poza kolejnością – dwa procesy piszące jednocześnie po SPI to artefakty
    albo zawieszony ekran.
    """

    def __init__(self, sciezka):
        self.sciezka = sciezka
        self.uchwyt = None

    def __enter__(self):
        self.sciezka.parent.mkdir(parents=True, exist_ok=True)
        self.uchwyt = open(self.sciezka, "w")
        try:
            import fcntl
        except ImportError:
            return True          # Windows – i tak nie ma czym rysować
        try:
            fcntl.flock(self.uchwyt, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.uchwyt.close()
            self.uchwyt = None
            return False
        return True

    def __exit__(self, *wyjatek):
        if self.uchwyt:
            self.uchwyt.close()
        return False


def renderuj(typ):
    """Rysuje jeden krok. Ciężkie moduły importujemy dopiero tutaj."""
    if typ == "prognoza":
        from config import output_file_forecast, output_png_forecast
        from generate_forecast_html import generate_forecast_html
        from epaper_image_from_html import render_html_to_epaper

        generate_forecast_html(output_file_forecast)
        render_html_to_epaper(output_file_forecast, output_png_forecast)
        return True

    if typ == "zdjecie":
        from epaper_image_from_image import display_random_from_folder

        wyswietlone = display_random_from_folder()
        if wyswietlone is None:
            log("brak zdjęć w katalogu – nic nie pokazano")
            return False
        log(f"pokazano zdjęcie: {wyswietlone.name}")
        return True

    log(f"nieznany typ kroku: {typ}")
    return False


def main():
    wymuszenie = "--force" in sys.argv

    with Blokada(LOCK_FILE) as wolne:
        if not wolne:
            log("inny takt trwa – pomijam")
            return 0

        krok, indeks, sekwencja, powod = ds.co_teraz()

        if krok is None and not wymuszenie:
            return 0
        if krok is None:
            indeks = indeks % len(sekwencja)
            krok, powod = sekwencja[indeks], "wymuszone"

        log(f"krok {indeks + 1}/{len(sekwencja)}: {krok['typ']} "
            f"na {krok['minuty']} min ({powod})")

        # Stan zapisujemy niezależnie od wyniku renderu. Gdyby zapis zależał od
        # powodzenia, pusty katalog zdjęć zatrzymałby sekwencję na zawsze i ramka
        # nigdy nie doszłaby do prognozy.
        ds.zapisz_stan(indeks, sekwencja)

        try:
            renderuj(krok["typ"])
        except Exception as blad:
            log(f"render nie powiódł się: {blad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
