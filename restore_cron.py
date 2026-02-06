#!/usr/bin/env python3
import subprocess
import os

# Ścieżka do katalogu repozytorium
repo_path = os.path.dirname(os.path.abspath(__file__))
backup_file = os.path.join(repo_path, "my_cron_backup.txt")

# Przywrócenie crontaba z backupu
subprocess.run(f"crontab {backup_file}", shell=True, check=True)
print(f"Crontab przywrócony z backupu: {backup_file}")
