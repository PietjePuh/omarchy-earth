#!/usr/bin/env python3
"""Build the standalone earth map: template + a fresh sample, one HTML file.

Kept separate from the sampler so the page can be rebuilt without touching
the collection logic, and so the template stays readable rather than being
a Python string.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import os

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "web" / "earth.html"
SAMPLER = HERE / "earth-sampler.py"
MARKER = "/*__EARTH_DATA__*/null"


def build(lat: float, lon: float, span: float, out: pathlib.Path) -> int:
    if not TEMPLATE.exists():
        print(f"template missing: {TEMPLATE}", file=sys.stderr)
        return 1

    proc = subprocess.run(
        [sys.executable, str(SAMPLER), "--lat", str(lat), "--lon", str(lon),
         "--span", str(span), "--once"],
        capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not proc.stdout.strip():
        print(f"sampler failed: {proc.stderr[:200]}", file=sys.stderr)
        return 1

    data = proc.stdout.strip().splitlines()[-1]
    # Validate before embedding: a malformed line would produce a page that
    # fails silently in the browser with nothing in any log.
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"sampler emitted invalid JSON: {e}", file=sys.stderr)
        return 1

    html = TEMPLATE.read_text()
    if MARKER not in html:
        print("template marker missing", file=sys.stderr)
        return 1
    # </script> inside embedded JSON would end the script block early.
    safe = data.replace("</", "<\\/")
    html = html.replace(MARKER, safe)

    out.parent.mkdir(parents=True, exist_ok=True)
    # Atomic: a half-written page is worse than an old one.
    fd, tmp = tempfile.mkstemp(dir=str(out.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(html)
    os.replace(tmp, out)

    print(f"{out}  ({len(html):,} bytes)  "
          f"radar={len(parsed.get('radar', {}).get('frames', []))} "
          f"wind={len(parsed.get('wind', {}).get('points', []))} "
          f"planes={parsed.get('aircraft', {}).get('count', 0)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--span", type=float, default=4.0)
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path.home() / ".cache/omarchy-earth/earth.html")
    args = ap.parse_args()
    return build(args.lat, args.lon, args.span, args.out)


if __name__ == "__main__":
    sys.exit(main())
