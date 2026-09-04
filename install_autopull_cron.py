#!/usr/bin/env python3
"""Dopisuje do crontaba wpis `@reboot`, który po starcie systemu robi `git pull`.

Idempotentny – uruchomiony drugi raz nic nie zmienia. Istniejące wpisy (render pogody
co 10 minut, losowanie zdjęcia) zostają nietknięte; przed zmianą leci backup do
`my_cron_backup.txt`, tak samo jak w overwrite_cron.py.

Uruchomienie na Pi:
    /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/install_autopull_cron.py
"""

import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
BACKUP_FILE = REPO_DIR / "my_cron_backup.txt"
AUTOPULL_SCRIPT = REPO_DIR / "git_autopull.py"
LOG_FILE = "/tmp/git_autopull.log"

# interpreter, którym cron ma uruchomić skrypt – ten sam, którym uruchomiono instalator
PYTHON = sys.executable

MARKER = "# pogoda: git pull po starcie systemu"
CRON_LINE = f"@reboot {PYTHON} {AUTOPULL_SCRIPT} >> {LOG_FILE} 2>&1"


def read_crontab():
    """Zwraca bieżący crontab. Pusty crontab (kod 1) też jest poprawną sytuacją."""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def write_crontab(content):
    process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    process.communicate(input=content.encode())
    return process.returncode == 0


def main():
    current = read_crontab()

    if MARKER in current or str(AUTOPULL_SCRIPT) in current:
        print("Wpis @reboot już istnieje – nic nie zmieniam.")
        return

    BACKUP_FILE.write_text(current, encoding="utf-8")
    print(f"Backup crona zapisany w: {BACKUP_FILE}")

    updated = current
    if updated and not updated.endswith("\n"):
        updated += "\n"
    updated += f"\n{MARKER}\n{CRON_LINE}\n"

    if write_crontab(updated):
        print(f"Dodano wpis:\n{CRON_LINE}")
    else:
        print("Nie udało się zapisać crontaba – zmiany nie zostały wprowadzone.")


if __name__ == "__main__":
    main()
