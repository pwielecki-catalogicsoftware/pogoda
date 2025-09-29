import webbrowser

from config import output_file_current
from fetch_weather_data import get_current_weather
# from main_script import icon_dir
from utils import localize_and_round, format_datetime_pl_genitive
from datetime import datetime


def generate_current_html(output_file="/output/pogoda_teraz.html"):
    data = get_current_weather()
    if not data:
        print(f"Brak danych pogodowych dla pogody bieżącej.")
        return

    weather_description = data['weather'][0]['description']
    icon = data['weather'][0]['icon']
    commune_name = data['name']
    actual_temperature = data['main']['temp']
    feels_like = data['main']['feels_like']
    pressure = data['main']['pressure']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    wind_direction = data['wind']['deg']
    sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
    sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
    icon_dir = f"../static/ikonyOpenWeather4x/{icon}.png"
    clouds = data['clouds']['all']

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
            <h1>{commune_name}</h1>
            <h2>{format_datetime_pl_genitive(datetime.fromtimestamp(data['dt']))}</h2>
            <p>{weather_description.capitalize()}</p>
            <p>Zachmurzenie: {clouds}</p>
            <p>Temperatura: {localize_and_round(actual_temperature,1)}°C</p>
            <p>(odczuwalna: {localize_and_round(feels_like,1)}°C)</p>
            <p>{pressure} hPa</p>
            <hr>
            <p>Wschód słońca o {sunrise}</p>
            <p>Zachód słońca o {sunset}</p>
        </div>
        <div class="kolumna-prawa">
            <img class="ikona-pogody" src="{icon_dir}" alt="ilustracja pogody">
        </div>
    </div>
</body>
</html>
"""

    with open(output_file_current, 'w', encoding='utf-8') as f:
        f.write(pogoda_teraz)
    webbrowser.open(output_file_current)
    print(data)
    return pogoda_teraz