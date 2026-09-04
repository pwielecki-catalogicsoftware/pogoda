"""Przygotowanie zdjęcia do wyświetlenia na e-papierze osadzonym w ramce.

Moduł celowo nie importuje `inky`, żeby dało się go uruchomić i obejrzeć wynik
na zwykłym komputerze – patrz blok `__main__` na końcu pliku.
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

import config


def prepare_photo(path, panel_size=None):
    """Zwraca obraz w rozmiarze panelu, ze zdjęciem wkadrowanym w okno blendy.

    Zdjęcie jest kadrowane metodą "cover": wypełnia całe widoczne okno, a nadmiar
    zostaje obcięty – bez czarnych pasów i bez rozciągania proporcji. Obszar pod
    blendą zostaje czarny, bo i tak go nie widać.
    """
    panel_size = tuple(panel_size or config.PANEL_SIZE)
    left, top = config.BLEND_LEFT, config.BLEND_TOP

    if panel_size != tuple(config.PANEL_SIZE):
        # Inny model ekranu niż ten, na którym mierzono blendę – przeskaluj offsety,
        # żeby zdjęcie nie wyszło poza panel. Wartości i tak trzeba zmierzyć na nowo.
        sx = panel_size[0] / config.PANEL_SIZE[0]
        sy = panel_size[1] / config.PANEL_SIZE[1]
        left, top = round(left * sx), round(top * sy)
        window = (
            panel_size[0] - left - round(config.BLEND_RIGHT * sx),
            panel_size[1] - top - round(config.BLEND_BOTTOM * sy),
        )
    else:
        window = config.VISIBLE_SIZE

    image = Image.open(path)

    # Każe libjpeg zdekodować JPEG od razu w zmniejszonej skali. Bez tego zdjęcie
    # 6000x4000 zajmuje 72 MB w pamięci, a Pi Zero 2 W ma jej 512 MB.
    image.draft("RGB", window)

    # Aparat zapisuje orientację w EXIF zamiast obracać piksele.
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    image = ImageOps.fit(
        image, window, method=Image.LANCZOS, centering=config.PHOTO_CENTERING
    )

    # Po tak dużej redukcji obraz jest miękki; e-papier dodatkowo zjada detal.
    radius, percent, threshold = config.PHOTO_UNSHARP
    image = image.filter(ImageFilter.UnsharpMask(radius, percent, threshold))

    if config.PHOTO_CONTRAST != 1.0:
        image = ImageEnhance.Contrast(image).enhance(config.PHOTO_CONTRAST)

    canvas = Image.new("RGB", panel_size, (0, 0, 0))
    canvas.paste(image, (left, top))
    return canvas


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Uzycie: python image_prep.py <zdjecie> [plik_wynikowy.png]")
        raise SystemExit(1)

    source = Path(sys.argv[1])
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else source.with_name(
        f"{source.stem}_podglad.png"
    )
    prepare_photo(source).save(target)
    print(f"Zapisano podglad: {target}")
