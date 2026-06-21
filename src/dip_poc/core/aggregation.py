from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from ..api.models import Person

UNKNOWN_FRAKTION = "Fraktionslos / unbekannt"

# Light normalisation so trivial spelling variants don't split a bucket.
_FRAKTION_ALIASES = {
    "CDU": "CDU/CSU",
    "CSU": "CDU/CSU",
    "BÜNDNIS 90/DIE GRÜNEN": "BÜNDNIS 90/DIE GRÜNEN",
    "DIE GRÜNEN": "BÜNDNIS 90/DIE GRÜNEN",
}


def normalise_fraktion(raw: str | None) -> str:
    if not raw or not raw.strip():
        return UNKNOWN_FRAKTION
    cleaned = raw.strip()
    return _FRAKTION_ALIASES.get(cleaned.upper(), cleaned)


def resolve_fraktion(person: Person, wahlperiode: int) -> str:
    matching = [
        role for role in person.person_roles
        if role.fraktion and wahlperiode in role.wahlperiode_nummer
    ]
    if matching:
        return normalise_fraktion(matching[0].fraktion)
    any_with_fraktion = [role for role in person.person_roles if role.fraktion]
    if any_with_fraktion:
        return normalise_fraktion(any_with_fraktion[0].fraktion)
    return UNKNOWN_FRAKTION


@dataclass(frozen=True)
class FraktionShare:
    fraktion: str
    count: int
    percentage: float  # rounded to 2 decimals


@dataclass(frozen=True)
class DistributionResult:
    wahlperiode: int
    total_persons: int
    shares: list[FraktionShare]
    unknown_count: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "wahlperiode": self.wahlperiode,
            "total_persons": self.total_persons,
            "unknown_count": self.unknown_count,
            "shares": [
                {"fraktion": s.fraktion, "count": s.count, "percentage": s.percentage}
                for s in self.shares
            ],
            "notes": self.notes,
        }


def compute_distribution(persons: Iterable[Person], wahlperiode: int) -> DistributionResult:
    """Count persons per fraction and compute percentages. Deterministic."""
    counter: Counter[str] = Counter()
    total = 0
    for person in persons:
        counter[resolve_fraktion(person, wahlperiode)] += 1
        total += 1

    shares: list[FraktionShare] = []
    for fraktion, count in counter.most_common():
        pct = round(100.0 * count / total, 2) if total else 0.0
        shares.append(FraktionShare(fraktion=fraktion, count=count, percentage=pct))

    notes: list[str] = []
    unknown = counter.get(UNKNOWN_FRAKTION, 0)
    if unknown:
        notes.append(
            f"{unknown} von {total} Personen ohne eindeutige Fraktionszuordnung "
            f"(als '{UNKNOWN_FRAKTION}' gezählt)."
        )
    if total == 0:
        notes.append("Keine Personen für diese Wahlperiode gefunden.")

    return DistributionResult(
        wahlperiode=wahlperiode,
        total_persons=total,
        shares=shares,
        unknown_count=unknown,
        notes=notes,
    )
