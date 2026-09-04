"""Sprawdza, czy zdjęcia trafiają dokładnie w ten sam prostokąt co ekrany pogody.

Układ pogody jest wyklikany w CSS-ie procentowo i działa co do piksela, więc to on
jest wzorcem. Skrypt mierzy prostokąt tła na gotowym renderze pogody, porównuje go
ze stałymi BLEND_* w config.py i z tym, gdzie prepare_photo faktycznie kładzie
zdjęcie. Uruchamiaj po każdej zmianie offsetów – w CSS albo w configu.

    python check_frame_geometry.py [render_pogody.png]
"""

import sys
from pathlib import Path

from PIL import Image

import config
from image_prep import prepare_photo

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RENDER = BASE_DIR / "output" / "pogoda_potem.png"
BG = (0x20, 0x2A, 0x44)          # background-color kontenerów w static/style.css
TOLERANCE = 12                   # kompresja PNG-a bywa stratna przy skalowaniu


def measure_weather(render_path):
    """Zwraca (left, top, right, bottom, szerokość, wysokość) prostokąta tła pogody."""
    image = Image.open(render_path).convert("RGB")
    width, height = image.size
    pixels = image.load()

    def is_bg(c):
        return all(abs(c[i] - BG[i]) < TOLERANCE for i in range(3))

    xs = [x for x in range(width) if any(is_bg(pixels[x, y]) for y in range(height))]
    ys = [y for y in range(height) if any(is_bg(pixels[x, y]) for x in range(width))]
    if not xs or not ys:
        raise SystemExit(f"Nie znalazłem tła {BG} w {render_path} – zły plik?")

    return (min(xs), min(ys), width - 1 - max(xs), height - 1 - max(ys),
            max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def measure_photo():
    """Zwraca to samo dla obszaru, w który prepare_photo wkleja zdjęcie."""
    probe = Image.new("RGB", (2000, 1400), (255, 255, 255))
    probe_path = BASE_DIR / "output" / "_probe_geometry.png"
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    probe.save(probe_path)
    try:
        canvas = prepare_photo(probe_path)
    finally:
        probe_path.unlink(missing_ok=True)

    box = canvas.getbbox()          # obszar niebędący czernią blendy
    width, height = canvas.size
    return (box[0], box[1], width - box[2], height - box[3],
            box[2] - box[0], box[3] - box[1])


def main():
    # Konsola Windows domyślnie stoi na cp1252 i wywala się na polskich znakach.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    render = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RENDER
    if not render.exists():
        raise SystemExit(f"Brak renderu pogody: {render}")

    weather = measure_weather(render)
    photo = measure_photo()
    declared = (config.BLEND_LEFT, config.BLEND_TOP,
                config.BLEND_RIGHT, config.BLEND_BOTTOM,
                config.VISIBLE_SIZE[0], config.VISIBLE_SIZE[1])

    labels = ("lewo", "góra", "prawo", "dół", "szerokość", "wysokość")
    print(f"{'':11s}{'pogoda':>9s}{'config':>9s}{'zdjęcie':>9s}")
    for i, label in enumerate(labels):
        print(f"{label:11s}{weather[i]:>9d}{declared[i]:>9d}{photo[i]:>9d}")

    if weather == declared == photo:
        print("\nOK – zdjęcia trafiają w ten sam prostokąt co pogoda.")
        return 0
    print("\nROZJAZD – popraw BLEND_* w config.py albo marginesy w static/style.css.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
