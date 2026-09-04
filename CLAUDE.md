# PogodaOdZera – Agent Guide

Hobbystyczny projekt: **stacja pogodowa / ramka na e-papierze** na Raspberry Pi Zero 2 W.
Trzeci projekt z rodziny obok `ebookPossibly` (Inkplate6, e-ink czytnik) i `watchPossibly`
(ESP32-S3, smartwatch). Docelowo wszystkie trzy mają się ze sobą komunikować – ale zawsze
jeden krok naraz, nie budujemy integracji „na zapas”.

## Rozmowa i konwencje

- **Odpowiedzi po polsku.** Kod i nazwy plików po angielsku/polsku – tak jak już są
  (mieszanka jest zastana, nie normalizuj jej hurtem). **Komentarze i printy są po polsku** –
  nowy kod pisz tak samo.
- **Commit lokalnie, nigdy `git push`.** Użytkownik pushuje sam. Commit dopiero po jego
  przeglądzie zmian – po edycji zatrzymaj się i pokaż, co zmieniłeś (plik, przed/po, powód).
- Gałąź robocza: `development` (domyślna zdalna to `master`). Nie przełączaj gałęzi sam.
- To projekt hobbystyczny – małe, czytelne kroki, bez nadmiernej inżynierii. Ale nie zostawiaj
  kodu, który wywala urządzenie: na Pi wszystko startuje z crona, bez konsoli.

## Sprzęt

- **Raspberry Pi Zero 2 W**, Raspberry Pi OS.
- **Pimoroni Inky Impression** (7-kolorowy e-paper, 800×480) – biblioteka `inky.auto.auto()`.
  Rozdzielczość czytana z `inky.resolution`, nie zakładaj jej na sztywno poza domyślnym 800×480.
- **4 przyciski** Inky na GPIO: `A=5` (poprzedni ekran), `B=6` (następny), `C=16` (wolny),
  `D=24` (długie 2 s = `sudo reboot`). Obsługa przez `gpiod` (edge detection, pull-up).
- Temperatura CPU przez `vcgencmd` (`utils.get_cpu_temp`).

## Środowisko na urządzeniu

| Co | Ścieżka na Pi |
|---|---|
| Repozytorium | `/home/piter/repo/pogoda` |
| Interpreter | `/home/piter/.virtualenvs/pimoroni/bin/python` |
| Zdjęcia (galeria) | `static/images`, miniatury `static/thumbs` |

Na Windowsie (ta maszyna) uruchomi się tylko część kodu – `inky`, `gpiod`, `vcgencmd`
i `wkhtmltoimage` są dostępne wyłącznie na Pi. **Nie da się tu przetestować renderu na ekran**;
weryfikacja końcowa zawsze należy do użytkownika, który wgrywa i uruchamia na Pi
(dokładnie jak w `ebookPossibly` / `watchPossibly`: dopóki nie zobaczył logu, nic nie jest
potwierdzone). Zakładaj Linuxa w kodzie urządzenia – `utils.py` ma już przełącznik formatu daty.

## Potok danych

```
fetch_weather_data.py   → OpenWeatherMap (weather? / forecast?), klucz z secret.py
generate_forecast_html.py / generate_current_html.py
                        → output/pogoda_potem.html | pogoda_teraz.html  (+ static/style.css, ikony)
epaper_image_from_html.py
      html_to_png_wkhtmltoimage()  → output/*.png   (wkhtmltoimage, --enable-local-file-access)
      display_on_epaper()          → Inky (resize do inky.resolution, saturation 0.5)
main.py                 → jednorazowy render prognozy
buttons.py              → pętla główna na urządzeniu: przyciski + auto-przełączanie co 15 min
```

- `config.py` – jedyne źródło ścieżek wyjściowych i współrzędnych (Warszawa, Komputerowa 8),
  `BASE_DIR` liczone z położenia pliku, więc cron działa niezależnie od CWD. **Nowe stałe
  dodawaj tutaj**, nie rozsiewaj literałów po modułach.
- `secret.py` – `API_KEY` do OpenWeatherMap, **w `.gitignore`**. Nigdy nie wpisuj klucza
  do plików śledzonych i nie pokazuj go w odpowiedziach.
- `output/` jest w `.gitignore` – artefakty nie idą do repo.

## Dodatkowe elementy

- `app.py` – **Flask, port 5000, `0.0.0.0`**: galeria zdjęć do wyświetlania na ramce.
  Upload wielu plików, miniatury 300×300 (Pillow), usuwanie z potwierdzeniem.
  Ścieżki `PHOTOS_DIR` / `THUMBS_DIR` są **zahardkodowane pod Pi** – jeśli je ruszasz,
  przenieś do `config.py`.
- `epaper_image_from_image.py` – losowy obraz z `static/images` na ekran (tryb ramki, z crona).
  Brak katalogu/plików → `None` i cisza, żeby cron nie nadpisał wygenerowanej pogody.
- `walentynkowy.py`, `overwrite_cron.py`, `restore_cron.py` – jednorazowa akcja okolicznościowa:
  podmiana crontaba z backupem do `my_cron_backup.txt` i przywróceniem. Wzorzec do
  ewentualnych kolejnych „trybów specjalnych”.
- `git_autopull.py` – po starcie systemu czeka na sieć (TCP do `github.com:443`, do 3 minut)
  i robi `git pull --ff-only` w katalogu repo. **Gałąź nie jest sprawdzana** – zakładamy, że
  urządzenie stoi na właściwej. Każdy błąd jest tylko logowany, kod wyjścia zawsze 0:
  aktualizacja nie ma prawa zablokować startu stacji. Podpięty przez wpis `@reboot` w cronie,
  który zakłada `install_autopull_cron.py` (idempotentnie, z backupem crontaba do
  `my_cron_backup.txt`); log leci do `/tmp/git_autopull.log`.
- `utils.kill_previous_instances` – `pgrep -f <nazwa skryptu>` + SIGTERM, żeby cron nie
  mnożył instancji.

## Cron na Pi

Aplikacja nie jest demonem – wszystko chodzi z crona:

- render pogody **co 10 minut**,
- losowe zdjęcie z `static/images` **co 10 minut, z przesunięciem o 2 minuty**,
- `@reboot` → `git_autopull.py` (aktualizacja repo po starcie),
- `buttons.py` (pętla przycisków) uruchamiany osobno, gdy jest potrzebny.

Skrypty muszą więc same dbać o kontekst: ścieżki z `config.py`/`BASE_DIR` (nigdy względne
do CWD), pełna ścieżka do interpretera z venva, `kill_previous_instances` przeciw
nakładaniu się instancji, brak interaktywnych promptów.

## Dług techniczny (znany, nie „naprawiaj” bez pytania)

- `main_script.py` – **martwy, sprzed refaktoru** na moduły. Ma **zahardkodowany klucz API
  wgrany do historii gita** (klucz spalony, wymieniony 2026-09-04; nowy siedzi w `secret.py`).
  Użytkownik **świadomie zostawia plik jako pamiątkę** – nie rozwijaj go i nie proponuj
  usunięcia z własnej inicjatywy; skasować dopiero, gdy sam o to poprosi.
- `display_on_epaper()` jest skopiowane w trzech plikach (`epaper_image_from_html.py`,
  `epaper_image_from_image.py`, `walentynkowy.py`) – naturalny kandydat na jeden moduł.
- `html_to_image.py` (html2image) i `server.py` (livereload) to pozostałości z prototypowania
  na PC; nie są w potoku. `generate_*_html.py` mają `STATIC_DIR` z `..` – ślad po innym układzie
  katalogów.
- `buttons.py` łapie przycisk `C` w `LABELS`, ale nie robi z nim nic – wolny slot.
