from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PersonRole(BaseModel):
    model_config = ConfigDict(extra="ignore")

    funktion: str | None = None
    fraktion: str | None = None
    nachname: str | None = None
    vorname: str | None = None
    wahlperiode_nummer: list[int] = Field(default_factory=list)


class Person(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    nachname: str | None = None
    vorname: str | None = None
    titel: str | None = None
    wahlperiode: list[int] = Field(default_factory=list)
    fraktion: list[str] = Field(default_factory=list)
    funktion: list[str] = Field(default_factory=list)
    basisdatum: str | None = None
    aktualisiert: str | None = None

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.vorname, self.nachname) if p]
        return " ".join(parts) if parts else (self.titel or self.id)


class PersonListResponse(BaseModel):

    model_config = ConfigDict(extra="ignore")

    num_found: int = Field(alias="numFound")
    documents: list[Person] = Field(default_factory=list)
    cursor: str | None = None
