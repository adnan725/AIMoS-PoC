from __future__ import annotations

import re

# A current+historic-safe range for Bundestag Wahlperioden.
_MIN_WP = 1
_MAX_WP = 30
_MAX_NAME_LEN = 80
# Letters (incl. German + accents), spaces, hyphen, apostrophe, dot.
_NAME_RE = re.compile(r"^[\w\s.\-']+$", re.UNICODE)


class ValidationError(ValueError):
    """Raised when a tool argument fails a security/sanity check."""


def validate_wahlperiode(value: object) -> int:
    try:
        wp = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValidationError(f"wahlperiode must be an integer, got {value!r}")
    if not (_MIN_WP <= wp <= _MAX_WP):
        raise ValidationError(
            f"wahlperiode {wp} out of plausible range [{_MIN_WP}, {_MAX_WP}]"
        )
    return wp


def validate_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"name must be a string, got {type(value).__name__}")
    name = value.strip()
    if not name:
        raise ValidationError("name must not be empty")
    if len(name) > _MAX_NAME_LEN:
        raise ValidationError(f"name too long ({len(name)} > {_MAX_NAME_LEN})")
    if not _NAME_RE.match(name):
        raise ValidationError("name contains disallowed characters")
    return name


def validate_tool_args(tool_name: str, args: dict) -> dict:
    """Validate+sanitise args for a known tool. Returns cleaned args."""
    cleaned = dict(args)
    if "wahlperiode" in cleaned and cleaned["wahlperiode"] is not None:
        cleaned["wahlperiode"] = validate_wahlperiode(cleaned["wahlperiode"])
    if "name" in cleaned and cleaned["name"] is not None:
        cleaned["name"] = validate_name(cleaned["name"])
    return cleaned
