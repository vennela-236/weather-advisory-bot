from typing import TypedDict, Any


class WeatherBotState(TypedDict, total=False):
    # User input
    question: str
    session_id: str

    # Conversation context
    conversation_history: list[dict]
    previous_activity_tags: list[str]

    # Extracted information
    location: str
    activity_tags: list[str]
    requested_time: str

    requested_date: str
    requested_period: str

    # Weather information
    coordinates: dict[str, Any]
    weather: dict[str, Any]

    # SOP matching
    matched_sops: list[dict]
    selected_sop: dict | None
    match_found: bool
    resolution_strategy: str

    # Execution status
    weather_available: bool
    error: str | None
    error_type: str | None 

    # Final response
    answer: str