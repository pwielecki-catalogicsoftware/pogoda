import webbrowser

import os
from config import output_file_forecast
from fetch_weather_data import get_hourly_forecast
# from main_script import icon_dir
from utils import localize_and_round, format_datetime_pl_genitive
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')


def generate_forecast_html(output_file="/output/pogoda_potem.html"):
    data = get_hourly_forecast()
    if not data:
        print(f"Brak danych pogodowych do prognozy.")
        return

    css_path_abs = os.path.join(STATIC_DIR, "style.css")

    commune_name = data['city']['name']

    def generuj_kolumny_prognoz(n):
        wynik = ""
        max_n = min(n, len(data['list']))

        for i in range(max_n):
            ikona_h = data['list'][i]['weather'][0]['icon']
            # icon_h_dir = os.path.join(STATIC_DIR, ikona_h)
            icon_h_dir = f"../static/ikonyOpenWeather/{ikona_h}.png"
            wynik += f"""
            <div class="kolumna-{i}">
                <p>{datetime.fromtimestamp(data['list'][i]['dt']).strftime("%H:%M")}</p>
                <p><img class="ikona-pogody" src="{icon_h_dir}" alt="ilustracja pogody"></p>
                <p>{localize_and_round(data['list'][i]['main']['temp'],1)}°C</p>
            </div>
            """
        return wynik

    pogoda_potem = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../static/style.css">
    <title>Prognoza na najbliższą dobę</title>
</head>
<body>
    <div id="container-column">
        <div class="top-section">
            <h1>{commune_name}</h1>
            <h3>{format_datetime_pl_genitive(datetime.fromtimestamp(data['list'][0]['dt']))}</h3>
            <h4>{data['list'][0]['weather'][0]['description']}, {localize_and_round(data['list'][0]['main']['temp'],1)}°C</h4>
        </div>
        <div class="middle-section">
            {generuj_kolumny_prognoz(8)}
        </div>
        <div class="bottom-section">
        <p>Sekcja dolna</p>
    </div>
</body>
</html>
"""

    with open(output_file_forecast, 'w', encoding='utf-8') as f:
        f.write(pogoda_potem)
    # webbrowser.open(output_file_forecast)
    # print(data)
    return pogoda_potem