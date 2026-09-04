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


if __name__ == "__main__":
    displayed = display_on_epaper(img_folder / "EWA_i_PIOTR_Bobrowy_walentynkowy.jpg")
    if displayed is None:
        print(f"Brak obrazów w katalogu {img_folder}; pomijam wyświetlenie (cron).")
    else:
        print(f"Wybrano i wyświetlono obraz: {displayed}")
