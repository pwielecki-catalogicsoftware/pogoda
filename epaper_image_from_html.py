import subprocess
from pathlib import Path
from PIL import Image
from inky.auto import auto


def html_to_png(html_path, output_path, width=800, height=480):
    """
    Konwertuje HTML do PNG przy użyciu Chromium w trybie headless.
    """
    html_path = Path(html_path).resolve()
    output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Chromium wymaga absolutnego file:// do plików lokalnych
    html_url = f"file://{html_path}"

    cmd = [
        "chromium",
        "--headless",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-sync",
        "--disable-background-networking",
        "--disable-component-update",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        html_url
    ]

    subprocess.run(cmd, check=True)


def display_on_epaper(png_path, saturation=0.5):
    """
    Wyświetla obraz PNG na Inky Impression (auto-detekcja modelu).
    """
    inky = auto(ask_user=False, verbose=True)
    inky.set_border(inky.BLACK)

    image = Image.open(png_path)
    image = image.resize(inky.resolution)

    try:
        inky.set_image(image, saturation=saturation)
    except TypeError:
        inky.set_image(image)

    inky.show()


def render_html_to_epaper(html_path, png_path, width=800, height=480):
    html_to_png(html_path, png_path, width, height)
    display_on_epaper(png_path)
