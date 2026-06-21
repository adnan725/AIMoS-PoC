// Real political colours so the proportion bar reads like an actual parliament.
// Keys are matched case-insensitively against the fraction name from the API.
const PARTY_COLORS = [
  { match: /cdu|csu|union/i, color: "#1A1A1A", label: "CDU/CSU" },
  { match: /spd/i, color: "#E3000F", label: "SPD" },
  { match: /grün|grune|b90/i, color: "#1FAE55", label: "Grüne" },
  { match: /fdp|frei/i, color: "#FFD600", label: "FDP" },
  { match: /afd|alternative/i, color: "#0A8FDC", label: "AfD" },
  { match: /linke|pds/i, color: "#BE3075", label: "Die Linke" },
  { match: /ssw/i, color: "#005CA9", label: "SSW" },
  { match: /fraktionslos|unbekannt|los/i, color: "#9A9486", label: "fraktionslos" },
];

export function partyColor(fraktion) {
  const hit = PARTY_COLORS.find((p) => p.match.test(fraktion || ""));
  return hit ? hit.color : "#5B6678";
}

// Yellow needs dark text for contrast; everything else gets light text.
export function textOn(color) {
  return color === "#FFD600" ? "#1A1A1A" : "#FBF9F5";
}

export async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore parse error, keep status */
    }
    throw new Error(detail);
  }
  return res.json();
}
