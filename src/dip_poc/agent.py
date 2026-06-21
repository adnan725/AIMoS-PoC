from __future__ import annotations

import asyncio
import json
import logging
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import settings
from .observability import (
    ValidationError,
    configure_logging,
    new_correlation_id,
    security_validation_rejected,
    timed,
    tool_completed,
    tool_selected,
    validate_tool_args,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Assistent für Daten des Deutschen Bundestags (DIP). "
    "Du hast Zugriff auf Tools, die echte Daten abrufen. Wähle bei jeder Frage "
    "eigenständig das passende Tool. Wenn ein Tool ein Ergebnis liefert, fasse es "
    "in klarem, sachlichem Deutsch zusammen. Erfinde keine Zahlen — nutze nur die "
    "von den Tools gelieferten Werte."
)

# Server is launched in-process as a subprocess via the module entry point.
_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "dip_poc.mcp.server"],
)


def _mcp_tools_to_groq(mcp_tools) -> list[dict]:
    """Translate MCP tool definitions into Groq function-calling schema."""
    out = []
    for t in mcp_tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": (t.description or "").strip(),
                    "parameters": t.inputSchema,
                },
            }
        )
    return out


async def _run_turn(session: ClientSession, groq_client, model: str, history: list[dict]) -> str:
    cid = new_correlation_id()
    logger.info("turn.start", extra={"event": {"type": "turn.start", "correlation_id": cid}})
    tools_resp = await session.list_tools()
    groq_tools = _mcp_tools_to_groq(tools_resp.tools)

    # First call: let the model decide whether/which tool to use.
    completion = groq_client.chat.completions.create(
        model=model, messages=history, tools=groq_tools, tool_choice="auto", temperature=0.2
    )
    msg = completion.choices[0].message

    if not msg.tool_calls:
        history.append({"role": "assistant", "content": msg.content})
        return msg.content

    # Record the assistant's tool-call request.
    history.append(
        {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        }
    )

    # Execute each requested tool through the MCP session.
    for tc in msg.tool_calls:
        raw_args = json.loads(tc.function.arguments or "{}")
        # Security gate: validate LLM-supplied args before they reach a tool.
        try:
            args = validate_tool_args(tc.function.name, raw_args)
        except ValidationError as exc:
            security_validation_rejected(tc.function.name, reason=str(exc))
            history.append(
                {"role": "tool", "tool_call_id": tc.id, "name": tc.function.name,
                 "content": json.dumps({"error": f"invalid arguments: {exc}"})}
            )
            continue

        tool_selected(tc.function.name, args)
        ok, err, payload = True, None, ""
        with timed("tool_exec") as t:
            try:
                result = await session.call_tool(tc.function.name, args)
                payload = "\n".join(
                    block.text for block in result.content
                    if getattr(block, "type", None) == "text"
                )
            except Exception as exc:  # surface failure to the model, keep loop alive
                ok, err = False, str(exc)
                payload = json.dumps({"error": err})
        tool_completed(tc.function.name, t["duration_ms"], ok=ok, error=err)
        history.append(
            {"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": payload}
        )

    # Second call: model formulates the final answer from the tool output.
    final = groq_client.chat.completions.create(
        model=model, messages=history, temperature=0.2
    )
    answer = final.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    return answer


async def chat_loop(one_shot: str | None = None) -> None:
    if not settings.groq_api_key:
        print("GROQ_API_KEY ist nicht gesetzt. Bitte in .env eintragen "
              "(kostenloser Key: https://groq.com/).")
        return

    from groq import Groq

    groq_client = Groq(api_key=settings.groq_api_key)
    history: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]

    async with stdio_client(_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print(f"✓ Verbunden mit MCP-Server. Verfügbare Tools: "
                  f"{', '.join(t.name for t in tools)}\n")

            if one_shot is not None:
                history.append({"role": "user", "content": one_shot})
                print(await _run_turn(session, groq_client, settings.groq_model, history))
                return

            print("Stelle eine Frage (z. B. 'Wie ist die Fraktionsverteilung in der "
                  "20. Wahlperiode?'). Beenden mit 'exit'.\n")
            while True:
                try:
                    user = input("Du> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if user.lower() in {"exit", "quit", "ende"}:
                    break
                if not user:
                    continue
                history.append({"role": "user", "content": user})
                answer = await _run_turn(session, groq_client, settings.groq_model, history)
                print(f"\nAssistant> {answer}\n")


def main() -> None:
    import os

    configure_logging(json_output=os.getenv("LOG_FORMAT", "json") == "json")
    one_shot = " ".join(sys.argv[1:]) or None
    asyncio.run(chat_loop(one_shot))


if __name__ == "__main__":
    main()
