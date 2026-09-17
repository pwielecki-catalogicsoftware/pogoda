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
- `app.py` – serwis webowy: zdjęcia i harmonogram; `templates/base.html` trzyma
  wspólny układ z zakładkami.
- `display_schedule.py` – presety i decyzja „co teraz pokazać". Nie importuje `inky`
  ani `PIL`, więc logikę przetestujesz na PC.
- `tick.py` – jeden takt harmonogramu (z crona co minutę); `--force` wymusza przerysowanie.
- `install_cron.py` – zakłada wszystkie wpisy crona projektu.
- `walentynkowy.py`, `overwrite_cron.py`, `restore_cron.py` – jednorazowa akcja okolicznościowa:
  podmiana crontaba z backupem do `my_cron_backup.txt` i przywróceniem. Wzorzec do
  ewentualnych kolejnych „trybów specjalnych”.
- `git_autopull.py` – po starcie systemu czeka na sieć (TCP do `github.com:443`, do 3 minut)
  i robi `git pull --ff-only` w katalogu repo. **Gałąź nie jest sprawdzana** – zakładamy, że
  urządzenie stoi na właściwej. Każdy błąd jest tylko logowany, kod wyjścia zawsze 0:
  aktualizacja nie ma prawa zablokować startu stacji. Podpięty przez wpis `@reboot`,
  który zakłada `install_cron.py`; log leci do `/tmp/git_autopull.log`.
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

## Serwis webowy

Flask (`app.py`, port 5000) na dwóch zakładkach: **Zdjęcia** (wgrywanie i kasowanie)
oraz **Harmonogram**. Szablony dziedziczą z `templates/base.html` – style i nawigacja
są tam raz, strony dokładają tylko swoją treść.

**Serwis nigdy nie rysuje po ekranie.** Zapisuje ustawienia albo przestawia stan,
po czym odpala `tick.py --force` przez `subprocess.Popen` i nie czeka na wynik –
render e-papieru trwa kilkadziesiąt sekund, a strona ma odpowiedzieć od razu.
Rysowanie zostaje wyłączną robotą taktu, więc ekran ma jednego właściciela.

Trasy harmonogramu: `GET /harmonogram`, `POST /harmonogram/zapisz` (JSON),
`POST /akcja/nastepny`, `POST /akcja/pogoda` (przewija do najbliższego kroku
z prognozą; 400, gdy sekwencja jej nie zawiera), `GET /stan` dla paska stanu.

Rzeczy, które wyglądają na drobiazgi, a mają powód:

- **Zapis jest automatyczny**, bez przycisku „Zapisz" – na telefonie mniej klikania,
  a cofnięcie zmiany to wybranie innego presetu.
- **Odpowiedź na akcję ściga się z taktem, który sama uruchamia**, więc bywa o krok
  spóźniona. Strona dopytuje `/stan` po dwóch sekundach i wyrównuje pasek.
- **Licznik po zejściu do zera pokazuje „zmiana lada moment"**, nie „za 0 min" –
  takt bywa opóźniony, a zero wiszące na ekranie wygląda jak awaria.
- **Serwer waliduje sekwencję ponownie** (`_popraw_kroki`), bo dane przychodzą
  z przeglądarki. Zapisujemy to, co przeszło walidację, nie to, co przyszło.
- **`secure_filename` przy każdej nazwie pliku** – bez tego nazwa z `../`
  zapisałaby zdjęcie poza katalogiem.

Serwis **nie ma uwierzytelniania** – stoi w domowym LAN-ie i tak ma zostać.
Gdyby kiedykolwiek miał wyjść poza sieć domową, to jest pierwsza rzecz do dołożenia.

## Harmonogram wyświetlania

Model jest jeden – **sekwencja kroków**, przechodzona w kółko. Preset to nazwana sekwencja,
tryb własny to sekwencja edytowalna. Dzięki temu interfejs nie rozdwaja się na dwa tryby.

Podział źródeł jest celowy i **nie wolno go scalać**:

- **presety żyją w `display_schedule.py`** – przyjeżdżają na ramkę z `git pull`;
- **wybór użytkownika żyje w `schedule.json`**, który jest w `.gitignore`. Gdyby był
  śledzony, pierwsza zmiana ustawień w przeglądarce zatrzymałaby `git pull --ff-only`
  i zabiła autopull.

Krok ze zdjęciem może mieć `zmieniaj_co` (minuty): bez niego przez cały krok wisi jedno
zdjęcie, z nim krok rozwija się na kilka krótszych i przy każdym losuje się nowe.
Rozwijaniem zajmuje się `rozwin()` – reszta logiki widzi po prostu dłuższą sekwencję.
Zmienianie zdjęć **podwaja zużycie panelu**, dlatego `odswiezen_na_dobe()` liczy koszt
każdej sekwencji; serwis webowy ma go pokazywać przy wyborze.

Dwie decyzje, które wyglądają na niedoróbki, a są celowe:

- **stan zapisuje się niezależnie od powodzenia renderu** (`tick.py`) – inaczej pusty
  katalog zdjęć zatrzymałby sekwencję na zawsze i ramka nigdy nie doszłaby do prognozy;
- **zmiana ustawień przerywa bieżący krok natychmiast** – `co_teraz()` porównuje podpis
  sekwencji, więc kliknięcie w przeglądarce działa od razu, a nie po pół godzinie.

## Cron na Pi

Aplikacja nie jest demonem, ale cron **nie decyduje już o tym, co jest na ekranie** –
tylko tyka. Wpisy projektu żyją w jednym bloku między markerami i zakłada je
`install_cron.py` (idempotentnie, z backupem do `my_cron_backup.txt`, nie tykając
wpisów spoza projektu):

- `* * * * *` → `tick.py` – jeden takt harmonogramu,
- `@reboot` → `git_autopull.py` (aktualizacja repo po starcie).

Takt sprawdza, czy bieżący krok sekwencji się wyczerpał. Jeśli nie, kończy się po ułamku
sekundy **bez importowania `inky` i `PIL`** – ciężkie moduły ładują się dopiero przy
faktycznym renderze. Blokada plikowa (`output/.tick.lock`) pilnuje, żeby dwa takty nie
pisały naraz po SPI; render pogody bywa dłuższy niż minuta.

Dlaczego takt, a nie demon: proces kończący się po każdym takcie nie ma jak spuchnąć
na 512 MB, a gdy raz padnie, następna minuta go naprawia. Demon, który padłby w nocy,
zostawiłby zamrożoną ramkę do rana. Czasy trwania i tak nie mieszczą się w składni
crontaba – cykl 35 minut nie zapisze się jako `*/35`, bo `*/n` łamie się, gdy `n` nie
dzieli 60.

`buttons.py` **nie jest uruchamiany** – przyciski nie są obsługiwane i użytkownik chce
sterować wszystkim przez serwis webowy. Kod zostaje uśpiony, nie rozwijaj go bez prośby.

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
