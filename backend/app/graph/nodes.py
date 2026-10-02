import re
from langchain_mistralai import ChatMistralAI

from datetime import datetime, timedelta
from app.graph.state import WeatherBotState
from app.services.geocoding import resolve_location, GeocodingError
from app.services.weather import fetch_weather, WeatherAPIError
from app.policies.sop_matcher import (
    match_sops,
    extract_activity_tags
)
def understand_query(state: WeatherBotState) -> dict:
    question = state.get("question", "").strip()

    if not question:
        return {
            "error": "Please enter a weather-related question.",
            "error_type": "invalid_query"
        }

    previous_location = state.get("location")
    previous_tags = state.get("previous_activity_tags", [])

    # Extract location
        # Extract the city from phrases such as:
    # "cycling tomorrow in Bhopal"
    # "cycling in Bhopal tomorrow"
    # "running at noon in Indore"

    location_matches = re.findall(
        r"\b(?:in|at|near)\s+([A-Za-z][A-Za-z\s]*?)(?=\s+(?:in|at|near|today|tomorrow|this|tonight|now|morning|afternoon|evening|noon|be|is|are|was|were|would|should|could|can|will|suitable|safe|okay|good|fine|for|with|because)\b|[?.!,]|$)",
        question,
        re.IGNORECASE
    )

    # Use the last location phrase, so "at noon in Indore"
    # resolves to "Indore", not "noon in Indore".
    location_candidates = [
        candidate.strip()
        for candidate in location_matches
        if candidate.strip().lower() not in {
            "noon", "morning", "afternoon", "evening",
            "today", "tomorrow", "tonight", "now", "the"
        }
    ]

    location = (
        location_candidates[-1]
        if location_candidates
        else previous_location
    )

    text = question.lower()

    # Identify requested date
    if "tomorrow" in text:
        requested_date = "tomorrow"
    elif "today" in text or "now" in text:
        requested_date = "today"
    else:
        requested_date = state.get("requested_date", "today")

    # Identify requested time period
    if "morning" in text:
        requested_period = "morning"
    elif "noon" in text:
        requested_period = "noon"
    elif "afternoon" in text:
        requested_period = "afternoon"
    elif "evening" in text or "tonight" in text:
        requested_period = "evening"
    elif "today" in text or "tomorrow" in text or "now" in text:
        requested_period = "all_day"
    else:
        requested_period = state.get("requested_period", "all_day")

    requested_time = (
        "tomorrow" if requested_date == "tomorrow"
        else requested_period
    )

    # First identify activities explicitly mentioned in this message.
    current_tags = extract_activity_tags(question)

    # Carry previous activity only for a time-only follow-up.
    # Example: "What about this evening?"
    time_followup_pattern = (
        r"^(?:(?:and\s+)?(?:what|how)\s+about\s+)?"
        r"(?:this\s+)?(?:today|tomorrow|tonight|now|"
        r"morning|noon|afternoon|evening|later)"
        r"(?:\s+(?:instead|then))?[?.!]*$"
    )

    is_time_followup = bool(
        re.match(time_followup_pattern, text.strip(), re.IGNORECASE)
    )

    if current_tags:
        activity_tags = current_tags
    elif is_time_followup:
        activity_tags = previous_tags
    else:
        # A new unrelated topic must not inherit the previous activity.
        activity_tags = []

    return {
        "location": location,
        "requested_time": requested_time,
        "requested_date": requested_date,
        "requested_period": requested_period,
        "activity_tags": activity_tags,
        "previous_activity_tags": activity_tags
    }

def resolve_location_node(state: WeatherBotState) -> dict:

    location = state.get("location")

    if not location:
        return {
            "error": "Please specify a city so I can check its weather.",
            "error_type": "location_missing",
            "weather_available": False
        }

    try:
        coordinates = resolve_location(location)

        return {
            "coordinates": coordinates,
            "weather_available": True,
            "error": None,
            "error_type": None
        }

    except GeocodingError as error:
        return {
            "error": str(error),
            "error_type": "geocoding_failure",
            "weather_available": False
        }


def fetch_weather_node(state: WeatherBotState) -> dict:

    coordinates = state.get("coordinates")

    if not coordinates:
        return {
            "error": "Location coordinates are unavailable.",
            "error_type": "location_failure",
            "weather_available": False
        }

    try:
        weather = fetch_weather(
            coordinates["latitude"],
            coordinates["longitude"]
        )

        return {
            "weather": weather,
            "weather_available": True,
            "error": None,
            "error_type": None
        }

    except WeatherAPIError as error:
        return {
            "error": str(error),
            "error_type": "weather_api_failure",
            "weather_available": False
        }

def select_forecast_node(state: WeatherBotState) -> dict:
    weather = state.get("weather", {})
    hourly = weather.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return {
            "error": "Hourly forecast data is unavailable.",
            "error_type": "forecast_unavailable",
            "weather_available": False,
        }

    current_time = weather.get("current", {}).get("time")

    try:
        reference = datetime.fromisoformat(current_time)
    except (TypeError, ValueError):
        return {
            "error": "The forecast's local reference time is unavailable.",
            "error_type": "forecast_time_unavailable",
            "weather_available": False,
        }

    requested_date = state.get("requested_date", "today")
    requested_period = state.get("requested_period", "all_day")

    # Choose the requested date
    if requested_date == "tomorrow":
        target_date = (reference + timedelta(days=1)).date()
    else:
        target_date = reference.date()

    # Choose the requested hours
    period_hours = {
        "morning": (6, 11),
        "noon": (12, 12),
        "afternoon": (12, 17),
        "evening": (18, 22),
        "all_day": (0, 23),
    }

    start_hour, end_hour = period_hours.get(
        requested_period,
        (0, 23)
    )

    # For today, don't include hours that have already passed
    if target_date == reference.date() and requested_period == "all_day":
        start_hour = reference.hour

    selected_indices = []

    for index, time_value in enumerate(times):
        try:
            forecast_time = datetime.fromisoformat(time_value)
        except (TypeError, ValueError):
            continue

        if (
            forecast_time.date() == target_date
            and start_hour <= forecast_time.hour <= end_hour
        ):
            selected_indices.append(index)

    if not selected_indices:
        return {
            "error": (
                f"No hourly forecast is available for "
                f"{requested_date} {requested_period}. "
                "Please try another time period."
            ),
            "error_type": "forecast_period_unavailable",
            "weather_available": False,
        }

    # Aggregate values across the selected period.
    # Maximum values allow threshold-based SOPs to detect
    # whether a risk occurs during any selected hour.
    selected_hourly = {}

    for field, values in hourly.items():
        if field == "time" or not isinstance(values, list):
            continue

        period_values = [
            values[index]
            for index in selected_indices
            if index < len(values)
            and isinstance(values[index], (int, float))
        ]

        if period_values:
            selected_hourly[field] = max(period_values)

    selected_hourly["period_start"] = times[selected_indices[0]]
    selected_hourly["period_end"] = times[selected_indices[-1]]

    updated_weather = dict(weather)
    updated_weather["selected_hourly"] = selected_hourly

    return {
        "weather": updated_weather,
        "weather_available": True,
        "error": None,
        "error_type": None,
    }

def match_sops_node(state: WeatherBotState) -> dict:
    weather = state.get("weather", {})
    
    question = state.get("question", "")
    
    # Use the tags already resolved by understand_query().
    # This preserves time-only follow-ups but avoids stale activity tags.
    activity_tags = state.get("activity_tags", [])

    result = match_sops(
        query=question,
        weather=weather,
        previous_tags=activity_tags
    )

    return {
        "activity_tags": result["activity_tags"],
        "matched_sops": result["matched_sops"],
        "selected_sop": result["selected_sop"],
        "match_found": result["match_found"],
        "resolution_strategy": result["resolution_strategy"]
    }

def generate_answer_node(state: WeatherBotState) -> dict:
    sop = state.get("selected_sop")
    weather = state.get("weather", {})
    coordinates = state.get("coordinates", {})

    selected = weather.get("selected_hourly", {})
    units = weather.get("units", {}).get("hourly", {})

    location = coordinates.get("name", "your location")

    requested_date = state.get("requested_date", "today")
    requested_period = state.get("requested_period", "all_day")

    period_label = {
        "morning": "morning",
        "noon": "noon",
        "afternoon": "afternoon",
        "evening": "evening",
        "all_day": "day",
    }.get(requested_period, requested_period)

    weather_details = []

    values = [
        ("Temperature", selected.get("temperature_2m"), "temperature_2m"),
        ("Feels-like temperature", selected.get("apparent_temperature"), "apparent_temperature"),
        ("Wind speed", selected.get("wind_speed_10m"), "wind_speed_10m"),
        ("Wind gusts", selected.get("wind_gusts_10m"), "wind_gusts_10m"),
        ("Precipitation probability", selected.get("precipitation_probability"), "precipitation_probability"),
        ("UV index", selected.get("uv_index"), "uv_index"),
    ]

    for label, value, field in values:
        if value is not None:
            unit = units.get(field, "")
            weather_details.append(f"{label}: {value} {unit}".strip())

    weather_summary = "\n".join(weather_details) or "No detailed weather values are available."

    # Convert SOP instruction-style text into user-facing advice.
    raw_advice = sop.get("advice", "").strip()
    advice = raw_advice

    replacements = {
        "Advise against cycling under the observed wind conditions. Explain that strong winds can affect balance and vehicle control. Suggest postponing the ride or choosing an alternative mode of transport.":
        "I advise against cycling under these wind conditions. Strong winds can affect your balance and control of the vehicle. Consider postponing the ride or choosing another way to travel.",
    }

    advice = replacements.get(raw_advice, advice)

    answer = (
        f"Weather advisory for {location}\n"
        f"Requested period: {requested_date}, {period_label}\n\n"
        f"Weather forecast:\n"
        f"{weather_summary}\n\n"
        f"Advisory:\n{advice}\n\n"
        f"Why this advisory applies: {sop.get('reason', 'The selected SOP condition was met.')}\n"
        f"Policy reference: {sop.get('id', 'N/A')} - {sop.get('title', 'Weather advisory')}\n"
        f"Severity: {sop.get('severity', 'N/A')}"
    )

    return {"answer": answer}

def no_sop_node(state: WeatherBotState) -> dict:
    tags = state.get("activity_tags", [])
    weather = state.get("weather", {})
    selected = weather.get("selected_hourly", {})
    units = weather.get("units", {}).get("hourly", {})

    if any(tag in tags for tag in ["cycling", "biking", "two_wheeler"]):
        details = []

        wind = selected.get("wind_speed_10m")
        gusts = selected.get("wind_gusts_10m")

        if wind is not None:
            unit = units.get("wind_speed_10m", "km/h")
            details.append(f"forecast wind speed: {wind} {unit}")

        if gusts is not None:
            unit = units.get("wind_gusts_10m", "km/h")
            details.append(f"forecast wind gusts: {gusts} {unit}")

        weather_details = (
            " For the selected period, " + "; ".join(details) + "."
            if details
            else " Detailed wind values are unavailable for the selected period."
        )

        answer = (
            "Cycling advisory: No cycling-related safety procedure was triggered "
            "for the selected forecast period."
            f"{weather_details} "
            "This does not guarantee that cycling is safe. Check local conditions "
            "before riding and use your judgment."
        )

    else:
        answer = (
            "I couldn't find a matching safety procedure for this request. "
            "No recommendation is made because the available procedures do not "
            "cover the request or their conditions were not met."
        )

    return {"answer": answer}

def failure_node(state: WeatherBotState) -> dict:

    error = state.get(
        "error",
        "An unexpected error occurred."
    )

    answer = (
        "I'm sorry, but I couldn't retrieve the required "
        "weather information.\n\n"
        f"Details: {error}\n\n"
        "I won't provide a weather-based safety recommendation "
        "without verified weather data. Please try again later."
    )

    return {"answer": answer}