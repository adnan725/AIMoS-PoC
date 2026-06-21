import json
from pathlib import Path

import pytest

from dip_poc.api.models import Person
from dip_poc.core.aggregation import (
    UNKNOWN_FRAKTION,
    compute_distribution,
    normalise_fraktion,
    resolve_fraktion,
)

FIXTURE = Path(__file__).parent / "fixtures" / "persons_wp20.json"


@pytest.fixture
def persons():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return [Person.model_validate(d) for d in data["documents"]]


def test_normalise_aliases_merge_cdu_csu():
    assert normalise_fraktion("CDU") == "CDU/CSU"
    assert normalise_fraktion("CSU") == "CDU/CSU"
    assert normalise_fraktion("  ") == UNKNOWN_FRAKTION
    assert normalise_fraktion(None) == UNKNOWN_FRAKTION


def test_resolve_picks_role_matching_wahlperiode(persons):
    schmidt = next(p for p in persons if p.nachname == "Schmidt")
    # Schmidt was SPD in WP19 but GRÜNE in WP20 — must resolve per period.
    assert resolve_fraktion(schmidt, 20) == "BÜNDNIS 90/DIE GRÜNEN"
    assert resolve_fraktion(schmidt, 19) == "SPD"


def test_person_without_role_is_unknown(persons):
    otto = next(p for p in persons if p.nachname == "Ohnefraktion")
    assert resolve_fraktion(otto, 20) == UNKNOWN_FRAKTION


def test_distribution_counts_and_percentages(persons):
    result = compute_distribution(persons, 20)
    assert result.total_persons == 5
    by_fraktion = {s.fraktion: s for s in result.shares}
    # Merz (CDU/CSU) + Beispiel (CDU -> CDU/CSU) = 2
    assert by_fraktion["CDU/CSU"].count == 2
    assert by_fraktion["CDU/CSU"].percentage == 40.0
    # Mustermann SPD = 1 (Schmidt is GRÜNE in WP20, not SPD)
    assert by_fraktion["SPD"].count == 1
    assert by_fraktion["BÜNDNIS 90/DIE GRÜNEN"].count == 1
    assert by_fraktion[UNKNOWN_FRAKTION].count == 1


def test_percentages_sum_to_100(persons):
    result = compute_distribution(persons, 20)
    assert round(sum(s.percentage for s in result.shares), 2) == 100.0


def test_unknown_surfaced_in_notes(persons):
    result = compute_distribution(persons, 20)
    assert result.unknown_count == 1
    assert any("Fraktionszuordnung" in n for n in result.notes)


def test_empty_input_is_safe():
    result = compute_distribution([], 20)
    assert result.total_persons == 0
    assert result.shares == []
    assert any("Keine Personen" in n for n in result.notes)
