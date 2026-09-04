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
- `image_prep.py` – kadrowanie zdjęcia w okno blendy i obróbka pod e-papier. Nie importuje
  `inky`, więc podgląd zrobisz na PC: `python image_prep.py <zdjecie>`.
- `check_frame_geometry.py` – kontrola, czy zdjęcia trafiają w ten sam prostokąt co pogoda.
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

## Geometria ramki (blenda)

Ekran jest przyklejony do płytki niesymetrycznie, więc passe-partout ramki zasłania
nierówno. Offsety **zostały dobrane doświadczalnie na sprzęcie** i użytkownik uznaje
układ pogody za wzorcowy – to on jest źródłem prawdy, nie wyliczenia z CSS-a.

| | lewo | góra | prawo | dół |
|---|---|---|---|---|
| offset | 55 px | 33 px | 48 px | 0 px |

Widoczne okno: **697 × 447 px** (panel 800 × 480). Zmierzone na `output/pogoda_potem.png`.

Te same wartości żyją w **dwóch miejscach, które o sobie nie wiedzą**:

- `static/style.css` – procentowo, `margin: 4.1% 6% 0% 6.875%` (ekrany pogody),
- `config.py` – w pikselach, `BLEND_*` (ścieżka zdjęć).

Po zmianie któregokolwiek uruchom `check_frame_geometry.py` – porównuje render pogody,
stałe z configu i realny wynik `prepare_photo()`, i zwraca 1 przy rozjeździe.

**Nie „poprawiaj” CSS-a pogody.** `height: calc(100% - 4.1% - 0%)` liczy procenty od
wysokości, a `margin-top: 4.1%` od szerokości (tak działa CSS), więc kontener wychodzi
na 493 px przy ekranie 480 px. Wygląda to na błąd, ale `overflow: hidden` ucina nadmiar
dokładnie na dolnej krawędzi, a dolny offset i tak ma być zerowy – efekt jest pikselowo
poprawny. „Naprawienie” tego odsunęłoby tło 13 px od dołu i zepsuło działający układ.

Zdjęcia idą przez `image_prep.prepare_photo()`: kadr **„cover”** w okno blendy (bez
czarnych pasów – użytkownik woli stracić skraj kadru niż oglądać letterbox), `draft()`
przy dekodowaniu JPEG-a (6000×4000 to 72 MB bitmapy, a Pi Zero 2 W ma 512 MB RAM),
`exif_transpose()`, LANCZOS, unsharp i kontrast. Parametry obróbki siedzą w `config.py`
i **czekają na dobranie przy ramce** – na monitorze nie ocenisz, jak wypadają na palecie
e-papieru. Ekrany pogody **nie** przechodzą przez ten moduł.

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
  Uwaga: wersja z `..._from_html.py` celowo **nie** kadruje przez `prepare_photo()`,
  bo HTML ma blendę wbudowaną w CSS – scalając je, zachowaj tę różnicę.
- `html_to_image.py` (html2image) i `server.py` (livereload) to pozostałości z prototypowania
  na PC; nie są w potoku. `generate_*_html.py` mają `STATIC_DIR` z `..` – ślad po innym układzie
  katalogów.
- `buttons.py` łapie przycisk `C` w `LABELS`, ale nie robi z nim nic – wolny slot.
