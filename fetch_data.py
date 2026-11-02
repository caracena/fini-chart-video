"""
fetch_data.py — Download prices from Yahoo Finance and build data.js for chart.html

Simulates "if you had invested $1,000 in <start> in A vs B vs C..." :
every asset is normalized so that it starts at --amount on the first common date.

Examples
--------
  # S&P 500 vs Gold since 2000 (weekly)
  python fetch_data.py ^GSPC GC=F --start 2000-01-01

  # Three assets, custom names, monthly data, $1,000,000 CLP
  python fetch_data.py ^GSPC BTC-USD GLD --names "S&P 500" Bitcoin Oro --start 2015-01-01 --interval 1mo

  # No internet? generate fake data to test the pipeline
  python fetch_data.py ^GSPC GC=F --demo

Tickers are Yahoo Finance symbols (search them at finance.yahoo.com):
  ^GSPC S&P 500 | ^IXIC Nasdaq | ^DJI Dow Jones | GC=F Gold futures | GLD Gold ETF
  BTC-USD Bitcoin | ETH-USD Ethereum | AAPL Apple | NVDA Nvidia | ^IPSA IPSA Chile
  CLP=X USD/CLP | SI=F Silver | VOO / SPY S&P 500 ETFs
"""
import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

KNOWN = {
    "^GSPC": ("S&P 500", "S&P\n500"),
    "^IXIC": ("Nasdaq", "NAS\nDAQ"),
    "^NDX": ("Nasdaq 100", "NDX\n100"),
    "^DJI": ("Dow Jones", "DOW"),
    "^IPSA": ("IPSA", "IPSA"),
    "GC=F": ("Oro", "ORO"),
    "GLD": ("Oro", "ORO"),
    "SI=F": ("Plata", "PLATA"),
    "BTC-USD": ("Bitcoin", "₿"),
    "ETH-USD": ("Ethereum", "Ξ"),
    "SPY": ("S&P 500", "SPY"),
    "VOO": ("S&P 500", "VOO"),
    "QQQ": ("Nasdaq 100", "QQQ"),
    "AAPL": ("Apple", "AAPL"),
    "MSFT": ("Microsoft", "MSFT"),
    "NVDA": ("Nvidia", "NVDA"),
    "TSLA": ("Tesla", "TSLA"),
    "AMZN": ("Amazon", "AMZN"),
    "GOOGL": ("Google", "GOOG"),
    "CLP=X": ("Dólar (CLP)", "USD"),
}
# Fini-friendly palette: S&P red, gold, then distinct hues
PALETTE = ["#A8102C", "#F2B200", "#1F6FEB", "#17A673", "#7B3FE4", "#F06A00", "#0AA5C0", "#E0458B"]
GOLD_TICKERS = {"GC=F", "GLD", "IAU"}
# Friendly aliases (also fixes Windows cmd/.bat eating the "^" of index symbols)
ALIASES = {
    "SP500": "^GSPC", "S&P500": "^GSPC", "SPX": "^GSPC", "GSPC": "^GSPC",
    "NASDAQ": "^IXIC", "IXIC": "^IXIC", "NDX": "^NDX", "NASDAQ100": "^NDX",
    "DOW": "^DJI", "DJI": "^DJI", "DOWJONES": "^DJI", "IPSA": "^IPSA",
    "ORO": "GC=F", "GOLD": "GC=F", "PLATA": "SI=F", "SILVER": "SI=F",
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD", "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "DOLAR": "CLP=X", "USDCLP": "CLP=X",
}


def normalize(ticker):
    t = ticker.strip()
    return ALIASES.get(t.upper(), t)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tickers", nargs="+", help="Yahoo Finance symbols, e.g. ^GSPC GC=F BTC-USD")
    p.add_argument("--names", nargs="+", help="Display names (same order as tickers)")
    p.add_argument("--short", nargs="+", help="Short text for the icon badge (use \\n for line break)")
    p.add_argument("--colors", nargs="+", help="Hex colors (same order as tickers)")
    p.add_argument("--start", default="2000-01-01", help="Start date YYYY-MM-DD (default 2000-01-01)")
    p.add_argument("--end", default=None, help="End date YYYY-MM-DD (default: today)")
    p.add_argument("--interval", default="1wk", choices=["1d", "1wk", "1mo"],
                   help="Data granularity. 1wk recommended for 10+ years (default 1wk)")
    p.add_argument("--amount", type=float, default=1000, help="Initial investment per asset (default 1000)")
    p.add_argument("--currency", default="$", help="Currency symbol shown in the chart (default $)")
    p.add_argument("--raw-prices", action="store_true",
                   help="Plot raw prices instead of the value of the initial investment")
    p.add_argument("--out", default="data.js", help="Output file (default data.js, next to chart.html)")
    p.add_argument("--csv", default=None, help="Also save the aligned table as CSV")
    p.add_argument("--demo", action="store_true", help="Generate synthetic data (offline test)")
    return p.parse_args()


def download(ticker, start, end, interval):
    """Return a pd.Series of adjusted closes indexed by date."""
    try:
        import yfinance as yf
    except ImportError:
        sys.exit("Missing package: run  pip install -r requirements.txt")
    df = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=True)
    if (df is None or df.empty) and not ticker.startswith("^"):
        print(f"  no data for '{ticker}', trying '^{ticker}' ...")
        df = yf.Ticker("^" + ticker).history(start=start, end=end, interval=interval, auto_adjust=True)
        ticker = "^" + ticker
    if df is None or df.empty:
        sys.exit(f"\nNo data for '{ticker}'. Check the symbol on finance.yahoo.com "
                 f"(or use an alias like SP500, NASDAQ, ORO, BTC).")
    s = df["Close"].dropna()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    s.name = ticker
    return s


def resolve_and_download(tickers, start, end, interval):
    """Download all; if a symbol only worked with a '^' prefix, update the ticker list."""
    out = []
    for i, t in enumerate(tickers):
        print(f"Downloading {t} ...", flush=True)
        s = download(t, start, end, interval)
        tickers[i] = s.name
        print(f"  {len(s)} rows  {s.index[0].date()} -> {s.index[-1].date()}")
        out.append(s)
    return out


def demo_series(ticker, start, end, interval, seed):
    import random
    rnd = random.Random(seed)
    freq = {"1d": "B", "1wk": "W-FRI", "1mo": "ME"}[interval]
    idx = pd.date_range(start, end or datetime.today(), freq=freq)
    steps_per_year = {"1d": 252, "1wk": 52, "1mo": 12}[interval]
    mu, vol = [(0.09, 0.17), (0.07, 0.15), (0.25, 0.6), (0.11, 0.25)][seed % 4]
    v, out = 100.0, []
    for i, d in enumerate(idx):
        shock = 0
        # crashes so event pop-ups have something to show
        if seed % 4 == 0 and d.year in (2001, 2008) and d.month in (3, 9, 10):
            shock = -0.04
        if seed % 4 == 0 and d.year == 2020 and d.month == 3:
            shock = -0.07
        v *= math.exp(mu / steps_per_year + vol / math.sqrt(steps_per_year) * rnd.gauss(0, 1) + shock)
        out.append(v)
    return pd.Series(out, index=idx, name=ticker)


def align(series_list, interval):
    df = pd.concat(series_list, axis=1).sort_index()
    rule = {"1d": "D", "1wk": "W-FRI", "1mo": "ME"}[interval]
    if interval != "1d":
        df = df.resample(rule).last()
    df = df.ffill()
    df = df.dropna(how="any")  # start when ALL assets have data
    if interval == "1d":
        df = df[df.index.dayofweek < 5]
    return df


def main():
    a = parse_args()
    a.tickers = [normalize(t) for t in a.tickers]

    if a.demo:
        series = [demo_series(t, a.start, a.end, a.interval, i) for i, t in enumerate(a.tickers)]
    else:
        series = resolve_and_download(a.tickers, a.start, a.end, a.interval)

    df = align(series, a.interval)
    if df.empty:
        sys.exit("The assets have no overlapping dates. Try a later --start.")
    first_dates = {s.name: s.index[0] for s in series}
    latest_start = max(first_dates, key=first_dates.get)
    if df.index[0] > pd.Timestamp(a.start) + pd.Timedelta(days=40):
        print(f"NOTE: common history starts {df.index[0].date()} (limited by {latest_start}).")

    out_series = []
    for i, t in enumerate(a.tickers):
        name, short = KNOWN.get(t, (t, t[:5]))
        if a.names and i < len(a.names):
            name = a.names[i]
            if not (a.short and i < len(a.short)) and t not in KNOWN:
                short = name[:5].upper()
        if a.short and i < len(a.short):
            short = a.short[i].replace("\\n", "\n")
        if a.colors and i < len(a.colors):
            color = a.colors[i]
        elif t in GOLD_TICKERS:
            color = "#F2B200"
        else:
            non_gold = [c for c in PALETTE if c != "#F2B200"]
            color = non_gold[sum(1 for x in a.tickers[:i] if x not in GOLD_TICKERS) % len(non_gold)]
        prices = df[t].tolist()
        values = prices if a.raw_prices else [p / prices[0] * a.amount for p in prices]
        out_series.append({
            "ticker": t, "name": name, "short": short, "color": color,
            "values": [round(v, 4) for v in values],
            "prices": [round(p, 4) for p in prices],
        })

    data = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "source": "demo" if a.demo else "Yahoo Finance",
        "interval": a.interval,
        "amount": a.amount,
        "currency": a.currency,
        "rawPrices": a.raw_prices,
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "series": out_series,
    }
    out = Path(a.out)
    if not out.is_absolute():
        out = Path(__file__).resolve().parent / out
    out.write_text("// generated by fetch_data.py — do not edit by hand\nwindow.CHART_DATA = "
                   + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    if a.csv:
        df.to_csv(a.csv)

    print(f"\nSaved {out}  ({len(df)} points, {df.index[0].date()} -> {df.index[-1].date()})")
    for s in out_series:
        v0, v1 = s["values"][0], s["values"][-1]
        print(f"  {s['name']:<14} {a.currency}{v0:,.0f} -> {a.currency}{v1:,.0f}  ({(v1 / v0 - 1) * 100:+.0f}%)")
    print("\nNext: open chart.html to preview, then  python record_video.py")


if __name__ == "__main__":
    main()
