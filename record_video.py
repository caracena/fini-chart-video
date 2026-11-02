"""
record_video.py — Render chart.html frame by frame and encode a vertical MP4 (1080x1920, 9:16)

Every frame is drawn at an exact timestamp, so the video is perfectly smooth no
matter how fast or slow your PC is (it is NOT a screen recording).

Examples
--------
  python record_video.py                                   # -> fini_chart.mp4 (1080x1920, 30 fps)
  python record_video.py --out sp500_vs_oro.mp4 --fps 60
  python record_video.py --audio musica.mp3                # add music (fades out at the end)
  python record_video.py --res 720                         # 720x1280 (smaller file)
  python record_video.py --snapshots 3 8 15                # just save PNGs at those seconds (quick check)

First time only:
  pip install -r requirements.txt
  python -m playwright install chromium
"""
import argparse
import base64
import functools
import http.server
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found. Run  pip install imageio-ffmpeg  (or install ffmpeg and add it to PATH).")


def serve(directory):
    """Serve the folder on localhost so fonts/images load without file:// restrictions."""
    handler = functools.partial(QuietHandler, directory=str(directory))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--page", default="chart.html", help="HTML page to record (default chart.html)")
    p.add_argument("--out", default="fini_chart.mp4", help="Output video file")
    p.add_argument("--fps", type=int, default=None, help="Frames per second (default: config.js fps, 30)")
    p.add_argument("--res", type=int, default=1080, choices=[720, 1080, 1440, 2160],
                   help="Output width; height is 16/9 of it (default 1080 -> 1080x1920)")
    p.add_argument("--audio", default=None, help="Optional music/voice file to add (mp3, wav, m4a...)")
    p.add_argument("--audio-start", type=float, default=0, help="Start the audio at this second of the file")
    p.add_argument("--crf", type=int, default=18, help="Quality (lower = better/bigger). Default 18")
    p.add_argument("--best", action="store_true", help="Slower, slightly smaller/better encode")
    p.add_argument("--snapshots", nargs="*", type=float, help="Only save PNG frames at these seconds")
    a = p.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Missing playwright: pip install -r requirements.txt && python -m playwright install chromium")

    page_path = (HERE / a.page).resolve()
    if not page_path.exists():
        sys.exit(f"Not found: {page_path}")
    if not (page_path.parent / "data.js").exists():
        sys.exit("data.js not found — run fetch_data.py first.")

    httpd, port = serve(page_path.parent)
    url = f"http://127.0.0.1:{port}/{page_path.name}?record=1"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_function("window.CHART !== undefined", timeout=15000)
        page.evaluate("() => window.CHART.ready")
        if errors:
            sys.exit("Error in chart.html: " + errors[0])

        info = page.evaluate("() => ({total: CHART.total, fps: CHART.fps, events: CHART.events.length})")
        fps = a.fps or int(info["fps"] or 30)
        total = float(info["total"])
        grab = """(t) => { CHART.render(t); return document.getElementById('c').toDataURL('image/png'); }"""

        if a.snapshots is not None:
            times = a.snapshots or [total * f for f in (0.15, 0.4, 0.7, 1.0)]
            for t in times:
                png = base64.b64decode(page.evaluate(grab, t).split(",", 1)[1])
                out = HERE / f"snapshot_{t:05.1f}s.png"
                out.write_bytes(png)
                print("saved", out.name)
            browser.close()
            httpd.shutdown()
            return

        n_frames = int(round(total * fps)) + 1
        w, h = a.res, a.res * 16 // 9
        out = Path(a.out)
        if not out.is_absolute():
            out = HERE / out
        cmd = [find_ffmpeg(), "-y", "-loglevel", "error",
               "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-"]
        if a.audio:
            cmd += ["-ss", str(a.audio_start), "-i", a.audio]
        vf = [] if w == 1080 else [f"scale={w}:{h}:flags=lanczos"]
        if vf:
            cmd += ["-vf", ",".join(vf)]
        cmd += ["-c:v", "libx264", "-preset", "slow" if a.best else "veryfast", "-crf", str(a.crf),
                "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(fps), "-movflags", "+faststart"]
        if a.audio:
            fade_start = max(0.0, total - 1.5)
            cmd += ["-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={fade_start:.2f}:d=1.5",
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}"]
        cmd += [str(out)]

        print(f"Recording {n_frames} frames ({total:.1f}s @ {fps}fps, {w}x{h}, {info['events']} pop-ups) ...")
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t0 = time.time()
        try:
            for f in range(n_frames):
                data = page.evaluate(grab, f / fps)
                ff.stdin.write(base64.b64decode(data.split(",", 1)[1]))
                if f % fps == 0 or f == n_frames - 1:
                    done = (f + 1) / n_frames
                    eta = (time.time() - t0) / done * (1 - done)
                    print(f"\r  {done * 100:5.1f}%  frame {f + 1}/{n_frames}  ETA {eta:4.0f}s", end="", flush=True)
        finally:
            ff.stdin.close()
            code = ff.wait()
            browser.close()
            httpd.shutdown()
        print()
        if code != 0:
            sys.exit("ffmpeg failed (exit code %d)" % code)
        print(f"Done: {out}  ({out.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
