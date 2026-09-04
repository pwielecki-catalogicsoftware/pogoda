import random
from pathlib import Path

from inky.auto import auto

import config
from image_prep import prepare_photo

# Bazowy katalog skryptu — to zapewni poprawne działanie, gdy cron uruchamia skrypt
BASE_DIR = Path(__file__).resolve().parent
img_folder = BASE_DIR / "static" / "images"

def display_on_epaper(png_path, saturation=None):
    """
    Wyświetla zdjęcie na Inky Impression (auto-detekcja modelu),
    wkadrowane w okno widoczne spod blendy ramki.
    """
    if saturation is None:
        saturation = config.PHOTO_SATURATION

    inky = auto(ask_user=False, verbose=True)  # wykrywa Twój ekran
    inky.set_border(inky.BLACK)

    image = prepare_photo(png_path, inky.resolution)

    try:
        inky.set_image(image, saturation=saturation)
    except TypeError:
        # starsze wersje biblioteki nie mają parametru saturation
        inky.set_image(image)

    inky.show()

def pick_random_image(folder=img_folder, exts=(".png", ".jpg", ".jpeg")):
    """Zwraca losowy plik obrazu z folderu lub None jeśli folder nie istnieje / jest pusty."""
    p = Path(folder)
    if not p.exists() or not p.is_dir():
        # Folder nie istnieje — nie nadpisujemy wygenerowanego obrazu
        return None
    images = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in exts]
    if not images:
        # Brak plików — nic nie robimy
        return None
    return random.choice(images)


def display_random_from_folder(folder=img_folder, exts=(".png", ".jpg", ".jpeg"), saturation=None):
    """Wybiera losowy obraz i wyświetla go. Zwraca ścieżkę do wyświetlonego pliku albo None, jeśli pominięto."""
    png_path = pick_random_image(folder, exts)
    if png_path is None:
        return None
    try:
        display_on_epaper(png_path, saturation=saturation)
        return png_path
    except Exception as e:
        print(f"Nie udało się wyświetlić {png_path}: {e}")
        return None


if __name__ == "__main__":
    displayed = display_random_from_folder()
    if displayed is None:
        print(f"Brak obrazów w katalogu {img_folder}; pomijam wyświetlenie (cron).")
    else:
        print(f"Wybrano i wyświetlono obraz: {displayed}")
