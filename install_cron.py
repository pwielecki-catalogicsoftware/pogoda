#!/usr/bin/env python3
"""Ustawia wszystkie wpisy crona projektu – zastępuje install_autopull_cron.py.

Wpisy projektu żyją w jednym bloku między markerami. Instalator wymienia cały
blok, a reszty crontaba nie tyka, więc jest idempotentny: uruchomiony drugi raz
zostawia dokładnie ten sam stan.

Przy okazji usuwa wpisy z poprzedniego układu – render pogody i losowanie zdjęcia
co 10 minut. Od teraz o tym, co jest na ekranie, decyduje `tick.py` na podstawie
sekwencji z `display_schedule.py`; cron tylko tyka co minutę.

Uruchomienie na Pi:
    /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/install_cron.py
"""

import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
BACKUP_FILE = REPO_DIR / "my_cron_backup.txt"

# interpreter, którym cron ma uruchamiać skrypty – ten sam, którym uruchomiono instalator
PYTHON = sys.executable

POCZATEK = "# >>> pogoda – wpisy zarządzane przez install_cron.py >>>"
KONIEC = "# <<< pogoda <<<"

WPISY = [
    ("# aktualizacja repozytorium po starcie systemu",
     f"@reboot {PYTHON} {REPO_DIR / 'git_autopull.py'} >> /tmp/git_autopull.log 2>&1"),
    ("# takt harmonogramu – sam decyduje, czy jest co rysować",
     f"* * * * * {PYTHON} {REPO_DIR / 'tick.py'} >> /tmp/tick.log 2>&1"),
]

# Wpisy z poprzedniego układu – do usunięcia, bo ich zadanie przejął tick.py.
PRZESTARZALE = (
    "main.py",
    "epaper_image_from_image.py",
    "git_autopull.py",
    "# pogoda: git pull po starcie systemu",
)


def czytaj_crontab():
    """Pusty crontab (kod wyjścia 1) też jest poprawną sytuacją."""
    wynik = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return wynik.stdout if wynik.returncode == 0 else ""


def zapisz_crontab(tresc):
    proces = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    proces.communicate(input=tresc.encode())
    return proces.returncode == 0


def bez_starego_bloku(linie):
    """Wycina poprzedni blok projektu wraz z markerami."""
    wynik, w_bloku = [], False
    for linia in linie:
        if linia.strip() == POCZATEK:
            w_bloku = True
            continue
        if linia.strip() == KONIEC:
            w_bloku = False
            continue
        if not w_bloku:
            wynik.append(linia)
    return wynik


def main():
    biezacy = czytaj_crontab()
    BACKUP_FILE.write_text(biezacy, encoding="utf-8")
    print(f"Backup crona zapisany w: {BACKUP_FILE}")

    linie = bez_starego_bloku(biezacy.splitlines())

    zachowane, usuniete = [], []
    for linia in linie:
        if any(wzorzec in linia for wzorzec in PRZESTARZALE):
            usuniete.append(linia)
        else:
            zachowane.append(linia)

    while zachowane and not zachowane[-1].strip():
        zachowane.pop()

    blok = [POCZATEK]
    for komentarz, wpis in WPISY:
        blok += [komentarz, wpis]
    blok.append(KONIEC)

    nowy = "\n".join(zachowane + [""] + blok) + "\n"

    if not zapisz_crontab(nowy):
        print("Nie udało się zapisać crontaba – nic nie zmieniono.")
        return 1

    for linia in usuniete:
        print(f"Usunięto stary wpis: {linia.strip()}")
    print(f"Zainstalowano {len(WPISY)} wpisy projektu:")
    for _, wpis in WPISY:
        print(f"  {wpis}")
    print(f"Wpisy spoza projektu zachowane: {len([l for l in zachowane if l.strip()])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
