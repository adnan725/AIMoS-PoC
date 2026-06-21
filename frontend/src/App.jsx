import React, { useEffect, useState } from "react";
import DistributionPanel from "./DistributionPanel.jsx";
import ChatPanel from "./ChatPanel.jsx";
import { fetchJSON } from "./lib.js";

const QUICK_PERIODS = [21, 20, 19, 18];

export default function App() {
  const [period, setPeriod] = useState(20);
  const [customInput, setCustomInput] = useState("");
  const [groqConfigured, setGroqConfigured] = useState(true);

  useEffect(() => {
    fetchJSON("/api/health")
      .then((h) => setGroqConfigured(h.groq_configured))
      .catch(() => setGroqConfigured(false));
  }, []);

  function loadCustom() {
    const wp = parseInt(customInput, 10);
    if (Number.isNaN(wp) || wp < 1 || wp > 30) return;
    setPeriod(wp);
    setCustomInput("");
  }

  return (
    <div className="flex h-full flex-col bg-[#f7f5f0] text-[#2d2d2d]">
      {/* Masthead */}
      <header className="border-b border-[#dedede] bg-white px-6 py-3 background-color: #fd5108">
        <div className="flex items-baseline gap-3 background-color: #fd5108">
          <span className=" text-base font-bold tracking-tight text-[#000000]">
            DIP
          </span>
          <span className="text-[11px] uppercase tracking-[0.22em] text-[#7d7d7d]">
            Dokumentations- &amp; Informationssystem · Bundestag
          </span>
        </div>
      </header>

      {/* Wahlperiode selection: quick picks + free input */}
      <nav className="flex flex-wrap items-center gap-1 border-b border-[#dedede] bg-[#f7f5f0] px-4 py-1">
        {QUICK_PERIODS.map((p) => {
          const active = p === period;
          return (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`relative px-4 py-3 font-[Arial] text-sm transition-colors ${
                active ? "text-[#000000]" : "text-[#7d7d7d] hover:text-[#2d2d2d]"
              }`}
            >
              WP {p}
              {active && (
                <span className="absolute inset-x-3 -bottom-px h-0.5 bg-[#e0301e]" />
              )}
            </button>
          );
        })}

        {!QUICK_PERIODS.includes(period) && (
          <span className="relative px-4 py-3 font-[Arial] text-sm text-[#000000]">
            WP {period}
            <span className="absolute inset-x-3 -bottom-px h-0.5 bg-[#e0301e]" />
          </span>
        )}

        <span className="mx-2 h-5 w-px bg-[#dedede]" />

        <div className="flex items-center gap-1.5 py-1.5">
          <input
            type="number"
            min={1}
            max={30}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") loadCustom();
            }}
            placeholder="WP"
            aria-label="Wahlperiode eingeben"
            className="w-16 rounded-md border border-[#dedede] bg-white px-2.5 py-1.5 font-[Arial] text-sm text-[#2d2d2d] outline-none transition-colors focus:border-[#d04a02] [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
          />
          <button
            onClick={loadCustom}
            disabled={!customInput.trim()}
            className="rounded-md bg-[#000000] px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:bg-[#d04a02] disabled:opacity-30"
          >
            Laden
          </button>
        </div>
      </nav>

      {/* Split: distribution left, chat right */}
      <main className="grid flex-1 grid-cols-1 overflow-hidden lg:grid-cols-[1.15fr_0.85fr]">
        <section className="min-h-0 border-b border-[#dedede] lg:border-b-0 lg:border-r">
          <DistributionPanel wahlperiode={period} />
        </section>
        <section className="min-h-0">
          <ChatPanel groqConfigured={groqConfigured} />
        </section>
      </main>
    </div>
  );
}