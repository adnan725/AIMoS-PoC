from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..llm.formatter import format_distribution
from ..observability import configure_logging
from ..services import get_fraktion_distribution, get_person_info

configure_logging()

mcp = FastMCP("dip-fraktion")

@mcp.tool()
def fraktion_distribution(wahlperiode: int) -> dict:
    """Berechnet die prozentuale Fraktionsverteilung aller Personen einer Wahlperiode.

    Nutze dieses Tool für Fragen wie 'Wie ist die Fraktionsverteilung in der
    20. Wahlperiode?'. Gibt strukturierte Zahlen UND einen lesbaren Text zurück.

    Args:
        wahlperiode: Die Nummer der Wahlperiode, z. B. 20.
    """
    result = get_fraktion_distribution(wahlperiode)
    return {"data": result.as_dict(), "summary": format_distribution(result)}


@mcp.tool()
def person_info(name: str, wahlperiode: int | None = None) -> dict:
    """Liefert Informationen zu einer Person (z. B. 'Wer ist Friedrich Merz?').

    Args:
        name: Name oder Namensteil der gesuchten Person.
        wahlperiode: Optional auf eine Wahlperiode einschränken.
    """

    return get_person_info(name, wahlperiode)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
