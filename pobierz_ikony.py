import os
import requests

# Lista kodów ikon z OpenWeather
ikony = [
    "01d", "01n", "02d", "02n", "03d", "03n",
    "04d", "04n", "09d", "09n", "10d", "10n",
    "11d", "11n", "13d", "13n", "50d", "50n"
]

# Folder docelowy
folder = "ikonyOpenWeather4x"
os.makedirs(folder, exist_ok=True)

# URL bazowy
base_url = "https://openweathermap.org/img/wn/"

# Pobieranie ikon
for kod in ikony:
    url = f"{base_url}{kod}@4x.png"
    lokalna_nazwa = os.path.join(folder, f"{kod}.png")

    if not os.path.exists(lokalna_nazwa):  # Nie pobieraj ponownie
        print(f"Pobieram {kod}...")
        r = requests.get(url)
        if r.status_code == 200:
            with open(lokalna_nazwa, "wb") as f:
                f.write(r.content)
        else:
            print(f"❌ Błąd przy pobieraniu {kod}: {r.status_code}")
    else:
        print(f"{kod} już istnieje, pomijam.")
