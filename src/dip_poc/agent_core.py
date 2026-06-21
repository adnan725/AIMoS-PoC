from __future__ import annotations

import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import settings
from .observability import (
    ValidationError,
    new_correlation_id,
    security_validation_rejected,
    timed,
    tool_completed,
    tool_selected,
    validate_tool_args,
)

from groq import Groq

_SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Assistent für Daten des Deutschen Bundestags (DIP). "
    "Du hast Zugriff auf Tools, die echte Daten abrufen. Wähle bei jeder Frage "
    "eigenständig das passende Tool. Wenn ein Tool ein Ergebnis liefert, fasse es "
    "in klarem, sachlichem Deutsch zusammen. Erfinde keine Zahlen — nutze nur die "
    "von den Tools gelieferten Werte."
)

_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "dip_poc.mcp.server"],
)


def _mcp_tools_to_groq(mcp_tools) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "").strip(),
                "parameters": t.inputSchema,
            },
        }
        for t in mcp_tools
    ]


async def answer_question(question: str, history: list[dict] | None = None) -> dict:

    if not settings.groq_api_key:
        return {
            "answer": "GROQ_API_KEY ist nicht gesetzt. Bitte trage einen kostenlosen "
            "Key aus https://console.groq.com/keys in die .env ein, um den "
            "Chat zu nutzen.",
            "tools_used": [],
            "correlation_id": None,
        }

    cid = new_correlation_id()
    groq_client = Groq(api_key=settings.groq_api_key)
    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history or [])
    messages.append({"role": "user", "content": question})
    tools_used: list[dict] = []

    async with stdio_client(_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            groq_tools = _mcp_tools_to_groq((await session.list_tools()).tools)

            first = groq_client.chat.completions.create(
                model=settings.groq_model, messages=messages,
                tools=groq_tools, tool_choice="auto", temperature=0.2,
            )
            msg = first.choices[0].message

            if not msg.tool_calls:
                return {"answer": msg.content, "tools_used": [], "correlation_id": cid}

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                raw_args = json.loads(tc.function.arguments or "{}")
                try:
                    args = validate_tool_args(tc.function.name, raw_args)
                except ValidationError as exc:
                    security_validation_rejected(tc.function.name, reason=str(exc))
                    messages.append({"role": "tool", "tool_call_id": tc.id,
                                     "name": tc.function.name,
                                     "content": json.dumps({"error": f"invalid arguments: {exc}"})})
                    tools_used.append({"name": tc.function.name, "args": args, "ok": False})
                    continue

                tool_selected(tc.function.name, args)
                ok, err, payload = True, None, ""
                with timed("tool_exec") as t:
                    try:
                        result = await session.call_tool(tc.function.name, args)
                        payload = "\n".join(
                            b.text for b in result.content
                            if getattr(b, "type", None) == "text"
                        )
                    except Exception as exc:
                        ok, err = False, str(exc)
                        payload = json.dumps({"error": err})
                tool_completed(tc.function.name, t["duration_ms"], ok=ok, error=err)
                tools_used.append({"name": tc.function.name, "args": args, "ok": ok})
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "name": tc.function.name, "content": payload})

            final = groq_client.chat.completions.create(
                model=settings.groq_model, messages=messages, temperature=0.2,
            )
            return {
                "answer": final.choices[0].message.content,
                "tools_used": tools_used,
                "correlation_id": cid,
            }
