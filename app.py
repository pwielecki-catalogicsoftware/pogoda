from pathlib import Path
import subprocess
import sys

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

import display_schedule as ds

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
PHOTOS_DIR = BASE_DIR / "static" / "images"
THUMBS_DIR = BASE_DIR / "static" / "thumbs"
ALLOWED = {"jpg", "jpeg", "png", "gif", "webp"}


def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


def wywolaj_tick():
    """Odpala takt poza kolejnością, żeby zmiana zadziałała od razu.

    Blokada w tick.py pilnuje, żeby nie wszedł w drogę taktowi z crona. Serwis
    nie czeka na wynik – render e-papieru trwa kilkadziesiąt sekund, a strona
    ma się odświeżyć natychmiast.
    """
    try:
        subprocess.Popen(
            [sys.executable, str(BASE_DIR / "tick.py"), "--force"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError as blad:
        app.logger.warning("nie udało się uruchomić taktu: %s", blad)


# ---------------------------------------------------------------- zdjęcia

@app.route("/")
def index():
    photos = sorted(f.name for f in PHOTOS_DIR.iterdir() if allowed(f.name))
    return render_template("index.html", photos=photos, zakladka="zdjecia")


@app.route("/upload", methods=["POST"])
def upload():
    for file in request.files.getlist("photos"):
        if not file or not allowed(file.filename):
            continue
        # nazwa przychodzi od klienta – bez tego "../" zapisałby plik poza katalogiem
        nazwa = secure_filename(file.filename)
        if not nazwa:
            continue
        sciezka = PHOTOS_DIR / nazwa
        file.save(sciezka)
        miniatura = Image.open(sciezka)
        miniatura.thumbnail((300, 300))
        miniatura.save(THUMBS_DIR / nazwa, optimize=True, quality=75)
    return redirect("/")


@app.route("/thumbs/<filename>")
def thumb(filename):
    return send_from_directory(THUMBS_DIR, secure_filename(filename))


@app.route("/photos/<filename>")
def photo(filename):
    return send_from_directory(PHOTOS_DIR, secure_filename(filename))


@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    nazwa = secure_filename(filename)
    for katalog in (PHOTOS_DIR, THUMBS_DIR):
        plik = katalog / nazwa
        if plik.exists():
            plik.unlink()
    return redirect("/")


# ---------------------------------------------------------------- harmonogram

@app.route("/harmonogram")
def harmonogram():
    ustawienia = ds.wczytaj_ustawienia()
    presety = [
        {"id": klucz, "nazwa": p["nazwa"], "opis": p["opis"], "kroki": p["kroki"],
         "odswiezen": ds.odswiezen_na_dobe(p["kroki"]),
         "rozwiniete": ds.rozwin(p["kroki"])}
        for klucz, p in ds.PRESETY.items()
    ]
    return render_template(
        "harmonogram.html", zakladka="harmonogram", presety=presety,
        ustawienia=ustawienia, min_minuty=ds.MIN_MINUTY,
        wlasny_odswiezen=ds.odswiezen_na_dobe(ustawienia["wlasny"]),
    )


@app.route("/harmonogram/zapisz", methods=["POST"])
def zapisz_harmonogram():
    dane = request.get_json(silent=True) or {}
    ustawienia = ds.wczytaj_ustawienia()

    aktywny = dane.get("aktywny")
    if aktywny in ds.PRESETY or aktywny == "wlasny":
        ustawienia["aktywny"] = aktywny
    if dane.get("wlasny"):
        ustawienia["wlasny"] = dane["wlasny"]

    # zapisujemy to, co przeszło walidację – nie to, co przyszło z przeglądarki
    ustawienia["wlasny"] = ds._popraw_kroki(ustawienia["wlasny"]) or ds.USTAWIENIA_AWARYJNE["wlasny"]
    ds.zapisz_ustawienia(ustawienia)
    wywolaj_tick()
    return jsonify(stan_harmonogramu(ustawienia))


@app.route("/akcja/nastepny", methods=["POST"])
def nastepny():
    """Skraca bieżący krok do zera – najbliższy takt przejdzie dalej."""
    ds.wymus_nastepny()
    wywolaj_tick()
    return jsonify(stan_harmonogramu())


@app.route("/akcja/pogoda", methods=["POST"])
def pokaz_pogode():
    """Przewija sekwencję do najbliższego kroku z prognozą.

    Nie wstawia kroku spoza sekwencji – po prostu zaczyna od niego, więc po
    upływie jego czasu ramka wraca do normalnego rytmu bez żadnej pamięci
    o tym, że ktoś ją popchnął.
    """
    indeks = ds.indeks_typu("prognoza")
    if indeks is None:
        return jsonify({"blad": "Bieżący harmonogram nie zawiera prognozy."}), 400
    ds.ustaw_krok(indeks)
    wywolaj_tick()
    return jsonify(stan_harmonogramu())


@app.route("/stan")
def stan():
    return jsonify(stan_harmonogramu())


def stan_harmonogramu(ustawienia=None):
    """Co jest na ekranie i ile zostało do zmiany – dla paska stanu."""
    ustawienia = ustawienia or ds.wczytaj_ustawienia()
    sekwencja = ds.rozwin(ds.aktywna_sekwencja(ustawienia))
    krok, indeks, _, _ = ds.co_teraz(ustawienia=ustawienia)
    biezacy = sekwencja[indeks % len(sekwencja)]
    return {
        "typ": biezacy["typ"],
        "indeks": indeks % len(sekwencja),
        "ile_krokow": len(sekwencja),
        "sekund_do_zmiany": ds.sekund_do_zmiany(ustawienia),
        "odswiezen": ds.odswiezen_na_dobe(ds.aktywna_sekwencja(ustawienia)),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
