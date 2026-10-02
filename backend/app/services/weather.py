import requests


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAPIError(Exception):
    """Raised when live weather data cannot be retrieved."""


def fetch_weather(latitude: float, longitude: float) -> dict:
    """
    Fetch actual current and hourly weather data
    from Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_gusts_10m",
            "wind_direction_10m",
            "uv_index"
        ]),

        "hourly": ",".join([
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "wind_speed_10m",
            "wind_gusts_10m",
            "uv_index",
            "weather_code"
        ]),

        "forecast_days": 2,
        "timezone": "auto"
    }

    try:
        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        raise WeatherAPIError(
            "Unable to retrieve live weather data."
        ) from error

    except ValueError as error:
        raise WeatherAPIError(
            "Invalid response from weather service."
        ) from error

    if not isinstance(data, dict) or "current" not in data:
        raise WeatherAPIError(
            "Weather service returned incomplete data."
        )

    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "current": data["current"],
        "hourly": data.get("hourly", {}),
        "units": {
            "current": data.get("current_units", {}),
            "hourly": data.get("hourly_units", {})
        }
    }