import React, { useEffect, useState } from "react";
import { partyColor, textOn, fetchJSON } from "./lib.js";

function Row({ s, max }) {
  const c = partyColor(s.fraktion);
  return (
    <tr className="border-b border-line/60 last:border-0">
      <td className="py-2.5 pr-3">
        <span className="flex items-center gap-2.5">
          <span
            className="inline-block h-3 w-3 shrink-0 rounded-[3px]"
            style={{ backgroundColor: c }}
          />
          <span className="font-medium">{s.fraktion}</span>
        </span>
      </td>
      <td className="py-2.5 text-right font-mono tabular-nums">{s.count}</td>
      <td className="py-2.5 pl-3 text-right font-mono tabular-nums">
        {s.percentage.toFixed(2)}%
      </td>
    </tr>
  );
}

export default function DistributionPanel({ wahlperiode }) {
  const [state, setState] = useState({ status: "loading" });

  useEffect(() => {
    let alive = true;
    setState({ status: "loading" });
    fetchJSON(`/api/distribution/${wahlperiode}`)
      .then((d) => alive && setState({ status: "ok", ...d }))
      .catch((e) => alive && setState({ status: "error", message: e.message }));
    return () => {
      alive = false;
    };
  }, [wahlperiode]);

  if (state.status === "loading") {
    return (
      <div className="flex h-full items-center justify-center text-ink/50">
        <span className="font-mono text-sm">Lade {wahlperiode}. Wahlperiode …</span>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center">
        <span className="font-display text-lg font-semibold">
          Daten nicht verfügbar
        </span>
        <p className="max-w-sm text-sm text-ink/60">{state.message}</p>
        <p className="max-w-sm text-xs text-ink/40">
          Häufige Ursache: der DIP-API-Schlüssel ist abgelaufen oder fehlt.
          Trage einen gültigen Schlüssel als DIP_API_KEY in die .env ein.
        </p>
      </div>
    );
  }

  const { data, summary } = state;
  const max = Math.max(...data.shares.map((s) => s.count), 1);

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-ink/45">
          Fraktionsverteilung
        </p>
        <h2 className="mt-1 font-display text-3xl font-semibold">
          {data.wahlperiode}. Wahlperiode
        </h2>
        <p className="mt-1 text-sm text-ink/55">
          {data.total_persons.toLocaleString("de-DE")} Personen ausgewertet
        </p>
      </header>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left font-mono text-xs uppercase tracking-wide text-ink/45">
            <th className="pb-2 font-medium">Fraktion</th>
            <th className="pb-2 text-right font-medium">Anzahl</th>
            <th className="pb-2 text-right font-medium">Anteil</th>
          </tr>
        </thead>
        <tbody>
          {data.shares.map((s) => (
            <Row key={s.fraktion} s={s} max={max} />
          ))}
        </tbody>
      </table>

      {summary && (
        <div className="rounded-sm border border-line bg-surface p-4">
          <p className="mb-1.5 font-mono text-xs uppercase tracking-[0.18em] text-ink/45">
            Auswertung
          </p>
          <p className="whitespace-pre-line text-sm leading-relaxed text-ink/80">
            {summary}
          </p>
        </div>
      )}

      {data.notes?.length > 0 && (
        <ul className="space-y-1 text-xs text-ink/50">
          {data.notes.map((n, i) => (
            <li key={i}>· {n}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
