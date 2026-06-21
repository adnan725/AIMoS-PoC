import pytest

from dip_poc.observability.logging_setup import redact
from dip_poc.observability.validation import (
    ValidationError,
    validate_name,
    validate_tool_args,
    validate_wahlperiode,
)


# --- validation ----------------------------------------------------------
def test_wahlperiode_accepts_valid():
    assert validate_wahlperiode(20) == 20
    assert validate_wahlperiode("20") == 20


@pytest.mark.parametrize("bad", [0, -1, 99, "abc", None])
def test_wahlperiode_rejects_invalid(bad):
    with pytest.raises(ValidationError):
        validate_wahlperiode(bad)


def test_name_accepts_german_characters():
    assert validate_name("Friedrich Merz") == "Friedrich Merz"
    assert validate_name("Gregor Gysi-Müller") == "Gregor Gysi-Müller"


@pytest.mark.parametrize("bad", ["", "   ", "a" * 200, "DROP TABLE;", "x\x00y"])
def test_name_rejects_bad_input(bad):
    with pytest.raises(ValidationError):
        validate_name(bad)


def test_validate_tool_args_cleans_both():
    cleaned = validate_tool_args("person_info", {"name": "  Merz ", "wahlperiode": "20"})
    assert cleaned["name"] == "Merz"
    assert cleaned["wahlperiode"] == 20


# --- redaction -----------------------------------------------------------
def test_redact_dip_apikey_param():
    out = redact("GET /person?apikey=OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw&x=1")
    assert "OSOegLs" not in out
    assert "REDACTED" in out


def test_redact_authorization_header():
    out = redact("Authorization: ApiKey OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3h")
    assert "OSOegLs" not in out


def test_redact_groq_key():
    out = redact("key=gsk_abcdEFGH1234567890")
    assert "gsk_abcdEFGH" not in out
    assert "REDACTED" in out
