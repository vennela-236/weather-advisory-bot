from app.policies.sop_matcher import match_sops


def test_high_wind_cycling():
    weather = {
        "current": {
            "wind_speed_10m": 45,
            "uv_index": 3
        }
    }

    result = match_sops(
        "Can I ride my bike today?",
        weather
    )

    assert result["match_found"] is True
    assert result["selected_sop"]["id"] == "SOP-001"


def test_high_uv_running():
    weather = {
        "selected_hourly": {
            "uv_index": 9,
            "apparent_temperature": 30
        }
    }

    result = match_sops(
        "Can I go running outside?",
        weather
    )

    assert result["match_found"] is True
    assert result["selected_sop"]["id"] == "SOP-002"


def test_fuzzy_picnic_scenario():
    weather = {
        "current": {}
    }

    result = match_sops(
        "Is today a good day for a picnic?",
        weather
    )

    assert result["match_found"] is True
    assert result["selected_sop"]["id"] == "SOP-005"


def test_no_matching_sop():
    weather = {
        "current": {
            "temperature_2m": 25
        }
    }

    result = match_sops(
        "Can I read a book indoors?",
        weather
    )

    assert result["match_found"] is False
    assert result["selected_sop"] is None


def test_unknown_severe_weather_hazard():
    weather = {
        "current": {
            "wind_speed_10m": 10
        }
    }

    result = match_sops(
        "Should I go cycling?",
        weather
    )

    assert "SOP-013" not in [
        sop["id"] for sop in result["matched_sops"]
    ]