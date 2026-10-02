import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class GeocodingError(Exception):
    """Raised when a location cannot be resolved."""


def resolve_location(city: str) -> dict:
    """
    Resolve a city name into latitude and longitude
    using the Open-Meteo Geocoding API.
    """

    if not city or not city.strip():
        raise GeocodingError("City name cannot be empty.")

    params = {
        "name": city.strip(),
        "count": 5,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        raise GeocodingError(
            "Unable to connect to the geocoding service."
        ) from error

    except ValueError as error:
        raise GeocodingError(
            "Invalid response from geocoding service."
        ) from error

    results = data.get("results", [])

    if not results:
        raise GeocodingError(
            f"Could not find the location: {city}"
        )

    # Use the first result as the default candidate.
    location = results[0]

    return {
        "name": location.get("name"),
        "country": location.get("country"),
        "admin1": location.get("admin1"),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location.get("timezone")
    }