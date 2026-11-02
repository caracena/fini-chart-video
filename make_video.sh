#!/usr/bin/env bash
# Mac / Linux version of make_video.bat
# Usage: ./make_video.sh SP500 NVDA --start 2000-01-01
# (all arguments go to fetch_data.py; then the MP4 is recorded and opened)
set -e
cd "$(dirname "$0")"
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
"$PY" fetch_data.py "$@"
"$PY" record_video.py
if command -v open >/dev/null 2>&1; then open fini_chart.mp4; fi
