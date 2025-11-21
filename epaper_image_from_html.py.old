import subprocess
from pathlib import Path
from PIL import Image
from inky.auto import auto
# from inky import Inky_Impressions_7 # from inky import InkyPHAT  # lub inny sterownik do Twojego e-papera

# def html_to_png(html_path, output_path, width=800, height=480):
#     """
#     Konwertuje HTML do PNG przy użyciu Chromium w trybie headless.
#     """
#     cmd = [
#         "chromium-browser",
#         "--headless",
#         "--disable-gpu",
#         "--disable-sync",
#         "--disable-background-networking",
#         "--disable-component-update",
#         f"--window-size={width},{height}",
#         "--hide-scrollbars",
#         f"--screenshot={output_path}",
#         str(html_path)
#     ]
#     subprocess.run(cmd, check=True)


def html_to_png_wkhtmltoimage(html_path, png_path, width=800, height=480):
    Path(png_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "wkhtmltoimage",
        "--width", str(width),
        "--height", str(height),
        "--enable-local-file-access",
        "--quiet",  # wycisza logi
        str(html_path),
        str(png_path)
    ]
    subprocess.run(cmd, check=True)


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

def render_html_to_epaper(html_path, png_path, width=800, height=480):
    # html_to_png(html_path, png_path, width, height)
    html_to_png_wkhtmltoimage(html_path, png_path, width, height)
    display_on_epaper(png_path)
