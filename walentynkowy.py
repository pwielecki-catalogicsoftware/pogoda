from pathlib import Path
from PIL import Image
from inky.auto import auto
import random

# Bazowy katalog skryptu — to zapewni poprawne działanie, gdy cron uruchamia skrypt
BASE_DIR = Path(__file__).resolve().parent
img_folder = BASE_DIR / "static" / "images"

def display_on_epaper(png_path, saturation=0.5):
    """
    Wyświetla obraz PNG na Inky Impression (auto-detekcja modelu).
    """
    inky = auto(ask_user=False, verbose=True)  # wykrywa Twój ekran
    inky.set_border(inky.BLACK)

    image = Image.open(png_path)
    image = image.resize(inky.resolution)  # dopasowanie do fizycznego ekranu

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
