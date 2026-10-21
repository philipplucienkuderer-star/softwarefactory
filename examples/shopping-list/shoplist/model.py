"""Input rules and errors shared by the shopping list and the dishes.

Error messages are German because the web page shows them to the user as they are.
"""

import math

# Ordered like a walk through a typical German supermarket.
CATEGORIES = (
    "Obst & Gemüse",
    "Backwaren",
    "Kühlregal",
    "Fleisch & Fisch",
    "Vorrat",
    "Tiefkühl",
    "Getränke",
    "Drogerie",
    "Sonstiges",
)
DEFAULT_CATEGORY = "Sonstiges"
MAX_NAME_LENGTH = 80
MAX_UNIT_LENGTH = 12


class ValidationError(ValueError):
    """The input breaks a rule. The message is meant for the user."""


class NotFound(LookupError):
    """No record has the requested id."""


def clean_name(value, label="Name"):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} darf nicht leer sein.")
    value = " ".join(value.split())
    if len(value) > MAX_NAME_LENGTH:
        raise ValidationError(f"{label} darf höchstens {MAX_NAME_LENGTH} Zeichen haben.")
    return value


def clean_amount(value):
    """Return None for "no amount" (e.g. a pinch of salt), otherwise a positive number."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("Menge muss eine Zahl sein.")
    if not math.isfinite(value) or value <= 0:
        raise ValidationError("Menge muss größer als 0 sein.")
    return round(float(value), 2)


def clean_unit(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError("Einheit muss Text sein.")
    value = value.strip()
    if len(value) > MAX_UNIT_LENGTH:
        raise ValidationError(f"Einheit darf höchstens {MAX_UNIT_LENGTH} Zeichen haben.")
    return value


def clean_category(value):
    if value in (None, ""):
        return DEFAULT_CATEGORY
    if value not in CATEGORIES:
        raise ValidationError(f"Unbekannte Kategorie: {value}")
    return value


def find_by_id(records, record_id, label):
    for record in records:
        if record["id"] == record_id:
            return record
    raise NotFound(f"{label} {record_id} gibt es nicht.")
