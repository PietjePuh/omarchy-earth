#!/usr/bin/env python3
"""Live ADS-B poller for the earth map: adsb.lol -> JSONP file + stdout line.

api.adsb.lol sends no CORS headers, so the map page (loaded via file://)
cannot fetch it directly. The bar widget runs this poller instead: it
reuses the sampler's adsb.lol logic and writes a JSONP file next to the
built page that the page CAN load (script tags are not subject to CORS):

    window.__LIVE_ADSB__={"ts":...,"aircraft":{...},"military_aircraft":{...}};

The same payload is printed on stdout as one JSON line so the QML bar
panel can refresh its Vluchten tab every poll without re-running the
full sampler.

A failed fetch never clobbers the last good file: on error the previous
file stays untouched and stdout carries {"ts":..., "error": ...} so the
caller can tell the poll failed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent


def load_sampler():
    """Import earth-sampler.py (dash in filename -> importlib, not import)."""
    spec = importlib.util.spec_from_file_location(
        "earth_sampler", HERE / "earth-sampler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_atomic(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--radius", type=int, default=50)
    ap.add_argument("--interval", type=float, default=30.0)
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path.home() / ".cache/omarchy-earth/live-adsb.js")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    sampler = load_sampler()

    while True:
        payload = {"ts": int(time.time()), "aircraft": {}, "military_aircraft": {}}
        errors = []

        def sample_once():
            """One full poll; returns error list (empty = success).

            Retries once after 5s: adsb.lol rate-limits bursts (e.g. right
            after build-map.py's sampler calls) with 429/timeout.
            """
            for attempt in (1, 2):
                errs = []
                try:
                    payload["aircraft"] = sampler.sample_aircraft(args.lat, args.lon, args.radius)
                    if payload["aircraft"].get("error"):
                        errs.append("aircraft:" + str(payload["aircraft"]["error"]))
                except Exception as e:  # one bad source must never kill the poller
                    errs.append(f"aircraft:{type(e).__name__}")
                    print(f"adsb poll aircraft failed: {e}", file=sys.stderr)
                try:
                    payload["military_aircraft"] = sampler.sample_military_aircraft(args.lat, args.lon)
                    if payload["military_aircraft"].get("error"):
                        errs.append("mil:" + str(payload["military_aircraft"]["error"]))
                except Exception as e:
                    errs.append(f"mil:{type(e).__name__}")
                    print(f"adsb poll military failed: {e}", file=sys.stderr)
                if not errs:
                    return []
                if attempt == 1:
                    time.sleep(5)
            return errs

        errors = sample_once()

        if errors:
            payload["error"] = " ".join(errors)
            # Keep the last good file; stdout tells the caller we are stale.
            sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
            sys.stdout.flush()
            if args.once:
                return 1
            time.sleep(max(10.0, args.interval))
            continue

        # </script> inside the payload would end the page's script tag early.
        body = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
        write_atomic(args.out, "window.__LIVE_ADSB__=" + body + ";\n")
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
        sys.stdout.flush()

        if args.once:
            return 0
        time.sleep(max(10.0, args.interval))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
