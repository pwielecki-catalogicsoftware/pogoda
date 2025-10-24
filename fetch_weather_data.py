import requests
import config
import secret

base_url = config.BASE_URL
lat = config.LAT
lon = config.LON
units = config.UNITS
lang = config.LANG
api_key = secret.API_KEY


def fetch_weather_data(endpoint):
    url = f"{base_url}{endpoint}lat={lat}&lon={lon}&units={units}&lang={lang}&appid={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Błąd pobierania danych z endpointu {endpoint}: {e}")
        return None


def get_current_weather():
    return fetch_weather_data("weather?")


def get_hourly_forecast():
    return fetch_weather_data("forecast?")