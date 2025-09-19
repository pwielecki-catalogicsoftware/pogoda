from html2image import Html2Image
from pathlib import Path

# katalog docelowy dla plików PNG
hti = Html2Image(output_path=str(Path(__file__).parent / '..' / 'output'))

def html_to_png(html_file, png_file):
    # wczytanie HTML
    with open(html_file, encoding='utf-8') as f:
        html_content = f.read()

    # generowanie PNG
    hti.screenshot(
        html_str=html_content,
        save_as=png_file,
        size=(800, 600),
        base_url=str(Path(__file__).parent / '..' / 'static')  # baza dla ścieżek względnych do CSS i ikon
    )
