import webbrowser
import locale
import os
from datetime import datetime

import requests

locale.setlocale(locale.LC_ALL, "pl-PL.UTF-8")

# funkcja, która zaokrągla do zadanego miejsca po przecinku (jak round) i używa separatora zgodnie z zadaną lokalizacją
def localize_and_round(float, ndigits=1):
    return locale.format_string(f"%.{ndigits}f",float)

base_url = "https://api.openweathermap.org/data/2.5/"

# Współrzędne dla Komputerowej 8 w Warszawie
lat = "52.2091"
lon = "20.9835"
units = "metric"
lang = "pl"

api_key = "53ace621445aefdff0340581bab2648e"
# api_key = "fc0b9a8e7f1bbeb5a78567b416501dc5"

def get_current_weather(lat, lon, units, lang, api_key):
    url = f"{base_url}weather?lat={lat}&lon={lon}&units={units}&lang={lang}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        return weather_data
        # print(weather_data)
    else:
        print(f"Nie udało się pobrać aktualnej pogody {response.status_code}")

def get_hourly_forecast(lat, lon, units, lang, api_key):
    url = f"{base_url}forecast?lat={lat}&lon={lon}&units={units}&lang={lang}&appid={api_key}"
    # url = f"https://api.openweathermap.org/data/2.5/forecast?lat=44.34&lon=10.99&appid={api_key}" # URL do testów
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        hourly_forecast_data = response.json()
        return hourly_forecast_data
        # print(weather_data)
    else:
        print(f"Nie udało się pobrać prognozy godzinowej {response.status_code}")



current_weather = get_current_weather(lat, lon, units, lang, api_key)
hourly_forecast = get_hourly_forecast(lat, lon, units, lang, api_key)


# używane elementy:
pogoda_opisowo = current_weather['weather'][0]['description']
ikona = current_weather['weather'][0]['icon']
miejscowość = hourly_forecast['city']['name']
temperatura_rzeczywista = current_weather['main']['temp']
temperatura_odczuwalna = current_weather['main']['feels_like']
ciśnienie = current_weather['main']['pressure']
wilgotność = current_weather['main']['humidity']
prędkość_wiatru = current_weather['wind']['speed']
kierunek_wiatru = current_weather['wind']['deg']
wschód_słońca = datetime.fromtimestamp(current_weather['sys']['sunrise']).strftime("%H:%M")
zachód_słońca = datetime.fromtimestamp(current_weather['sys']['sunset']).strftime("%H:%M")

# elementy używane w prognozie trzygodzinnej


def data_godzina(slot):
    return hourly_forecast['list'][slot]['dt_txt']

def generuj_kolumny_prognoz(n):
    wynik = ""
    max_n = min(n, len(hourly_forecast['list']))

    for i in range(max_n):
        ikona_h = hourly_forecast['list'][i]['weather'][0]['icon']
        icon_h_dir = f"../static/ikonyOpenWeather/{ikona_h}.png"
        wynik += f"""
        <div class="kolumna-{i}">
            <p>{datetime.fromtimestamp(hourly_forecast['list'][i]['dt']).strftime("%H:%M")}</p>
            <p>{hourly_forecast['list'][i]['weather'][0]['description']}</p>
            <p><img class="ikona-pogody" src="{icon_h_dir}" alt="ilustracja pogody"></p>
            <p>{localize_and_round(hourly_forecast['list'][i]['main']['temp'],1)}°C</p>
            <p>{localize_and_round(hourly_forecast['list'][i]['main']['feels_like'],1)}°C</p>
        </div>
        """
    return wynik

# if current_weather:
#     print(current_weather)
if hourly_forecast:
    print(hourly_forecast)

icon_dir = f"../static/ikonyOpenWeather4x/{ikona}.png"
# icon_dir = f"src/icons/{ikona}.svg"
# if os.path.exists(icon_dir):
#     print(f"Znaleziono {icon_dir}")
# else:
#     print(f"could not find {icon_dir}")

pogoda_teraz = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../static/style.css">
    <title>Aktualna pogoda</title>
</head>
<body>
    <div id="container-row">
        <div class="kolumna-lewa">
            <h1>{miejscowość}</h1>
            <p>{pogoda_opisowo.capitalize()}</p>
            <p>Temperatura: {localize_and_round(temperatura_rzeczywista,1)}°C</p>
            <p>(odczuwalna: {localize_and_round(temperatura_odczuwalna,1)}°C)</p>
            <p>{ciśnienie} hPa</p>
            <hr>
            <p>Wschód słońca o {wschód_słońca}</p>
            <p>Zachód słońca o {zachód_słońca}</p>
        </div>
        <div class="kolumna-prawa">
            <img class="ikona-pogody" src="{icon_dir}" alt="ilustracja pogody">
        </div>
    </div>
</body>
</html>
"""

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
            <h1>{miejscowość}, {datetime.fromtimestamp(hourly_forecast['list'][0]['dt']).strftime("%#d %B")}</h1>
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

webbrowser.register(
    "firefox",
    None,
    webbrowser.BackgroundBrowser("C:\\Program Files\\Mozilla Firefox\\firefox.exe")
)

# with open('/output/pogoda_teraz.html', 'w', encoding='utf-8') as f:
#     f.write(pogoda_teraz)
# webbrowser.open('output/pogoda_teraz.html')

with open('output/pogoda_potem.html', 'w', encoding='utf-8') as f:
    f.write(pogoda_potem)
webbrowser.get("firefox").open('output/pogoda_potem.html')
