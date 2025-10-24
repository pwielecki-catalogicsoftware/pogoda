#!/usr/bin/env python3

import time
import subprocess
from pathlib import Path
from PIL import Image
from inky.auto import auto

import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge

# =========================
# PARAMETRY KONFIGURACYJNE
# =========================
LONG_PRESS_DURATION = 2.0      # sekundy wymagane do rebootu (D)
DEBOUNCE_TIME = 0.1            # opóźnienie po renderze (sekundy)
ASK_USER_INKY = False           # True, jeśli chcesz wybierać model ekranu ręcznie przy starcie
SATURATION = 0.5                # nasycenie kolorów dla Inky

# GPIO dla przycisków
SW_A = 5   # poprzedni obraz
SW_B = 6   # następny obraz
SW_C = 16
SW_D = 24  # długie przytrzymanie = reboot

BUTTONS = [SW_A, SW_B, SW_C, SW_D]
LABELS = ["A", "B", "C", "D"]

# =========================
# INICJALIZACJA EKRANU
# =========================
inky = auto(ask_user=ASK_USER_INKY, verbose=False)
inky.set_border(inky.BLACK)

# =========================
# LISTA OBRAZÓW
# =========================
from config import (
    output_file_current,
    output_file_forecast,
    output_png_current,
    output_png_forecast,
)

images = [
    (output_file_current, output_png_current),
    (output_file_forecast, output_png_forecast),
]
current_index = 0

# =========================
# FLAGI KONTROLNE
# =========================
rendering_in_progress = False
D_press_start = None

# =========================
# FUNKCJE POMOCNICZE
# =========================
def show_image(index):
    """Renderuje HTML do PNG i wyświetla na ekranie"""
    global rendering_in_progress
    rendering_in_progress = True
    html_path, png_path = images[index]

    from epaper_image_from_html import render_html_to_epaper
    render_html_to_epaper(html_path, png_path, width=inky.resolution[0], height=inky.resolution[1])

    rendering_in_progress = False
    time.sleep(DEBOUNCE_TIME)
    print(f"Displayed image {index}: {png_path}")

# Pokaż pierwszy obraz przy starcie
show_image(current_index)

# =========================
# KONFIGURACJA PRZYCISKÓW
# =========================
INPUT = gpiod.LineSettings(direction=Direction.INPUT,
                           bias=Bias.PULL_UP,
                           edge_detection=Edge.FALLING)

chip = gpiodevice.find_chip_by_platform()
OFFSETS = [chip.line_offset_from_id(id) for id in BUTTONS]
line_config = dict.fromkeys(OFFSETS, INPUT)
request = chip.request_lines(consumer="pogoda-buttons", config=line_config)

# =========================
# OBSŁUGA PRZYCISKÓW
# =========================
def handle_button(event):
    """Wywoływana przy wciśnięciu dowolnego przycisku"""
    global current_index, D_press_start, rendering_in_progress

    if rendering_in_progress:
        return

    index = OFFSETS.index(event.line_offset)
    label = LABELS[index]
    print(f"Button press detected: {label}")

    # ---------
    # A / B – przewijanie ekranów
    # ---------
    if label == "A":
        current_index = (current_index - 1) % len(images)
        show_image(current_index)
    elif label == "B":
        current_index = (current_index + 1) % len(images)
        show_image(current_index)

    # ---------
    # D – długie przytrzymanie = reboot
    # ---------
    elif label == "D":
        if D_press_start is None:
            D_press_start = time.time()

# =========================
# PĘTLA GŁÓWNA
# =========================
while True:
    for event in request.read_edge_events():
        handle_button(event)

    # Sprawdzenie długości wciśnięcia D
    if D_press_start is not None:
        d_offset = OFFSETS[LABELS.index("D")]
        d_state = request.get_values()[d_offset]  # 0 = wciśnięty, 1 = puszczony
        if d_state == 1:
            D_press_start = None
        elif time.time() - D_press_start >= LONG_PRESS_DURATION:
            print("D long press detected. Rebooting Raspberry Pi...")
            subprocess.run(["sudo", "reboot"])
            D_press_start = None

    time.sleep(0.1)
