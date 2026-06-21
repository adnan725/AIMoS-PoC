from __future__ import annotations

import logging

from .api.client import DIPClient
from .api.models import Person
from .core.aggregation import DistributionResult, compute_distribution, resolve_fraktion

logger = logging.getLogger(__name__)

# calculate the distribution of fraktionszugehörigkeit for a given wahlperiode,
def get_fraktion_distribution(wahlperiode: int, client: DIPClient | None = None) -> DistributionResult:
    owns = client is None
    client = client or DIPClient()
    try:
        persons = list(client.iter_persons(wahlperiode))
        logger.info("fetched %d persons for WP%d", len(persons), wahlperiode)
        return compute_distribution(persons, wahlperiode)
    finally:
        if owns:
            client.close()

# get information about a person by name (or name fragment)
def get_person_info(name: str, wahlperiode: int | None = None, client: DIPClient | None = None) -> dict:
    owns = client is None
    client = client or DIPClient()
    try:
        matches = client.get_person_by_name(name, wahlperiode)
        if not matches:
            return {"query": name, "found": False, "candidates": []}
        return {
            "query": name,
            "found": True,
            "candidates": [_summarise_person(p) for p in matches[:5]],
        }
    finally:
        if owns:
            client.close()


# 
def _summarise_person(person: Person) -> dict:
    wp = person.wahlperiode[-1] if person.wahlperiode else 0
    roles = [
        {
            "funktion": r.funktion,
            "fraktion": r.fraktion,
            "wahlperioden": r.wahlperiode_nummer,
        }
        for r in person.person_roles
    ]
    return {
        "id": person.id,
        "name": person.full_name,
        "titel": person.titel,
        "wahlperioden": person.wahlperiode,
        "aktuelle_fraktion": resolve_fraktion(person, wp) if wp else None,
        "rollen": roles,
    }
