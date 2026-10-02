import json
from pathlib import Path
from typing import Any


SOP_FILE = Path(__file__).parent / "sops.json"


class SOPLoadingError(Exception):
    """Raised when SOP policies cannot be loaded."""


def load_sops() -> list[dict[str, Any]]:
    """
    Dynamically load SOP policies from the JSON file.
    """

    try:
        with open(SOP_FILE, "r", encoding="utf-8") as file:
            sops = json.load(file)

    except FileNotFoundError as error:
        raise SOPLoadingError(
            f"SOP file not found: {SOP_FILE}"
        ) from error

    except json.JSONDecodeError as error:
        raise SOPLoadingError(
            "SOP JSON file contains invalid syntax."
        ) from error

    if not isinstance(sops, list):
        raise SOPLoadingError(
            "SOP file must contain a JSON list."
        )

    required_fields = {
        "id",
        "title",
        "category",
        "severity",
        "applies_to",
        "when",
        "advice",
        "reason"
    }

    seen_ids = set()

    for index, sop in enumerate(sops):

        if not isinstance(sop, dict):
            raise SOPLoadingError(
                f"SOP at position {index} must be an object."
            )

        missing_fields = required_fields - set(sop.keys())

        if missing_fields:
            raise SOPLoadingError(
                f"SOP at position {index} is missing: "
                f"{missing_fields}"
            )

        if sop["id"] in seen_ids:
            raise SOPLoadingError(
                f"Duplicate SOP ID: {sop['id']}"
            )

        seen_ids.add(sop["id"])

        if not isinstance(sop["applies_to"], list):
            raise SOPLoadingError(
                f"{sop['id']}: applies_to must be a list."
            )

        if not isinstance(sop["when"], dict):
            raise SOPLoadingError(
                f"{sop['id']}: when must be an object."
            )

    return sops