from __future__ import annotations

import json
import logging

from ..config import Settings, settings as default_settings
from ..core.aggregation import DistributionResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Du bist ein präziser Datenanalyst für parlamentarische Daten. "
    "Du erhältst eine bereits fertig berechnete Fraktionsverteilung als JSON. "
    "Deine Aufgabe ist es ausschließlich, diese Zahlen in einen klaren, "
    "sachlichen deutschen Fließtext zu fassen. Erfinde keine Zahlen, ändere "
    "keine Werte, rechne nichts neu. Nenne die größten Fraktionen zuerst, "
    "weise auf Datenlücken in den 'notes' hin, und halte dich kurz (3–6 Sätze)."
)


def _fallback_text(result: DistributionResult) -> str:
    if not result.shares:
        return f"Für die {result.wahlperiode}. Wahlperiode wurden keine Personen gefunden."
    lines = [
        f"In der {result.wahlperiode}. Wahlperiode wurden {result.total_persons} "
        f"Personen ausgewertet. Die Fraktionsverteilung:"
    ]
    for s in result.shares:
        lines.append(f"  • {s.fraktion}: {s.count} ({s.percentage:.2f} %)")
    lines.extend(result.notes)
    return "\n".join(lines)


def format_distribution(result: DistributionResult, settings: Settings | None = None) -> str:
    settings = settings or default_settings
    if not settings.groq_api_key:
        logger.info("no GROQ_API_KEY set — using deterministic fallback formatter")
        return _fallback_text(result)

    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Formuliere eine Auswertung dieser Verteilung:\n"
                    + json.dumps(result.as_dict(), ensure_ascii=False, indent=2),
                },
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:  # never let formatting break the pipeline
        logger.warning("Groq formatting failed (%s) — using fallback", exc)
        return _fallback_text(result)
