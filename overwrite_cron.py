#!/usr/bin/env python3
import subprocess
import os

# Ścieżka do katalogu repozytorium (tam, gdzie jest ten skrypt)
repo_path = os.path.dirname(os.path.abspath(__file__))
backup_file = os.path.join(repo_path, "my_cron_backup.txt")

# 1. Backup aktualnego crontaba
subprocess.run(f"crontab -l > {backup_file}", shell=True, check=True)
print(f"Backup crona zapisany w: {backup_file}")

# 2. Nowy crontab (tutaj wpisz swoje zadania)
# new_cron = """
# # Przykładowy wpis: 14 lutego o 11:00
# 0 11 14 2 * /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/walentynkowy.py
# 0 0 15 2 * /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/restore_cron.py
# """

new_cron = """
# Wprawka
34 15 6 2 * /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/walentynkowy.py
37 15 6 2 * /home/piter/.virtualenvs/pimoroni/bin/python /home/piter/repo/pogoda/restore_cron.py
"""



# 3. Nadpisanie crontaba nowym wpisem
process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
process.communicate(input=new_cron.encode())

print("Crontab został nadpisany nowymi zadaniami.")
