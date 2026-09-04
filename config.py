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



# --- Blenda ramki -------------------------------------------------------------
# Ekran jest przyklejony do płytki niesymetrycznie, więc po osadzeniu w ramce
# passe-partout zasłania nierówno: z lewej więcej niż z prawej, u góry sporo,
# u dołu nic. Wartości dobrane doświadczalnie na sprzęcie.
#
# Wartości nie są przeliczone z CSS-a "na papierze", tylko ZMIERZONE na gotowym
# renderze pogody (output/pogoda_potem.png): prostokąt tła zajmuje tam dokładnie
# x 55..751, y 33..479. Zdjęcia mają trafiać w ten sam prostokąt co do piksela.
#
# UWAGA: te same offsety są zapisane procentowo w static/style.css
# (`margin: 4.1% 6% 0% 6.875%`) dla ekranów pogody. CSS nie czyta tego pliku –
# zmieniając jedno, popraw drugie i przepuść check_frame_geometry.py.

PANEL_SIZE = (800, 480)          # natywna rozdzielczość Inky Impression 7.3"

BLEND_LEFT = 55                  # 6.875% z 800
BLEND_RIGHT = 48                 # 6% z 800
BLEND_TOP = 33                   # 4.1% z 800 – w CSS margin % liczy się od szerokości
BLEND_BOTTOM = 0                 # ekran sięga dolnej krawędzi okna ramki

# Widoczne okno: 697 x 447 px, proporcja 1.559 (panel ma 1.667, zdjęcia 3:2 – 1.500)
VISIBLE_SIZE = (
    PANEL_SIZE[0] - BLEND_LEFT - BLEND_RIGHT,
    PANEL_SIZE[1] - BLEND_TOP - BLEND_BOTTOM,
)

# --- Przygotowanie zdjęć pod e-papier -----------------------------------------
# Kadrowanie "cover": zdjęcie wypełnia całe okno, nadmiar jest obcinany.
# Pion centrujemy powyżej środka, bo twarze rzadko wypadają w połowie kadru.
PHOTO_CENTERING = (0.5, 0.4)

# Parametry dobrane na oko – do przetestowania na ramce i podkręcenia.
PHOTO_UNSHARP = (1.2, 80, 3)     # promień, siła %, próg – po redukcji 6000 -> 800 px
PHOTO_CONTRAST = 1.15            # 1.0 = bez zmian; paleta e-papieru spłaszcza kontrast
PHOTO_SATURATION = 0.5           # przekazywane do inky.set_image()
