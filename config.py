# plik konfiguracyjny zawierający postawowe stałe stosowane w projekcie

import os

# lokalizacja folderu, w którym jest ten plik config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# lokalizacja pliku docelowego
output_file_current = f"{BASE_DIR}{os.sep}output{os.sep}pogoda_teraz.html"
output_file_forecast = f"{BASE_DIR}{os.sep}output{os.sep}pogoda_potem.html"

output_png_current = f"{BASE_DIR}{os.sep}output{os.sep}pogoda_teraz.png"
output_png_forecast = f"{BASE_DIR}{os.sep}output{os.sep}pogoda_potem.png"


# Współrzędne dla Komputerowej 8 w Warszawie
LAT = "52.2091"
LON = "20.9835"

UNITS = "metric"
LANG = "pl"

BASE_URL = "https://api.openweathermap.org/data/2.5/"

