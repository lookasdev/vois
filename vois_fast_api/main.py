# main.py

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict
import httpx
from datetime import datetime, timedelta
import statistics

app = FastAPI()

# Coordinates for Cluj‑Napoca, Romania
CLUJ_LAT = 46.770439
CLUJ_LON = 23.591423


def get_weather_data(weather_url):
    with httpx.Client() as client:
        res = client.get(weather_url)
        return res.json()

async def reverse_geocode(lat: float, lon: float) -> str:
    """Get location name from latitude/longitude using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "weather-suggestion-app"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        return data.get("display_name", "Unknown location")

def summarize_weather(data):
    hourly = data["hourly"]
    timestamps = hourly["time"]
    temps = hourly["temperature_2m"]
    humidity = hourly["relative_humidity_2m"]
    uv = hourly["uv_index"]

    # Get today's and tomorrow's date in YYYY-MM-DD format
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    def extract_day_stats(day_str):
        day_temps = []
        day_humidity = []
        day_uv = []

        for i, ts in enumerate(timestamps):
            if ts.startswith(day_str):
                day_temps.append(temps[i])
                day_humidity.append(humidity[i])
                day_uv.append(uv[i])

        if not day_temps:
            return None  # Handle empty case safely

        return {
            "min_temp": min(day_temps),
            "max_temp": max(day_temps),
            "avg_humidity": round(statistics.mean(day_humidity), 1),
            "max_uv": max(day_uv)
        }

    today_stats = extract_day_stats(today_str)
    tomorrow_stats = extract_day_stats(tomorrow_str)

    return today_stats, tomorrow_stats

# async def log_weather(response_dict: dict, day: str):  # day can be "today" or "tomorrow"
#     await db.weather_logs.insert_one({
#         "day": day,
#         "timestamp": datetime.utcnow(),
#         "content": response_dict
#         # "content": json.dumps(response_dict, ensure_ascii=False, indent=2)
#     })

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "app is running"}


@app.get("/weather")
def get_cluj_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={CLUJ_LAT}&longitude={CLUJ_LON}"
        "&current_weather=true"
        "&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&timezone=Europe/Bucharest"
    )
    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Open‑Meteo API error")
    data = resp.json()
    current = data.get("current_weather", {})
    hourly = data.get("hourly", {})
    return JSONResponse({
        "city": "Cluj‑Napoca",
        "current": current,
        "hourly": hourly,
    })


@app.get("/weather-suggestion-today")
async def weather_suggestion():
    try:
        lat = CLUJ_LAT
        lon = CLUJ_LON
        location_name = await reverse_geocode(lat, lon)
        # Fetch weather data
        data = get_weather_data(
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,uv_index,precipitation,wind_speed_10m"
        )

        current = data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        uv = current.get("uv_index")
        rain = current.get("precipitation")
        wind = current.get("wind_speed_10m")

        response = {
            "location": location_name,
            "temperature": temp,
            "humidity": humidity,
            "uv_index": uv,
            "precipitation": rain,
            "wind_speed": wind,
        }
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather model error: {str(e)}")


@app.get("/weather-suggestion-tomorrow")
async def weather_suggestion():
    try:
        lat = CLUJ_LAT
        lon = CLUJ_LON
        location_name = await reverse_geocode(lat, lon)

        # Fetch weather data
        weather_data = get_weather_data(
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            "hourly=temperature_2m,relative_humidity_2m,uv_index&"
            "timezone=auto"
        )

        # 2. Summarize data
        today, tomorrow = summarize_weather(weather_data)

        response = {
            "location": location_name,
            "summary": {
                "tomorrow": tomorrow
            },
        }
        # print(" before log")
        # await log_weather(response, day="tomorrow")
        # print("after log")
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))