import re
from typing import Any


SEVERITY_PRIORITY = {
    "critical": 4,
    "high": 3,
    "moderate": 2,
    "contextual": 1,
    "low": 0
}


# Maps different user expressions to standardized activity tags.
ACTIVITY_ALIASES = {
    "cycling": [
        "cycle", "cycling", "bike", "biking", "bicycle",
        "bike ride", "cycle ride"
    ],
    "running": [
        "run", "running", "jog", "jogging"
    ],
    "walking": [
        "walk", "walking", "stroll"
    ],
    "travel": [
        "travel", "journey", "commute", "commuting",
        "go to work", "drive", "driving"
    ],
    "picnic": [
        "picnic", "outing", "outdoor gathering"
    ],
    "children": [
        "child", "children", "kid", "kids", "my son",
        "my daughter", "my baby"
    ],
    "elderly": [
        "elderly", "senior citizen", "older people",
        "old parents", "grandparents"
    ],
    "pets": [
        "pet", "pets", "dog", "dogs", "puppy",
        "walking my dog", "walk my dog"
    ],
    "park_visit": [
        "park", "playground"
    ],
        "outdoor_exercise": [
        "exercise", "workout", "outdoor exercise"
    ],
        "outdoor_meal": [
        "outdoor lunch", "picnic", "eat outside", "lunch outdoors"
    ],
    "uv_exposure": [
        "uv", "uv index", "uv exposure",
        "sun exposure", "strong sunlight"
    ]
}


OUTDOOR_KEYWORDS = [
    "outdoor", "outside", "park", "picnic", "garden",
    "cycling", "bike", "bicycle", "running", "jogging",
    "walking", "hiking", "trekking", "sports",
    "playground", "exercise"
]


def normalize_text(text: str) -> str:
    """Normalize user text for intent matching."""

    return re.sub(r"\s+", " ", text.lower().strip())


def extract_activity_tags(
    query: str,
    previous_tags: list[str] | None = None
) -> list[str]:
    """
    Extract activity and user-group tags from the query.

    Previous tags support follow-up questions such as:
    'What about this evening?'
    """

    text = normalize_text(query)

    tags = set(previous_tags or [])

    for tag, aliases in ACTIVITY_ALIASES.items():

        for alias in aliases:

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text):
                tags.add(tag)
                break

    # Cycling and two-wheeler are related but distinct tags.
    if "cycling" in tags:
        tags.update(["biking", "two_wheeler"])

    if "travel" in tags and "cycling" not in tags:
        tags.add("journey")

    # Identify general outdoor activities.
    is_outdoor = any(
        re.search(r"\b" + re.escape(keyword) + r"\b", text)
        for keyword in OUTDOOR_KEYWORDS
    )

    if tags and (
        is_outdoor
        or "picnic" in tags
        or "park_visit" in tags
    ):
        tags.add("outdoor_any")

    return list(tags)


def sop_applies_to_activity(
    sop: dict,
    activity_tags: list[str]
) -> bool:
    """
    Check whether a policy covers the identified activity.
    """

    applicable_tags = set(sop.get("applies_to", []))
    user_tags = set(activity_tags)

    if "outdoor_any" in applicable_tags:
        return "outdoor_any" in user_tags

    return bool(applicable_tags.intersection(user_tags))


def get_field_value(
    data: dict,
    field_path: str
) -> Any:
    """
    Retrieve a nested field using dot notation.

    Example:
    current.wind_speed_10m

    For hourly fields, selected_hourly takes priority.
    """

    parts = field_path.split(".")

    if parts[0] == "hourly" and "selected_hourly" in data:
        selected = data["selected_hourly"]

        if parts[1] in selected:
            value = selected[parts[1]]

            for part in parts[2:]:
                if not isinstance(value, dict):
                    return None

                value = value.get(part)

            return value

    value = data

    for part in parts:

        if not isinstance(value, dict):
            return None

        if part not in value:
            return None

        value = value[part]

    return value


def evaluate_single_condition(
    actual_value: Any,
    operator: str,
    expected_value: Any
) -> bool:
    """
    Evaluate one policy condition.

    Supports scalar values and lists of hourly values.
    Missing data never counts as a match.
    """

    if actual_value is None:
        return False

    if isinstance(actual_value, list):
        return any(
            evaluate_single_condition(
                item,
                operator,
                expected_value
            )
            for item in actual_value
        )

    try:
        if operator == "gt":
            return actual_value > expected_value

        elif operator == "gte":
            return actual_value >= expected_value

        elif operator == "lt":
            return actual_value < expected_value

        elif operator == "lte":
            return actual_value <= expected_value

        elif operator == "equals":
            return actual_value == expected_value

        elif operator == "in":
            return actual_value in expected_value

        elif operator == "not_equals":
            return actual_value != expected_value

    except (TypeError, ValueError):
        return False

    raise ValueError(
        f"Unsupported SOP operator: {operator}"
    )


def evaluate_condition(
    condition: dict,
    weather: dict
) -> bool:
    """Evaluate a condition against weather and hazard data."""

    field = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    if not field or not operator:
        return False

    actual = get_field_value(weather, field)

    return evaluate_single_condition(
        actual,
        operator,
        expected
    )


def evaluate_sop_conditions(
    sop: dict,
    weather: dict
) -> bool:
    """
    Evaluate the complete SOP condition.

    - Every condition in 'all' must pass.
    - At least one condition in 'any' must pass.
    - An SOP with no conditions is unconditional.
    """

    rules = sop.get("when", {})

    all_conditions = rules.get("all", [])
    any_conditions = rules.get("any", [])

    if not all_conditions and not any_conditions:
        return True

    all_passed = all(
        evaluate_condition(condition, weather)
        for condition in all_conditions
    )

    any_passed = (
        any(
            evaluate_condition(condition, weather)
            for condition in any_conditions
        )
        if any_conditions
        else True
    )

    return all_passed and any_passed


def match_sops(
    query: str,
    weather: dict,
    previous_tags: list[str] | None = None
) -> dict:
    """
    Find all applicable SOPs and select the highest-severity policy.

    Resolution strategy:
    1. Match activity.
    2. Evaluate weather conditions.
    3. Sort matching policies by severity.
    4. Select the highest-severity SOP.
    """

    from app.policies.sop_loader import load_sops

    activity_tags = extract_activity_tags(
        query,
        previous_tags
    )

    all_sops = load_sops()

    matches = []

    for sop in all_sops:

        if not sop_applies_to_activity(
            sop,
            activity_tags
        ):
            continue

        if not evaluate_sop_conditions(
            sop,
            weather
        ):
            continue

        matches.append(sop)

    matches.sort(
        key=lambda sop: SEVERITY_PRIORITY.get(
            sop["severity"].lower(),
            -1
        ),
        reverse=True
    )

    return {
        "activity_tags": activity_tags,
        "matched_sops": matches,
        "selected_sop": matches[0] if matches else None,
        "match_found": bool(matches),
        "resolution_strategy": "highest_severity"
    }