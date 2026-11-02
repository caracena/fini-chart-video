# Fini Chart Video — "If you had invested $1,000 in…" shorts

Recreates the format of the reference short (S&P 500 vs Gold): growth-of-$1,000 lines
drawing over time, axes that rescale, a big year counter, the "+84%" advantage badge,
end-of-line labels, and crisis pop-ups with dashed markers. Output: **1080×1920 MP4 (9:16)**
ready for Reels / TikTok / Shorts.

```
fetch_data.py   → downloads prices from Yahoo Finance → data.js
chart.html      → animated chart (open it in a browser to preview)
config.js       → texts, timing, crisis events, colors, icons
record_video.py → renders chart.html frame by frame → MP4
```

## 1. Install (once)

```bash
pip install -r requirements.txt
python -m playwright install chromium
```
(ffmpeg comes bundled through `imageio-ffmpeg`, no separate install needed.)

## 2. Get the data

```bash
python fetch_data.py "^GSPC" "GC=F" --start 2000-01-01
python fetch_data.py "^GSPC" "BTC-USD" "GLD" --start 2015-01-01 --names "S&P 500" Bitcoin Oro
python fetch_data.py "AAPL" "MSFT" "NVDA" --start 2010-01-01 --amount 1000000 --interval 1mo
```
> **Windows tip:** cmd / `.bat` files eat the `^` of index symbols. Easiest is to use the
> aliases, which need no `^`: `SP500`, `NASDAQ`, `NASDAQ100`, `DOW`, `IPSA`, `ORO`/`GOLD`,
> `PLATA`, `BTC`, `ETH`, `DOLAR`. A symbol that arrives without its `^` (e.g. `GSPC`) is also
> retried automatically as `^GSPC`.

Options: `--start --end --interval 1d|1wk|1mo --amount --currency --names --short --colors --raw-prices --csv`.
Assets are aligned on common dates, so the chart starts when **all** of them have data
(e.g. Yahoo's `GC=F` gold futures begin in Aug 2000, `GLD` in Nov 2004, `BTC-USD` in Sep 2014).
`--demo` creates fake data for testing without internet; the footer then reads "DATOS DE PRUEBA".

Useful symbols: `^GSPC` S&P 500 · `^IXIC` Nasdaq · `^DJI` Dow · `^IPSA` IPSA Chile ·
`GC=F`/`GLD` gold · `SI=F` silver · `BTC-USD` · `ETH-USD` · `CLP=X` USD/CLP · any stock (`AAPL`, `NVDA`…).

## 3. Preview & tweak

Open `chart.html` (double-click). Space = pause, R = restart, slider = scrub.
Edit `config.js` to change title, subtitle, brand, durations, crisis events, colors, icons
(`"gold"`, `"silver"`, `"coin"`, an emoji, or an image path like `"img/logo.png"`), log scale, etc.
Crisis falls (`~49%`) are computed from the data automatically; events smaller than `eventMinDrop` are skipped.

## 4. Record the video

```bash
python record_video.py                          # → fini_chart.mp4, 1080x1920 @30fps
python record_video.py --out sp_vs_oro.mp4 --audio musica.mp3 --fps 60
python record_video.py --res 720                # 720x1280, smaller file
python record_video.py --snapshots 3 10 20      # only PNG stills, for a quick check
```
Frame-exact: each frame is rendered at a precise timestamp, so the video is smooth regardless
of PC speed (~30 s to render a 25 s clip).

Shortcut on Windows: `.\make_video.bat SP500 ORO --start 2000-01-01`
Shortcut on Mac/Linux: `./make_video.sh SP500 ORO --start 2000-01-01`
(first time: `chmod +x make_video.sh`; on Mac use `python3` / `pip3` in all commands above)

Alternative without Python: the **⏺ Grabar** button in `chart.html` records in real time
in the browser (Chrome saves MP4, others WebM). Use the Python recorder for the final export.
