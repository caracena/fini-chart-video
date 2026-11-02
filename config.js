// ─────────────────────────────────────────────────────────────
//  config.js — edit texts, timing and look of the animation.
//  The price data itself comes from data.js (made by fetch_data.py).
// ─────────────────────────────────────────────────────────────
window.CHART_CONFIG = {
  // Header
  title: "¿Dónde deberías guardar tus ahorros? 👇",
  subtitle: "",                    // e.g. "Si hubieras invertido $1.000 en el año 2000"
  showVsRow: true,                 // the "A vs B vs C" icons row

  // Footer
  sourceText: "fuente: Yahoo Finance",
  brand: "🐷 @Fini.Game",          // "" to hide

  // Numbers & dates
  locale: "es-CL",                 // "en-US" → $1,000  |  "es-CL" → $1.000
  logScale: false,                 // true is better for crypto vs. stocks

  // Timing (seconds)
  intro: 0.6,                      // empty chart before lines start
  duration: 18,                    // time the lines take to draw (without pauses)
  eventPause: 1.4,                 // pause on each crisis pop-up
  endHold: 3,                      // freeze at the end
  fps: 30,

  // Big % under the year:
  //  [0, 1]  → how much asset #1 is above/below asset #2 (like the reference video)
  //  "return" → total return of the first asset
  //  null    → hide
  compare: [0, 1],
  compareCaption: true,            // small "S&P 500 vs Oro" under the %

  // Icons per ticker: "gold" | "silver" | "coin" | an emoji like "🍎" | an image path like "img/apple.png"
  // Tickers not listed get a colored square with their short name.
  icons: {
    "GC=F": "gold", "GLD": "gold", "IAU": "gold",
    "SI=F": "silver",
    "BTC-USD": "coin", "ETH-USD": "coin"
  },

  // Crisis pop-ups. Only shown if inside the data range. The "~X%" fall is computed
  // from the data (peak → bottom) for `asset` (0 = first ticker). Set `drop: 49` to force a number.
  events: [
    { date: "2000-03-24", label: "Burbuja punto com" },
    { date: "2007-10-09", label: "Crisis financiera" },
    { date: "2020-02-19", label: "Crash COVID-19" },
    { date: "2022-01-03", label: "Inflación y alza de tasas" },
    { date: "2025-02-19", label: "Shock arancelario" }
  ],
  eventMinDrop: 10,                // skip pop-ups where the fall is smaller than this %
  dropText: "{asset} cayó ~{pct}%",  // {asset} = name of the asset measured, {pct} = fall

  theme: {
    bg: "#FBFAF6",
    panel: "#F3F2EE",
    text: "#111111",
    axis: "#222222",
    grid: "rgba(0,0,0,0.055)",
    year: "#8C8C8C",
    up: "#1FA34A",
    down: "#D2283A",
    eventLine: "rgba(200,30,55,0.55)",
    popupBg: "rgba(255,241,243,0.97)",
    popupBorder: "#C8102E"
  }
};
