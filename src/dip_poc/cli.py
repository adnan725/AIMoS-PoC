from __future__ import annotations

import argparse
import logging
import os

from .llm.formatter import format_distribution
from .observability import configure_logging, new_correlation_id
from .services import get_fraktion_distribution


def main() -> None:
    parser = argparse.ArgumentParser(description="DIP Fraktionsverteilung (PoC)")
    parser.add_argument("--wahlperiode", "-w", type=int, default=20)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    configure_logging(
        level=logging.INFO if args.verbose else logging.WARNING,
        json_output=os.getenv("LOG_FORMAT", "json") == "json",
    )
    new_correlation_id()

    print(f"Lade Personendaten für die {args.wahlperiode}. Wahlperiode …\n")
    result = get_fraktion_distribution(args.wahlperiode)

    print(f"{'Fraktion':<35}{'Anzahl':>8}{'Anteil':>10}")
    print("-" * 53)
    for s in result.shares:
        print(f"{s.fraktion:<35}{s.count:>8}{s.percentage:>9.2f}%")
    print("-" * 53)
    print(f"{'Gesamt':<35}{result.total_persons:>8}\n")

    print("LLM-Auswertung:\n")
    print(format_distribution(result))


if __name__ == "__main__":
    main()
