from pathlib import Path
from PIL import Image
from inky.auto import auto

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

display_on_epaper("static\images\EWA_i_PIOTR_Bobrowy_Dwor_HIGHRES_19102025_0280.jpg")