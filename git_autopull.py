#!/usr/bin/env python3
"""Automatyczny `git pull` po starcie systemu.

Czeka, aż Pi nawiąże połączenie z siecią, po czym aktualizuje repozytorium z jego
zdalnego źródła. Gałąź nie jest sprawdzana ani zmieniana – zakładamy, że urządzenie
stoi na właściwej.

Skrypt jest celowo "cichy w porażce": każdy błąd (brak sieci, brak gałęzi zdalnej,
rozjechane commity lokalne, brak gita) jest tylko logowany, a proces kończy się
kodem 0. Nic, co dzieje się tutaj, nie może zablokować startu stacji pogodowej.

Uruchomienie samodzielne (np. z crona `@reboot`):
    /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/git_autopull.py

Albo z innego modułu:
    from git_autopull import autopull
    autopull()
"""

import os
import socket
import subprocess
import time
from pathlib import Path

# katalog repozytorium = katalog tego pliku
REPO_DIR = Path(__file__).resolve().parent

# host używany do stwierdzenia, że sieć działa (samo połączenie TCP, bez wysyłania danych)
NETWORK_PROBE = ("github.com", 443)
PROBE_TIMEOUT = 5           # sekundy na pojedynczą próbę połączenia
NETWORK_WAIT_TOTAL = 180    # jak długo maksymalnie czekamy na sieć po starcie systemu
NETWORK_RETRY_DELAY = 5     # przerwa między próbami
GIT_TIMEOUT = 120           # limit czasu na samo `git pull`


def log(message):
    text = f"[git_autopull] {message}"
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        # konsola bez UTF-8 (np. cp1252 na Windowsie) nie może wywrócić skryptu
        print(text.encode("ascii", "replace").decode("ascii"), flush=True)


def network_is_up(probe=NETWORK_PROBE, timeout=PROBE_TIMEOUT):
    """Czy da się otworzyć połączenie TCP do hosta kontrolnego."""
    try:
        with socket.create_connection(probe, timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_network(total_wait=NETWORK_WAIT_TOTAL, retry_delay=NETWORK_RETRY_DELAY):
    """Czeka na sieć. Zwraca True, jeśli się pojawiła w wyznaczonym czasie."""
    deadline = time.monotonic() + total_wait
    while True:
        if network_is_up():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(retry_delay)


def git_pull(repo_dir=REPO_DIR, timeout=GIT_TIMEOUT):
    """Wykonuje `git pull` w repozytorium. Zwraca True przy powodzeniu."""
    env = dict(os.environ)
    # bez tego git potrafi zawisnąć, czekając na login do zdalnego repozytorium
    env["GIT_TERMINAL_PROMPT"] = "0"

    result = subprocess.run(
        ["git", "-C", str(repo_dir), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        log(f"Aktualizacja zakończona powodzeniem: {output or 'brak zmian'}")
        return True
    log(f"`git pull` zwrócił kod {result.returncode}: {output or 'brak komunikatu'}")
    return False


def autopull(repo_dir=REPO_DIR):
    """Pełny przebieg: poczekaj na sieć i zaktualizuj repo. Nigdy nie rzuca wyjątkiem."""
    try:
        if not wait_for_network():
            log(f"Brak sieci po {NETWORK_WAIT_TOTAL} s – pomijam aktualizację.")
            return False
        return git_pull(repo_dir)
    except subprocess.TimeoutExpired:
        log(f"`git pull` przekroczył {GIT_TIMEOUT} s – przerwane.")
    except FileNotFoundError:
        log("Nie znaleziono polecenia `git` – pomijam aktualizację.")
    except Exception as e:
        log(f"Nieoczekiwany błąd aktualizacji ({type(e).__name__}): {e}")
    return False


if __name__ == "__main__":
    autopull()
