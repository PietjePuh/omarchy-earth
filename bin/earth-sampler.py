#!/usr/bin/env python3
"""Unified Earth & World Monitor sampler: official sources, zero API keys.

Collects and emits one comprehensive JSON object per line on stdout:
  - Weather forecast & current conditions (Open-Meteo)
  - Rain nowcast 2h series at 5-minute resolution (Buienradar)
  - Practical activity verdicts (Korte broek, BBQ, was buiten, fietsen, ramen...)
  - Solar elevation arc & daylight phase (NOAA algorithm)
  - Civil aircraft overhead with range & bearing (adsb.lol)
  - Live military flights worldwide & nearby (adsb.lol /v2/mil)
  - Strategic maritime chokepoints & canals (Hormuz, Bab-el-Mandeb, Suez, etc.)
  - Global nuclear facilities & power stations (IAEA PRIS / strategic sites)
  - Strategic overseas military bases (Ramstein, Al Udeid, Diego Garcia, etc.)
  - Geopolitical conflict hotspots & flashpoints (Ukraine, Gaza, Red Sea, etc.)
  - METAR airfields with FAA flight categories (aviationweather.gov)
  - Global rain radar timeline frames (RainViewer)
  - Wind field grid 36 points worldwide (Open-Meteo)
  - Air quality & ammonia & pollen index (Open-Meteo)
  - Significant earthquakes past 24h (USGS)
  - Orange and Red disaster alerts worldwide (GDACS)
  - NASA GIBS MODIS true color date
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import html
import json
import math
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

UA = "omarchy-earth/2.0 (unified bar widget; contact: local user)"
HTTP_TIMEOUT = 18

RAINVIEWER_INDEX = "https://api.rainviewer.com/public/weather-maps.json"
OPENMETEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
AIRQUALITY = "https://air-quality-api.open-meteo.com/v1/air-quality"
ADSB = "https://api.adsb.lol/v2/point/{lat}/{lon}/{radius}"
ADSB_MIL = "https://api.adsb.lol/v2/mil"
METAR = "https://aviationweather.gov/api/data/metar?bbox={s},{w},{n},{e}&format=json"
USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
GDACS = ("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
         "?alertlevel=Orange;Red")
NOWCAST_URL = "https://gpsgadget.buienradar.nl/data/raintext?lat={lat}&lon={lon}"
RADIOBROWSER = "https://de1.api.radio-browser.info/json/stations/search"
GLOBAL_RADIO_CACHE = DATA_DIR / "global-radio-cache.json"
GLOBAL_RADIO_CACHE_TTL = 6 * 3600  # station lists barely change hour to hour;
# ~20 sequential country queries would otherwise add real latency to every
# single sampler run, so this is the one network fetch in this file that's
# disk-cached rather than re-fetched live every time (all others rely on
# ThreadPoolExecutor concurrency + short per-fetch timeouts to stay fast).

DRY_THRESHOLD = 0.05  # mm/h

FLTCAT_COLOUR = {
    "VFR": "#5cb85c",     # green
    "MVFR": "#5bc0de",    # blue
    "IFR": "#d9534f",     # red
    "LIFR": "#d17ad1",    # magenta
}

OPERATORS = {
    "KLM": "KLM Royal Dutch Airlines", "TRA": "Transavia", "EJU": "easyJet Europe", "EZY": "easyJet",
    "RYR": "Ryanair", "TOM": "TUI Airways", "TFL": "TUI fly Netherlands", "EXS": "Jet2",
    "DLH": "Lufthansa", "BAW": "British Airways", "AFR": "Air France",
    "UAE": "Emirates", "QTR": "Qatar Airways", "SWR": "Swiss", "AUA": "Austrian Airlines",
    "WZZ": "Wizz Air", "VLG": "Vueling", "CND": "Corendon Dutch", "CAI": "Corendon",
    "UPS": "UPS Airlines", "FDX": "FedEx Express", "DHK": "DHL Air", "BCS": "European Air Transport",
    "DAL": "Delta Air Lines", "UAL": "United Airlines", "AAL": "American Airlines",
    "THY": "Turkish Airlines", "SAS": "Scandinavian Airlines", "FIN": "Finnair",
    "IBE": "Iberia", "TAP": "TAP Air Portugal", "BEL": "Brussels Airlines",
    "SIA": "Singapore Airlines", "CPA": "Cathay Pacific", "QFA": "Qantas",
    "ETD": "Etihad Airways", "NAF": "Koninklijke Luchtmacht", "RFR": "Royal Air Force",
    "GAF": "German Air Force", "FAF": "French Air Force", "IAM": "Italian Air Force",
}

AIRCRAFT_TYPES = {
    "B738": "Boeing 737-800", "B737": "Boeing 737-700", "B739": "Boeing 737-900ER", "B38M": "Boeing 737 MAX 8", "B39M": "Boeing 737 MAX 9",
    "B77W": "Boeing 777-300ER", "B772": "Boeing 777-200ER", "B77L": "Boeing 777-200LR", "B789": "Boeing 787-9 Dreamliner",
    "B788": "Boeing 787-8 Dreamliner", "B78X": "Boeing 787-10 Dreamliner", "B744": "Boeing 747-400", "B748": "Boeing 747-8",
    "B763": "Boeing 767-300ER", "B752": "Boeing 757-200",
    "A320": "Airbus A320", "A20N": "Airbus A320neo", "A321": "Airbus A321", "A21N": "Airbus A321neo",
    "A319": "Airbus A319", "A332": "Airbus A330-200", "A333": "Airbus A330-300", "A339": "Airbus A330-900neo",
    "A359": "Airbus A350-900", "A35K": "Airbus A350-1000", "A388": "Airbus A380-800",
    "E190": "Embraer E190", "E195": "Embraer E195", "E295": "Embraer E195-E2", "E75L": "Embraer E175",
    "CRJ9": "Bombardier CRJ-900", "BCS3": "Airbus A220-300", "BCS1": "Airbus A220-100",
    "AT76": "ATR 72-600", "DH8D": "De Havilland Dash 8-400",
    "H60": "Sikorsky UH-60 Black Hawk", "AH64": "Boeing AH-64 Apache", "CH47": "Boeing CH-47 Chinook",
    "C30J": "Lockheed C-130J Super Hercules", "C130": "Lockheed C-130 Hercules", "C17": "Boeing C-17 Globemaster III",
    "A400": "Airbus A400M Atlas", "F35": "Lockheed Martin F-35 Lightning II", "F16": "General Dynamics F-16 Falcon",
    "EF20": "Eurofighter Typhoon", "EUFI": "Eurofighter Typhoon", "R135": "Boeing RC-135 Rivet Joint",
    "E3TF": "Boeing E-3 Sentry (AWACS)", "P8": "Boeing P-8 Poseidon", "KC46": "Boeing KC-46 Pegasus",
    "K35R": "Boeing KC-135 Stratotanker", "NH90": "NHIndustries NH90",
}


WEATHER_CODES = {
    0: "Helder", 1: "Overwegend helder", 2: "Licht bewolkt", 3: "Bewolkt",
    45: "Mist", 48: "Rijpmist", 51: "Lichte motregen", 53: "Motregen",
    55: "Dichte motregen", 61: "Lichte regen", 63: "Regen", 65: "Zware regen",
    71: "Lichte sneeuw", 73: "Sneeuw", 75: "Zware sneeuw", 77: "Sneeuwkorrels",
    80: "Lichte buien", 81: "Buien", 82: "Hevige buien", 85: "Sneeuwbuien",
    86: "Zware sneeuwbuien", 95: "Onweer", 96: "Onweer met hagel", 99: "Zwaar onweer"
}


def fetch_json(url: str, timeout: int = HTTP_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def fetch_text(url: str, timeout: int = HTTP_TIMEOUT) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(h))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def compass(b: float) -> str:
    names = ["N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO",
             "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW"]
    return names[int((b + 11.25) % 360 / 22.5)]


def mm_per_hour(raw: int) -> float:
    if raw <= 0:
        return 0.0
    return 10 ** ((raw - 109) / 32) * 0.1


def solar_elevation(ts: float, lat: float, lon: float) -> float:
    jd = ts / 86400.0 + 2440587.5
    n = jd - 2451545.0
    mean_long = (280.460 + 0.9856474 * n) % 360
    anomaly = math.radians((357.528 + 0.9856003 * n) % 360)
    ecliptic = mean_long + 1.915 * math.sin(anomaly) + 0.020 * math.sin(2 * anomaly)
    ecliptic_rad = math.radians(ecliptic)
    obliquity = math.radians(23.439 - 0.0000004 * n)
    sin_dec = math.sin(obliquity) * math.sin(ecliptic_rad)
    cos_dec = math.cos(math.asin(sin_dec))
    ra = math.degrees(math.atan2(math.cos(obliquity) * math.sin(ecliptic_rad), math.cos(ecliptic_rad)))
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    hour_angle = math.radians((gmst + lon - ra + 360) % 360)
    lat_rad = math.radians(lat)
    sin_elev = math.sin(lat_rad) * sin_dec + math.cos(lat_rad) * cos_dec * math.cos(hour_angle)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))


def solar_status(lat: float, lon: float, points: int = 24) -> dict:
    now = time.time()
    midnight = now - (now % 86400) + time.timezone
    if midnight > now:
        midnight -= 86400
    step = 86400 / points
    arc = []
    for i in range(points + 1):
        ts = midnight + i * step
        elev = solar_elevation(ts, lat, lon)
        arc.append({
            "time": time.strftime("%H:%M", time.localtime(ts)),
            "elev": round(elev, 1),
        })

    rise = set_ = None
    prev = solar_elevation(midnight, lat, lon)
    for m in range(1, 24 * 60):
        ts = midnight + m * 60
        elev = solar_elevation(ts, lat, lon)
        if prev < -0.833 <= elev and rise is None:
            rise = time.strftime("%H:%M", time.localtime(ts))
        if prev > -0.833 >= elev and rise is not None and set_ is None:
            set_ = time.strftime("%H:%M", time.localtime(ts))
        prev = elev

    current = solar_elevation(now, lat, lon)
    if current > -0.833:
        phase = "dag"
    elif current > -6:
        phase = "schemering"
    else:
        phase = "nacht"

    return {
        "arc": arc,
        "now_elev": round(current, 1),
        "now_index": int((now - midnight) / step) if step else 0,
        "phase": phase,
        "rise": rise or "--:--",
        "set": set_ or "--:--",
        "max_elev": round(max(p["elev"] for p in arc), 1) if arc else 0.0,
    }


def sample_nowcast(lat: float, lon: float) -> dict:
    out = {
        "series": [], "raining_now": False, "starts_at": None,
        "stops_at": None, "peak_mm": 0.0, "peak_at": "",
        "total_mm": 0.0, "summary": "geen data", "error": ""
    }
    try:
        txt = fetch_text(NOWCAST_URL.format(lat=lat, lon=lon), timeout=10)
    except Exception as e:
        out["error"] = type(e).__name__
        out["summary"] = "radar niet bereikbaar"
        return out

    lines = [ln.strip() for ln in txt.strip().splitlines() if ln.strip()]
    series = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != 2:
            continue
        try:
            val = int(parts[0])
            t = parts[1].strip()
            mm = mm_per_hour(val)
            series.append({"time": t, "mm": round(mm, 2), "raw": val})
        except ValueError:
            continue

    if not series:
        out["summary"] = "lege meting"
        return out

    out["series"] = series
    now_wet = series[0]["mm"] >= DRY_THRESHOLD
    wet = [p for p in series if p["mm"] >= DRY_THRESHOLD]
    stops_at = None
    if now_wet:
        for p in series:
            if p["mm"] < DRY_THRESHOLD:
                stops_at = p["time"]
                break

    peak = max(series, key=lambda p: p["mm"])
    total = sum(p["mm"] for p in series) * (5.0 / 60.0)

    if not wet:
        summary = "komende 2 uur droog"
    elif now_wet:
        dur = f"tot ~{stops_at}" if stops_at else "komende 2 uur"
        summary = f"regen {dur} (piek {peak['mm']:.1f} mm/u)"
    else:
        summary = f"regen om {wet[0]['time']} (piek {peak['mm']:.1f} mm/u)"

    out["raining_now"] = bool(now_wet)
    out["starts_at"] = None if now_wet else (wet[0]["time"] if wet else None)
    out["stops_at"] = stops_at
    out["peak_mm"] = round(peak["mm"], 2)
    out["peak_at"] = peak["time"]
    out["total_mm"] = round(total, 2)
    out["summary"] = summary
    return out


def sample_weather(lat: float, lon: float) -> dict:
    url = (
        f"{OPENMETEO_FORECAST}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
        "weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index,"
        "surface_pressure,dew_point_2m,visibility"
        "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,cloud_cover,uv_index,sunshine_duration,wind_speed_10m,wind_direction_10m"
        "&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,sunshine_duration"
        "&wind_speed_unit=kmh&timezone=auto&past_days=7&forecast_days=8"
    )
    out = {"current": {}, "hourly": [], "daily": [], "timeline_hourly": [], "error": ""}
    try:
        d = fetch_json(url, timeout=15)
    except Exception as e:
        out["error"] = type(e).__name__
        return out

    c = d.get("current") or {}
    code = c.get("weather_code", 0)
    w_speed = c.get("wind_speed_10m") or 0.0
    bft = 0
    limits = [1, 5, 11, 19, 28, 38, 49, 61, 74, 88, 102, 117]
    for i, lim in enumerate(limits):
        if w_speed >= lim:
            bft = i + 1

    out["current"] = {
        "temp": c.get("temperature_2m"),
        "feels_like": c.get("apparent_temperature"),
        "humidity": c.get("relative_humidity_2m"),
        "cloud_cover": c.get("cloud_cover"),
        "uv_index": c.get("uv_index"),
        "wind_speed_kmh": round(w_speed, 1),
        "wind_gusts_kmh": round(c.get("wind_gusts_10m") or 0.0, 1),
        "wind_direction": c.get("wind_direction_10m"),
        "wind_bft": bft,
        "pressure_hpa": round(c["surface_pressure"], 1) if c.get("surface_pressure") is not None else None,
        "dew_point": round(c["dew_point_2m"], 1) if c.get("dew_point_2m") is not None else None,
        "visibility_km": round(c["visibility"] / 1000.0, 1) if c.get("visibility") is not None else None,
        "weather_code": code,
        "description": WEATHER_CODES.get(code, "Onbekend"),
    }

    hourly = d.get("hourly") or {}
    h_times = hourly.get("time") or []
    now_str = time.strftime("%Y-%m-%dT%H:00")
    start = next((i for i, t in enumerate(h_times) if t >= now_str), 0)
    for i in range(start, min(start + 12, len(h_times))):
        out["hourly"].append({
            "time": h_times[i][11:16],
            "temp": (hourly.get("temperature_2m") or [])[i] if i < len(hourly.get("temperature_2m") or []) else None,
            "pop": (hourly.get("precipitation_probability") or [])[i] if i < len(hourly.get("precipitation_probability") or []) else None,
            "cloud": (hourly.get("cloud_cover") or [])[i] if i < len(hourly.get("cloud_cover") or []) else None,
            "uv": (hourly.get("uv_index") or [])[i] if i < len(hourly.get("uv_index") or []) else None,
            "sun_min": round(((hourly.get("sunshine_duration") or [])[i] or 0) / 60) if i < len(hourly.get("sunshine_duration") or []) else 0,
        })

    # Comprehensive past 7 days to next 8 days hourly scrubber array
    t_temps = hourly.get("temperature_2m") or []
    t_pops = hourly.get("precipitation_probability") or []
    t_precips = hourly.get("precipitation") or []
    t_codes = hourly.get("weather_code") or []
    t_winds = hourly.get("wind_speed_10m") or []
    t_dirs = hourly.get("wind_direction_10m") or []

    for i, t in enumerate(h_times):
        out["timeline_hourly"].append({
            "t": t,
            "c": t_codes[i] if i < len(t_codes) else 0,
            "tmp": t_temps[i] if i < len(t_temps) else None,
            "prc": round(t_precips[i], 2) if i < len(t_precips) and t_precips[i] is not None else 0.0,
            "pop": t_pops[i] if i < len(t_pops) else 0,
            "wnd": round(t_winds[i], 1) if i < len(t_winds) and t_winds[i] is not None else 0.0,
            "dir": t_dirs[i] if i < len(t_dirs) else 0,
        })

    daily = d.get("daily") or {}
    d_times = daily.get("time") or []
    for i, t in enumerate(d_times):
        out["daily"].append({
            "date": t,
            "temp_max": (daily.get("temperature_2m_max") or [])[i] if i < len(daily.get("temperature_2m_max") or []) else None,
            "temp_min": (daily.get("temperature_2m_min") or [])[i] if i < len(daily.get("temperature_2m_min") or []) else None,
            "sunrise": (daily.get("sunrise") or [""])[i][11:16] if i < len(daily.get("sunrise") or []) else "",
            "sunset": (daily.get("sunset") or [""])[i][11:16] if i < len(daily.get("sunset") or []) else "",
            "uv_max": (daily.get("uv_index_max") or [])[i] if i < len(daily.get("uv_index_max") or []) else None,
            "sun_hours": round(((daily.get("sunshine_duration") or [])[i] or 0) / 3600, 1) if i < len(daily.get("sunshine_duration") or []) else None,
        })

    return out


def evaluate_advice(weather: dict, nowcast: dict, solar: dict) -> list[dict]:
    out: list[dict] = []
    cw = weather.get("current") or {}
    temp = cw.get("temp")
    feels = cw.get("feels_like") if cw.get("feels_like") is not None else temp
    bft = cw.get("wind_bft")
    humidity = cw.get("humidity")
    uv = cw.get("uv_index") or 0.0

    series = nowcast.get("series") or []
    soon = [p["mm"] for p in series[:12]]
    later = [p["mm"] for p in series[12:]]
    rain_soon = max(soon) if soon else 0.0
    rain_later = max(later) if later else 0.0
    dry_window = rain_soon < DRY_THRESHOLD and rain_later < DRY_THRESHOLD

    hourly = weather.get("hourly") or []
    next_6h = hourly[:6]
    sun_minutes = sum((h.get("sun_min") or 0) for h in next_6h) if next_6h else 0
    avg_cloud = (sum((h.get("cloud") or 0) for h in next_6h) / len(next_6h)) if next_6h else None
    max_uv = max(((h.get("uv") or 0) for h in next_6h), default=uv)

    is_day = (solar.get("now_elev") or -90) > -0.833

    def add(key, label, ok, reason, caution=False):
        out.append({
            "key": key,
            "label": label,
            "verdict": "caution" if caution else ("yes" if ok else "no"),
            "reason": reason
        })

    # Korte broek
    if feels is not None:
        if feels >= 20:
            add("shorts", "Korte broek", True, f"voelt als {feels:.0f}°C")
        elif feels >= 16:
            add("shorts", "Korte broek", True, f"voelt als {feels:.0f}°C, met een trui", caution=True)
        else:
            add("shorts", "Korte broek", False, f"voelt als {feels:.0f}°C, te fris")

    # Barbecue
    if temp is not None:
        reasons = []
        ok = True
        soft = False
        if not dry_window:
            ok = False
            when = "binnen een uur" if rain_soon >= DRY_THRESHOLD else "over ruim een uur"
            reasons.append(f"regen {when}")
        if bft is not None and bft >= 5:
            ok = False
            reasons.append(f"wind {bft} Bft")
        elif bft is not None and bft == 4:
            soft = True
            reasons.append(f"wind {bft} Bft, zet uit de wind")
        if temp < 5:
            ok = False
            reasons.append(f"{temp:.0f}°C is te koud")
        elif temp < 12:
            soft = True
            reasons.append(f"{temp:.0f}°C is fris, jas aan")
        if ok and not reasons:
            reasons.append(f"droog, {temp:.0f}°C, wind {bft if bft is not None else '?'} Bft")
        add("bbq", "Barbecue", ok, ", ".join(reasons), caution=ok and soft)

    # Was buiten
    if humidity is not None:
        dry_air = humidity < 80
        windy = bft is not None and bft >= 6
        ok = dry_window and (dry_air or sun_minutes > 60) and not windy
        if not dry_window:
            reason = "er komt regen binnen twee uur"
        elif windy:
            reason = f"{bft} Bft, de was waait van de lijn"
        elif not dry_air and sun_minutes <= 60:
            reason = f"{humidity:.0f}% vocht en weinig zon"
        else:
            reason = f"droog, {humidity:.0f}% vocht, {sun_minutes}m zon"
        add("laundry", "Was buiten", ok, reason)

    # Fietsen
    if temp is not None:
        ok = dry_window
        bits = []
        if not dry_window:
            bits.append("regen op komst")
        if bft is not None and bft >= 6:
            ok = False
            bits.append(f"{bft} Bft tegenwind")
        elif bft is not None and bft >= 4:
            bits.append(f"{bft} Bft")
        if not bits:
            bits.append(f"droog, {temp:.0f}°C")
        add("cycling", "Fietsen", ok, ", ".join(bits))

    # Zonnebrand
    if is_day and max_uv:
        if max_uv >= 6:
            add("sunscreen", "Zonnebrand", True, f"UV {max_uv:.0f}, insmeren")
        elif max_uv >= 3:
            add("sunscreen", "Zonnebrand", True, f"UV {max_uv:.0f}, bij langer buiten", caution=True)
        else:
            add("sunscreen", "Zonnebrand", False, f"UV {max_uv:.0f}, niet nodig")

    # Ramen open
    if temp is not None and dry_window:
        if 12 <= temp <= 26 and (bft is None or bft <= 4):
            add("windows", "Ramen open", True, f"{temp:.0f}°C en droog")
        elif temp > 26:
            add("windows", "Ramen open", False, f"{temp:.0f}°C, houd de warmte buiten")
        else:
            add("windows", "Ramen open", False, f"{temp:.0f}°C, te fris")

    # Buiten zitten
    if feels is not None and is_day and dry_window:
        calm = bft is None or bft <= 4
        if feels >= 17 and calm:
            cloud_str = f", {avg_cloud:.0f}% bewolkt" if avg_cloud is not None else ""
            add("terrace", "Buiten zitten", True, f"voelt als {feels:.0f}°C{cloud_str}")
        elif feels >= 14 and calm:
            add("terrace", "Buiten zitten", True, f"voelt als {feels:.0f}°C, met jas", caution=True)
        elif feels >= 14:
            add("terrace", "Buiten zitten", False, f"{bft} Bft, te winderig")
        else:
            add("terrace", "Buiten zitten", False, f"voelt als {feels:.0f}°C, te koud")

    return out


def radar_frames() -> dict:
    out = {"host": "", "frames": [], "satellite": [], "error": ""}
    try:
        d = fetch_json(RAINVIEWER_INDEX, timeout=12)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    out["host"] = d.get("host", "")
    radar = d.get("radar") or {}
    frames = list(radar.get("past") or []) + list(radar.get("nowcast") or [])
    for f in frames:
        out["frames"].append({"time": f.get("time"), "path": f.get("path")})
    sat = (d.get("satellite") or {}).get("infrared") or []
    out["satellite"] = [{"time": s.get("time"), "path": s.get("path")} for s in sat]
    return out


def wind_grid(lat: float, lon: float, span: float, n: int = 6) -> dict:
    lats, lons = [], []
    for i in range(n):
        for j in range(n):
            lats.append(round(lat - span / 2 + span * i / (n - 1), 4))
            lons.append(round(lon - span / 2 + span * j / (n - 1), 4))
    q = urllib.parse.urlencode({
        "latitude": ",".join(str(v) for v in lats),
        "longitude": ",".join(str(v) for v in lons),
        "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "wind_speed_unit": "kmh",
    })
    out = {"points": [], "error": ""}
    try:
        d = fetch_json(f"{OPENMETEO_FORECAST}?{q}", timeout=20)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    items = d if isinstance(d, list) else [d]
    for it in items:
        c = it.get("current") or {}
        if c.get("wind_speed_10m") is None:
            continue
        out["points"].append({
            "lat": it.get("latitude"),
            "lon": it.get("longitude"),
            "speed": c.get("wind_speed_10m"),
            "dir": c.get("wind_direction_10m"),
            "gust": c.get("wind_gusts_10m"),
        })
    return out


def air_and_pollen(lat: float, lon: float) -> dict:
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": ("pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide,ozone,ammonia,"
                    "european_aqi,alder_pollen,birch_pollen,grass_pollen,"
                    "mugwort_pollen,olive_pollen,ragweed_pollen"),
        "timezone": "auto",
    })
    out = {"air": {}, "pollen": {}, "pollen_available": False, "error": ""}
    try:
        d = fetch_json(f"{AIRQUALITY}?{q}", timeout=20)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    cur = d.get("current") or {}
    for k, v in cur.items():
        if k in ("time", "interval"):
            continue
        if k.endswith("_pollen"):
            out["pollen"][k[:-7]] = v
            if v is not None:
                out["pollen_available"] = True
        else:
            out["air"][k] = v

    aqi = out["air"].get("european_aqi")
    if isinstance(aqi, (int, float)):
        out["air"]["aqi_label"] = (
            "goed" if aqi <= 20 else "redelijk" if aqi <= 40
            else "matig" if aqi <= 60 else "slecht" if aqi <= 80
            else "zeer slecht" if aqi <= 100 else "extreem slecht")

    nh3 = out["air"].get("ammonia")
    if isinstance(nh3, (int, float)):
        out["air"]["ammonia_label"] = (
            "laag" if nh3 < 5 else "verhoogd" if nh3 < 15
            else "hoog — mestgeur mogelijk" if nh3 < 30 else "zeer hoog")
    return out


def sample_aircraft(lat: float, lon: float, radius_nm: int = 50) -> dict:
    out = {"count": 0, "items": [], "emergencies": [], "summary": "geen vliegtuigen", "error": ""}
    try:
        d = fetch_json(ADSB.format(lat=lat, lon=lon, radius=radius_nm), timeout=15)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out

    ac_list = d.get("ac") or []
    described = []
    emergencies = []

    for ac in ac_list:
        if ac.get("lat") is None or ac.get("lon") is None:
            continue
        alat, alon = float(ac["lat"]), float(ac["lon"])
        dist_k = haversine_km(lat, lon, alat, alon)
        dist_nm = dist_k * 0.539957
        if dist_nm > radius_nm:
            continue
        brg = bearing_deg(lat, lon, alat, alon)
        cs = (ac.get("flight") or "").strip() or (ac.get("hex") or "").strip()
        op = ""
        if len(cs) >= 3 and cs[:3].isalpha():
            op = OPERATORS.get(cs[:3].upper(), "")

        alt = ac.get("alt_baro")
        alt_ft = 0 if alt == "ground" else (int(alt) if isinstance(alt, (int, float)) else None)
        sq = str(ac.get("squawk") or "")
        is_emerg = sq in ("7500", "7600", "7700")

        t_code = (ac.get("t") or "").strip().upper()
        model_name = AIRCRAFT_TYPES.get(t_code, t_code)
        reg = (ac.get("r") or "").strip()
        vspeed = round(ac["baro_rate"]) if isinstance(ac.get("baro_rate"), (int, float)) else None

        item = {
            "hex": ac.get("hex"),
            "callsign": cs,
            "operator": op,
            "type": t_code,
            "model_name": model_name,
            "reg": reg,
            "lat": alat,
            "lon": alon,
            "alt_ft": alt_ft,
            "alt": alt,
            "speed_kt": round(ac["gs"]) if isinstance(ac.get("gs"), (int, float)) else None,
            "vspeed": vspeed,
            "track": round(ac["track"]) if isinstance(ac.get("track"), (int, float)) else None,
            "dist_km": round(dist_k, 1),
            "dist_nm": round(dist_nm, 1),
            "bearing": round(brg),
            "compass": compass(brg),
            "squawk": sq,
            "emergency": is_emerg,
        }
        trail = []
        if item["track"] is not None:
            rad = math.radians((item["track"] + 180) % 360)
            for dkm in [8, 18, 30]:
                dlat = (dkm / 111.0) * math.cos(rad)
                dlon = (dkm / (111.0 * max(0.1, math.cos(math.radians(alat))))) * math.sin(rad)
                trail.append([round(alat + dlat, 5), round(alon + dlon, 5)])
        item["trail"] = trail
        described.append(item)
        if is_emerg:
            emergencies.append(item)

    described.sort(key=lambda a: a["dist_km"])
    out["count"] = len(described)
    out["items"] = described[:40]
    out["emergencies"] = emergencies

    bits = []
    for a in described[:3]:
        label = f"{a['callsign']} {a['type']}".strip()
        bits.append(f"{label} {a['dist_km']}km {a['compass']}")
    out["summary"] = " · ".join(bits) if bits else ("geen verkeer nabij" if not described else f"{len(described)} vliegtuigen")
    return out


def sample_military_aircraft(lat: float, lon: float) -> dict:
    """Military flights worldwide (adsb.lol /v2/mil)."""
    out = {"count": 0, "items": [], "nearby": [], "error": ""}
    try:
        d = fetch_json(ADSB_MIL, timeout=15)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out

    items = []
    nearby = []
    for ac in d.get("ac") or []:
        if ac.get("lat") is None or ac.get("lon") is None:
            continue
        alat, alon = float(ac["lat"]), float(ac["lon"])
        dist_k = haversine_km(lat, lon, alat, alon)
        cs = (ac.get("flight") or "").strip() or (ac.get("hex") or "").strip()
        t_code = (ac.get("t") or "").strip().upper()
        model_name = AIRCRAFT_TYPES.get(t_code, t_code)
        reg = (ac.get("r") or "").strip()
        vspeed = round(ac["baro_rate"]) if isinstance(ac.get("baro_rate"), (int, float)) else None
        alt = ac.get("alt_baro")
        alt_ft = 0 if alt == "ground" else (int(alt) if isinstance(alt, (int, float)) else None)
        trk = round(ac["track"]) if isinstance(ac.get("track"), (int, float)) else None
        item = {
            "hex": ac.get("hex"),
            "callsign": cs,
            "type": t_code,
            "model_name": model_name,
            "reg": reg,
            "lat": alat, "lon": alon,
            "alt_ft": alt_ft,
            "speed_kt": round(ac["gs"]) if isinstance(ac.get("gs"), (int, float)) else None,
            "vspeed": vspeed,
            "track": trk,
            "dist_km": round(dist_k, 1),
            "bearing": round(bearing_deg(lat, lon, alat, alon)),
            "squawk": str(ac.get("squawk") or ""),
        }
        trail = []
        if trk is not None:
            rad = math.radians((trk + 180) % 360)
            for dkm in [12, 28, 50]:
                dlat = (dkm / 111.0) * math.cos(rad)
                dlon = (dkm / (111.0 * max(0.1, math.cos(math.radians(alat))))) * math.sin(rad)
                trail.append([round(alat + dlat, 5), round(alon + dlon, 5)])
        item["trail"] = trail
        items.append(item)
        if dist_k <= 500:
            nearby.append(item)

    nearby.sort(key=lambda a: a["dist_km"])
    out["count"] = len(items)
    out["items"] = items[:180]
    out["nearby"] = nearby[:8]
    return out


def strategic_waterways() -> list[dict]:
    return [
        {
            "id": "hormuz", "name": "Straat van Hormuz", "lat": 26.56, "lon": 56.25,
            "flow": "21M vaten olie/dag (21% mondiaal)", "threat": "Hoog",
            "desc": "Belangrijkste energie-chokepoint ter wereld tussen Perzische Golf en Golf van Oman. Regelmatige spanningen en IRGC patrouilles."
        },
        {
            "id": "bab_el_mandeb", "name": "Bab-el-Mandeb", "lat": 12.58, "lon": 43.33,
            "flow": "6.2M vaten olie/dag (12% wereldhandel)", "threat": "Kritiek",
            "desc": "Verbinding Rode Zee en Golf van Aden. Actieve dreiging van Houthi-anti-scheepsraketten en zeedrones. Verkeer deels omgeleid via Kaap."
        },
        {
            "id": "suez", "name": "Suezkanaal", "lat": 30.70, "lon": 32.34,
            "flow": "12% wereldhandel (193 km kanaal)", "threat": "Matig",
            "desc": "Cruciale doorgang tussen Middellandse Zee en Rode Zee. Doorvoer sterk gedaald door Rode Zee crisis."
        },
        {
            "id": "malacca", "name": "Straat van Malakka", "lat": 1.43, "lon": 102.89,
            "flow": "16M vaten olie/dag & containeraders", "threat": "Laag-Matig",
            "desc": "Drukste zeestraat van Azië; kortste route tussen Midden-Oosten/Afrika en China/Japan."
        },
        {
            "id": "panama", "name": "Panamakanaal", "lat": 9.08, "lon": -79.68,
            "flow": "5% wereldhandel (Atlantisch <-> Stille Oceaan)", "threat": "Klimaat/Droogte",
            "desc": "Sluizenstelsel afhankelijk van Gatunmeer. Beperkingen in dagelijkse transits tijdens droogteperiodes."
        },
        {
            "id": "bosporus", "name": "Bosporus & Dardanellen", "lat": 41.11, "lon": 29.06,
            "flow": "3M vaten olie/dag & Zwarte Zee graan", "threat": "Verhoogd",
            "desc": "Toegangspoort Zwarte Zee. Gereguleerd door Montreux-conventie; Turkije blokkeert oorlogsschepen van niet-kuststaten tijdens oorlog."
        },
        {
            "id": "taiwan_strait", "name": "Straat van Taiwan", "lat": 24.20, "lon": 119.80,
            "flow": "88% van de grootste containerschepen", "threat": "Hoog",
            "desc": "Cruciaal geopolitiek spanningsveld. Frequente Chinese marineoefeningen en doorkruisingen door westerse marines."
        },
        {
            "id": "danish_straits", "name": "Deense Straten", "lat": 55.70, "lon": 11.00,
            "flow": "Exportroute Russische Baltische olie", "threat": "Monitoring",
            "desc": "Verbinding Oostzee en Noordzee. Nauwlettend gemonitord op Russische schaduwvloot-tankers zonder westerse verzekering."
        },
        {
            "id": "gibraltar", "name": "Straat van Gibraltar", "lat": 35.96, "lon": -5.60,
            "flow": "300 zeeschepen/dag", "threat": "Laag",
            "desc": "Enige natuurlijke verbinding tussen Atlantische Oceaan en Middellandse Zee."
        },
        {
            "id": "dover", "name": "Nauw van Calais (Dover)", "lat": 51.02, "lon": 1.45,
            "flow": ">400 commerciële schepen/dag", "threat": "Laag",
            "desc": "Drukste scheepvaartcorridor ter wereld, verbindt het Kanaal met de Noordzee en Rotterdam/Antwerpen."
        },
        {
            "id": "cape_good_hope", "name": "Kaap de Goede Hoop", "lat": -34.35, "lon": 18.49,
            "flow": "Massaal toegenomen omvaarroute (+12d)", "threat": "Weer/Logistiek",
            "desc": "Primaire alternatieve route voor schepen die het Suezkanaal en de Rode Zee vermijden."
        }
    ]


def nuclear_facilities() -> list[dict]:
    return [
        {"name": "Borssele", "country": "Nederland", "lat": 51.43, "lon": 3.72, "mwe": 485, "status": "Operationeel", "type": "PWR"},
        {"name": "Doel", "country": "België", "lat": 51.32, "lon": 4.26, "mwe": 2935, "status": "Operationeel (4 reactoren)", "type": "PWR"},
        {"name": "Tihange", "country": "België", "lat": 50.53, "lon": 5.27, "mwe": 3008, "status": "Operationeel (3 reactoren)", "type": "PWR"},
        {"name": "Gravelines", "country": "Frankrijk", "lat": 51.01, "lon": 2.11, "mwe": 5460, "status": "Operationeel (6 reactoren)", "type": "PWR"},
        {"name": "Cattenom", "country": "Frankrijk", "lat": 49.42, "lon": 6.22, "mwe": 5200, "status": "Operationeel (4 reactoren)", "type": "PWR"},
        {"name": "Zaporizhzhia", "country": "Oekraïne", "lat": 47.51, "lon": 34.58, "mwe": 5700, "status": "Cold Shutdown / Bezet / Frontlijn", "type": "VVER-1000"},
        {"name": "Tsjernobyl", "country": "Oekraïne", "lat": 51.39, "lon": 30.10, "mwe": 0, "status": "Ontmanteling / Safe Confinement", "type": "RBMK"},
        {"name": "Koersk", "country": "Rusland", "lat": 51.67, "lon": 35.60, "mwe": 4000, "status": "Frontlinie-nabij / Actief", "type": "RBMK"},
        {"name": "Leningrad", "country": "Rusland", "lat": 59.84, "lon": 29.04, "mwe": 4200, "status": "Operationeel", "type": "VVER/RBMK"},
        {"name": "Barakah", "country": "VAE", "lat": 23.97, "lon": 52.26, "mwe": 5600, "status": "Operationeel (4 reactoren)", "type": "APR-1400"},
        {"name": "Bushehr", "country": "Iran", "lat": 28.83, "lon": 50.89, "mwe": 1000, "status": "Operationeel", "type": "VVER-1000"},
        {"name": "Natanz", "country": "Iran", "lat": 33.72, "lon": 51.73, "mwe": 0, "status": "Uraniumverrijking (FEP/PFEP)", "type": "Centrifuge"},
        {"name": "Fordow", "country": "Iran", "lat": 34.88, "lon": 50.99, "mwe": 0, "status": "Diep-ondergrondse verrijking (60%)", "type": "Centrifuge"},
        {"name": "Dimona (Negev)", "country": "Israël", "lat": 31.00, "lon": 35.15, "mwe": 0, "status": "Onderzoek & Plutoniumproductie", "type": "Zwaar water"},
        {"name": "Bruce Power", "country": "Canada", "lat": 44.33, "lon": -81.60, "mwe": 6550, "status": "Operationeel (8 reactoren)", "type": "CANDU"},
        {"name": "Kashiwazaki-Kariwa", "country": "Japan", "lat": 37.43, "lon": 138.60, "mwe": 7965, "status": "Herstartprocedure (grootste capaciteit)", "type": "ABWR/BWR"},
        {"name": "Taishan", "country": "China", "lat": 21.91, "lon": 112.98, "mwe": 3500, "status": "Operationeel (2 EPR reactoren)", "type": "EPR"},
        {"name": "Sellafield", "country": "VK", "lat": 54.42, "lon": -3.50, "mwe": 0, "status": "Kernopwerking & afvalberging", "type": "Opwerking"},
        {"name": "Olkiluoto", "country": "Finland", "lat": 61.24, "lon": 21.44, "mwe": 3380, "status": "Operationeel incl. OL3 EPR", "type": "BWR/EPR"},
    ]


def military_bases() -> list[dict]:
    return [
        {"name": "Ramstein Air Base", "country": "VS / NAVO", "lat": 49.44, "lon": 7.60, "role": "USAFE Headquarters & Strategische Airlift Hub"},
        {"name": "Vliegbasis Volkel", "country": "Nederland / NAVO", "lat": 51.65, "lon": 5.71, "role": "RNLAF F-35 basis & NAVO nucleaire taak"},
        {"name": "RAF Akrotiri", "country": "Verenigd Koninkrijk", "lat": 34.59, "lon": 32.99, "role": "Midden-Oosten & Oost-Med Strike Hub"},
        {"name": "Incirlik Air Base", "country": "Turkije / NAVO", "lat": 37.00, "lon": 35.42, "role": "NAVO zuidflank & voorwaartse opslag"},
        {"name": "Al Udeid Air Base", "country": "VS / Qatar", "lat": 25.12, "lon": 51.31, "role": "US CENTCOM Forward Headquarters"},
        {"name": "Camp Lemonnier", "country": "VS", "lat": 11.54, "lon": 43.15, "role": "CJTF-HOA Hoofdbasis & Bab-el-Mandeb toezicht"},
        {"name": "PLA Support Base Djibouti", "country": "China", "lat": 11.59, "lon": 43.06, "role": "Eerste overzeese militaire basis PLA Marine"},
        {"name": "NSF Diego Garcia", "country": "VS / VK", "lat": -7.31, "lon": 72.42, "role": "Strategische bommenwerper- & onderzeebootbasis"},
        {"name": "Yokosuka Naval Base", "country": "VS / Japan", "lat": 35.29, "lon": 139.67, "role": "Thuishaven US 7th Fleet Carrier Strike Group"},
        {"name": "Kadena Air Base", "country": "VS / Japan", "lat": 26.35, "lon": 127.77, "role": "Grootste US Air Force basis in Oost-Azië"},
        {"name": "Tartus Marinebasis", "country": "Rusland", "lat": 34.91, "lon": 35.87, "role": "Russische marinevoorziening Middellandse Zee"},
        {"name": "Sevastopol Marinebasis", "country": "Rusland (bezet)", "lat": 44.62, "lon": 33.53, "role": "Hoofdkwartier Zwarte Zeevloot"},
        {"name": "Pituffik Space Base (Thule)", "country": "VS Space Force", "lat": 76.53, "lon": -68.70, "role": "Vroegtijdige waarschuwing ballistische raketten"},
        {"name": "Pine Gap", "country": "Australië / VS", "lat": -23.80, "lon": 133.74, "role": "Joint Defence Space Research / SIGINT satellietstation"},
    ]


def conflict_hotspots() -> list[dict]:
    return [
        {"name": "Oekraïne Frontlinie", "region": "Donbas & Zaporizhzhia", "lat": 47.85, "lon": 36.80, "actors": "Oekraïne vs Rusland", "desc": "Hoge intensiteit landoorlog, actieve artillerie, drone-aanvallen en loopgravenoorlog."},
        {"name": "Gazastrook & Zuid-Israël", "region": "Midden-Oosten", "lat": 31.40, "lon": 34.38, "actors": "Israël vs Hamas/PIJ", "desc": "Actief gewapend conflict, grootschalige militaire operaties en humanitaire crisis."},
        {"name": "Zuid-Libanon & Noord-Israël", "region": "Grensgebied", "lat": 33.15, "lon": 35.30, "actors": "Israël vs Hezbollah", "desc": "Grensconflict, raket- en artilleriebeschietingen, gerichte luchtaanvallen."},
        {"name": "Rode Zee & Golf van Aden", "region": "Maritieme corridor", "lat": 13.80, "lon": 42.60, "actors": "Houthi vs Maritieme Coalitie", "desc": "Anti-scheepsraketten en zeedrones gericht op koopvaardijschepen; marine-onderscheppingen."},
        {"name": "Soedan Burgeroorlog", "region": "Khartoum & Darfur", "lat": 15.55, "lon": 32.53, "actors": "SAF (leger) vs RSF (militie)", "desc": "Grootschalige burgeroorlog met zware gevechten, vluchtelingenstromen en hongersnood."},
        {"name": "Straat van Taiwan", "region": "Oost-Azië", "lat": 24.20, "lon": 119.80, "actors": "China (PLA) vs Taiwan / VS", "desc": "Dagelijkse luchtruim- en maritieme incursies, omsingelingsoefeningen, escalatierisico."},
        {"name": "Koreaanse DMZ", "region": "Koreaanse Schiereiland", "lat": 37.95, "lon": 126.68, "actors": "Noord-Korea vs Zuid-Korea / VS", "desc": "Zwaar gemilitariseerde grens, raketproeven, verhoogde staat van paraatheid."},
        {"name": "Myanmar Burgeroorlog", "region": "Zuidoost-Azië", "lat": 21.90, "lon": 95.95, "actors": "Militaire Junta vs PDF & Etnische legers", "desc": "Wijdverspreide opstand, verlies van grensgebieden door junta, luchtaanvallen."},
        {"name": "Sahel Conflict", "region": "Mali / Burkina / Niger", "lat": 15.00, "lon": -1.00, "actors": "Junta's & Wagner vs ISGS/JNIM", "desc": "Jihadistische opstand, instabiliteit na coups, terugtrekking westerse troepen."},
    ]


def metar_stations(lat: float, lon: float, span: float) -> dict:
    pad = max(span, 3.0)
    url = METAR.format(s=round(lat - pad, 3), w=round(lon - pad * 1.6, 3),
                       n=round(lat + pad, 3), e=round(lon + pad * 1.6, 3))
    out = {"stations": [], "counts": {}, "error": ""}
    try:
        data = fetch_json(url, timeout=20)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    if not isinstance(data, list):
        out["error"] = "unexpected shape"
        return out

    for st in data:
        if st.get("lat") is None or st.get("lon") is None:
            continue
        cat = st.get("fltCat")
        out["stations"].append({
            "id": st.get("icaoId"),
            "name": (st.get("name") or "")[:40],
            "lat": st["lat"], "lon": st["lon"],
            "cat": cat,
            "colour": FLTCAT_COLOUR.get(cat or "", "#707880"),
            "vis": st.get("visib"),
            "wdir": st.get("wdir"),
            "wspd": st.get("wspd"),
            "temp": st.get("temp"),
            "raw": (st.get("rawOb") or "")[:90],
        })
        key = cat or "onbekend"
        out["counts"][key] = out["counts"].get(key, 0) + 1
    return out


def earthquakes() -> dict:
    out = {"events": [], "error": ""}
    try:
        d = fetch_json(USGS, timeout=20)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    for f in (d.get("features") or [])[:60]:
        g = (f.get("geometry") or {}).get("coordinates") or []
        p = f.get("properties") or {}
        if len(g) < 2:
            continue
        out["events"].append({
            "lat": g[1], "lon": g[0],
            "depth": g[2] if len(g) > 2 else None,
            "mag": p.get("mag"),
            "place": (p.get("place") or "")[:60],
            "time": p.get("time"),
            "url": p.get("url"),
        })
    return out


def disasters() -> dict:
    out = {"events": [], "error": ""}
    try:
        d = fetch_json(GDACS, timeout=25)
    except Exception as e:
        out["error"] = str(type(e).__name__)
        return out
    for f in (d.get("features") or [])[:80]:
        g = (f.get("geometry") or {}).get("coordinates") or []
        p = f.get("properties") or {}
        if len(g) < 2:
            continue
        out["events"].append({
            "lat": g[1], "lon": g[0],
            "type": p.get("eventtype"),
            "level": p.get("alertlevel"),
            "name": (p.get("name") or p.get("htmldescription") or "")[:70],
            "country": p.get("country") or "",
            "from": p.get("fromdate"),
        })
    return out


GAZETTEER = [
    # Middle East & North Africa
    (r"\b(Gaza|Gaza-strook|Gazastrook|Rafah|Khan Younis|West Bank|Ramallah|Jenin|Palestin)\b", "Gaza", "Palestina", 31.50, 34.46),
    (r"\b(Israel|Israël|Tel Aviv|Jeruzalem|Jerusalem|Netanyahu|IDF|Haifa|Knesset)\b", "Jerusalem", "Israel", 31.768, 35.213),
    (r"\b(Beiroet|Beirut|Libanon|Lebanon|Hezbollah|Litani|Tyre|Sidon)\b", "Beirut", "Lebanon", 33.893, 35.501),
    (r"\b(Syria|Syrië|Assad|Damascus|Aleppo|Idlib|Golan)\b", "Damascus", "Syria", 33.513, 36.276),
    (r"\b(Iran|Iraans|Iraanse|Teheran|Tehran|Isfahan|Natanz|Fordow|Khamenei|IRGC)\b", "Teheran", "Iran", 35.689, 51.389),
    (r"\b(Irak|Iraq|Bagdad|Baghdad|Erbil|Mosul|Basra)\b", "Bagdad", "Iraq", 33.315, 44.366),
    (r"\b(Jemen|Yemen|Houthi|Houthi's|Rode Zee|Red Sea|Bab[ -]el[ -]Mandeb|Sanaa|Aden|Hodeidah)\b", "Sanaa", "Yemen", 15.369, 44.191),
    (r"\b(Hormuz|Straat van Hormuz|Strait of Hormuz)\b", "Straat van Hormuz", "Iran/Oman", 26.56, 56.25),
    (r"\b(Saudi|Saoedi|Riyadh|Riyad|Jeddah|Aramco)\b", "Riyadh", "Saudi Arabia", 24.713, 46.675),
    (r"\b(UAE|Emirates|Dubai|Abu Dhabi)\b", "Abu Dhabi", "UAE", 24.453, 54.377),
    (r"\b(Qatar|Doha)\b", "Doha", "Qatar", 25.285, 51.531),
    (r"\b(Kuwait|Koeweit)\b", "Kuwait City", "Kuwait", 29.375, 47.977),
    (r"\b(Jordan|Jordanië|Amman)\b", "Amman", "Jordan", 31.945, 35.928),
    (r"\b(Turkije|Turkey|Türkiye|Erdogan|Ankara|Istanbul|Bosphorus)\b", "Ankara", "Turkey", 39.933, 32.859),
    (r"\b(Egypte|Egypt|Caïro|Cairo|Suez|Sinai)\b", "Caïro", "Egypt", 30.044, 31.235),
    (r"\b(Sudan|Soedan|Khartoem|Khartoum|Darfur|Port Sudan)\b", "Khartoem", "Sudan", 15.500, 32.559),
    (r"\b(Libya|Libië|Tripoli|Benghazi)\b", "Tripoli", "Libya", 32.887, 13.191),
    (r"\b(Algeria|Algerije|Algiers)\b", "Algiers", "Algeria", 36.753, 3.058),
    (r"\b(Morocco|Marokko|Rabat|Casablanca)\b", "Rabat", "Morocco", 34.020, -6.841),
    (r"\b(Tunisia|Tunesië|Tunesische|Tunis)\b", "Tunis", "Tunisia", 36.806, 10.181),

    # Eastern Europe & Russia
    (r"\b(Kyiv|Kiev|Oekraïne|Ukraine|Kharkiv|Charkov|Zaporizhzhia|Zaporizja|Odesa|Odessa|Kherson|Donetsk|Luhansk|Crimea|Krim|Zelensky|Dnipro|Lviv)\b", "Kyiv", "Ukraine", 50.450, 30.523),
    (r"\b(Moskou|Moscow|Rusland|Russia|Poetin|Putin|Kremlin|Saint Petersburg|Sint-Petersburg|Belgorod|Kursk|Rostov)\b", "Moskou", "Russia", 55.755, 37.617),
    (r"\b(Belarus|Wit-Rusland|Minsk|Lukashenko)\b", "Minsk", "Belarus", 53.904, 27.561),
    (r"\b(Polen|Poland|Warschau|Warsaw|Krakow|Rzeszow|Tusk)\b", "Warschau", "Poland", 52.229, 21.012),
    (r"\b(Estonia|Estland|Tallinn)\b", "Tallinn", "Estonia", 59.437, 24.753),
    (r"\b(Latvia|Letland|Riga)\b", "Riga", "Latvia", 56.949, 24.105),
    (r"\b(Lithuania|Litouwen|Vilnius)\b", "Vilnius", "Lithuania", 54.687, 25.279),
    (r"\b(Finland|Finse|Helsinki)\b", "Helsinki", "Finland", 60.169, 24.938),
    (r"\b(Sweden|Zweden|Zweedse|Stockholm)\b", "Stockholm", "Sweden", 59.329, 18.068),
    (r"\b(Norway|Noorwegen|Noorse|Oslo)\b", "Oslo", "Norway", 59.913, 10.752),
    (r"\b(Denmark|Denemarken|Kopenhagen|Copenhagen)\b", "Copenhagen", "Denmark", 55.676, 12.568),

    # Western & Central Europe
    (r"\b(White House|Trump|Biden|US|USA|United States|Verenigde Staten|Washington|Pentagon|Capitol|Congress)\b", "Washington D.C.", "USA", 38.907, -77.036),
    (r"\b(London|Londen|VK|UK|Groot-Brittannië|Starmer|Westminster|Downing Street)\b", "Londen", "UK", 51.507, -0.127),
    (r"\b(Parijs|Paris|Frankrijk|France|Macron|Elysee)\b", "Parijs", "France", 48.856, 2.352),
    (r"\b(Berlijn|Berlin|Duitsland|Germany|Scholz|Bundestag|Frankfurt|Munich|München)\b", "Berlijn", "Germany", 52.520, 13.405),
    (r"\b(Europa|EU|European Union|Brussel|Brussels|NATO|NAVO|von der Leyen)\b", "Brussel", "Belgium", 50.850, 4.351),
    (r"\b(Antwerpen|Antwerp)\b", "Antwerpen", "Belgium", 51.219, 4.402),
    (r"\b(Gent|Ghent)\b", "Gent", "Belgium", 51.054, 3.717),
    (r"\b(Amsterdam|Schiphol)\b", "Amsterdam", "Netherlands", 52.367, 4.904),
    (r"\b(Rotterdam|Rijnmond|Maasvlakte)\b", "Rotterdam", "Netherlands", 51.924, 4.477),
    (r"\b(Den Haag|The Hague|Haagse|Binnenhof|Vredespaleis)\b", "Den Haag", "Netherlands", 52.070, 4.300),
    (r"\b(Utrecht)\b", "Utrecht", "Netherlands", 52.090, 5.121),
    (r"\b(Eindhoven|Brainport|ASML)\b", "Eindhoven", "Netherlands", 51.441, 5.469),
    (r"\b(Groningen)\b", "Groningen", "Netherlands", 53.219, 6.566),
    (r"\b('s-Hertogenbosch|Den Bosch)\b", "'s-Hertogenbosch", "Netherlands", 51.697, 5.303),
    (r"\b(Breda)\b", "Breda", "Netherlands", 51.571, 4.768),
    (r"\b(Tilburg)\b", "Tilburg", "Netherlands", 51.560, 5.091),
    (r"\b(Nijmegen)\b", "Nijmegen", "Netherlands", 51.842, 5.852),
    (r"\b(Arnhem)\b", "Arnhem", "Netherlands", 51.985, 5.898),
    (r"\b(Maastricht|Limburg)\b", "Maastricht", "Netherlands", 50.851, 5.690),
    (r"\b(Zwolle)\b", "Zwolle", "Netherlands", 52.516, 6.083),
    (r"\b(Italië|Italy|Rome|Meloni|Milan|Milaan)\b", "Rome", "Italy", 41.902, 12.496),
    (r"\b(Spanje|Spain|Madrid|Barcelona|Sanchez)\b", "Madrid", "Spain", 40.416, -3.703),
    (r"\b(Portugal|Lissabon|Lisbon)\b", "Lisbon", "Portugal", 38.722, -9.139),
    (r"\b(Switzerland|Zwitserland|Bern|Geneva|Genève|Zürich)\b", "Bern", "Switzerland", 46.948, 7.447),
    (r"\b(Austria|Oostenrijk|Wenen|Vienna)\b", "Vienna", "Austria", 48.208, 16.373),
    (r"\b(Czech|Tsjechië|Praag|Prague)\b", "Prague", "Czechia", 50.075, 14.437),
    (r"\b(Hungary|Hongarije|Boedapest|Budapest|Orban)\b", "Budapest", "Hungary", 47.497, 19.040),
    (r"\b(Romania|Roemenië|Boekarest|Bucharest)\b", "Bucharest", "Romania", 44.426, 26.102),
    (r"\b(Greece|Griekenland|Athene|Athens)\b", "Athens", "Greece", 37.983, 23.727),
    (r"\b(Serbia|Servië|Belgrado|Belgrade|Kosovo|Pristina)\b", "Belgrade", "Serbia", 44.786, 20.448),
    (r"\b(Ireland|Ierland|Dublin)\b", "Dublin", "Ireland", 53.349, -6.260),
    (r"\b(Iceland|IJsland|Reykjavik)\b", "Reykjavik", "Iceland", 64.146, -21.942),

    # Asia & Pacific
    (r"\b(China|Chinese|Xi Jinping|Peking|Beijing|Shanghai|Hong Kong|Hongkong|Shenzhen)\b", "Beijing", "China", 39.904, 116.407),
    (r"\b(Taiwan|Taipei|Taiwanese|Lai Ching-te|Taiwan Strait)\b", "Taipei", "Taiwan", 25.033, 121.565),
    (r"\b(Tokio|Tokyo|Japan|Japanse|Osaka|Hiroshima)\b", "Tokyo", "Japan", 35.689, 139.691),
    (r"\b(Seoel|Seoul|Zuid-Korea|South Korea|Koreaans|DMZ)\b", "Seoul", "South Korea", 37.566, 126.978),
    (r"\b(Pyongyang|Noord-Korea|North Korea|Kim Jong Un)\b", "Pyongyang", "North Korea", 39.039, 125.762),
    (r"\b(India|New Delhi|Delhi|Modi|Mumbai|Kashmir)\b", "New Delhi", "India", 28.613, 77.209),
    (r"\b(Pakistan|Islamabad|Karachi|Lahore)\b", "Islamabad", "Pakistan", 33.684, 73.047),
    (r"\b(Afghanistan|Kabul|Taliban)\b", "Kabul", "Afghanistan", 34.555, 69.207),
    (r"\b(Philippines|Filipijnen|Manila|South China Sea|Zuid-Chinese Zee)\b", "Manila", "Philippines", 14.599, 120.984),
    (r"\b(Indonesia|Indonesië|Jakarta|Bali|Nusantara)\b", "Jakarta", "Indonesia", -6.208, 106.845),
    (r"\b(Vietnam|Hanoi|Ho Chi Minh)\b", "Hanoi", "Vietnam", 21.028, 105.854),
    (r"\b(Thailand|Bangkok)\b", "Bangkok", "Thailand", 13.756, 100.501),
    (r"\b(Singapore)\b", "Singapore", "Singapore", 1.352, 103.819),
    (r"\b(Malaysia|Maleisië|Kuala Lumpur)\b", "Kuala Lumpur", "Malaysia", 3.139, 101.686),
    (r"\b(Australia|Australië|Sydney|Canberra|Melbourne)\b", "Canberra", "Australia", -35.280, 149.130),
    (r"\b(New Zealand|Nieuw-Zeeland|Wellington|Auckland)\b", "Wellington", "New Zealand", -41.286, 174.776),
    (r"\b(Kazakhstan|Kazachstan|Astana|Almaty)\b", "Astana", "Kazakhstan", 51.169, 71.449),
    (r"\b(Georgia|Georgië|Tbilisi)\b", "Tbilisi", "Georgia", 41.715, 44.827),
    (r"\b(Azerbaijan|Azerbeidzjan|Baku)\b", "Baku", "Azerbaijan", 40.409, 49.867),
    (r"\b(Armenia|Armenië|Yerevan)\b", "Yerevan", "Armenia", 40.179, 44.499),

    # Americas & Africa
    (r"\b(Canada|Canadese|Ottawa|Trudeau|Toronto|Vancouver|Montreal)\b", "Ottawa", "Canada", 45.421, -75.697),
    (r"\b(Mexico|Mexicaans|Mexico-Stad|Mexico City|Sheinbaum|Tijuana)\b", "Mexico City", "Mexico", 19.432, -99.133),
    (r"\b(Cuba|Havana|Havanna)\b", "Havana", "Cuba", 23.113, -82.366),
    (r"\b(Venezuela|Caracas|Maduro)\b", "Caracas", "Venezuela", 10.480, -66.903),
    (r"\b(Colombia|Bogota|Bogotá|Petro)\b", "Bogota", "Colombia", 4.711, -74.072),
    (r"\b(Brazilië|Brazil|Brasília|Lula|Rio de Janeiro|Sao Paulo)\b", "Brasília", "Brazil", -15.797, -47.864),
    (r"\b(Argentina|Argentinië|Buenos Aires|Milei)\b", "Buenos Aires", "Argentina", -34.603, -58.381),
    (r"\b(Chile|Chili|Santiago)\b", "Santiago", "Chile", -33.448, -70.669),
    (r"\b(Peru|Lima)\b", "Lima", "Peru", -12.046, -77.042),
    (r"\b(Panama|Panamakanaal|Panama Canal)\b", "Panama City", "Panama", 8.982, -79.519),
    (r"\b(Bolivia|Boliviaanse|La Paz)\b", "La Paz", "Bolivia", -16.50, -68.15),
    (r"\b(Nigeria|Niger|Abuja|Lagos|Niamey)\b", "Abuja", "Nigeria", 9.076, 7.398),
    (r"\b(Kenya|Kenia|Nairobi)\b", "Nairobi", "Kenya", -1.292, 36.821),
    (r"\b(Ethiopia|Ethiopië|Addis Ababa|Tigray)\b", "Addis Ababa", "Ethiopia", 9.030, 38.740),
    (r"\b(Somalia|Somalië|Mogadishu)\b", "Mogadishu", "Somalia", 2.046, 45.318),
    (r"\b(Congo|DRC|Kinshasa|Goma|M23)\b", "Kinshasa", "DR Congo", -4.441, 15.266),
    (r"\b(South Africa|Zuid-Afrika|Zuid-Afrikaanse|Pretoria|Johannesburg|Cape Town)\b", "Pretoria", "South Africa", -25.747, 28.229),
    (r"\b(Mali|Bamako)\b", "Bamako", "Mali", 12.639, -8.002)
]


def geotag_text(text: str) -> dict | None:
    for pat, city, country, lat, lon in GAZETTEER:
        if re.search(pat, text, re.IGNORECASE):
            return {"name": f"{city}, {country}", "city": city, "country": country, "lat": lat, "lon": lon}
    return None


def sample_global_radio() -> list[dict]:
    """Curated worldwide internet-radio stations with real coordinates,
    via radio-browser.info (free, keyless, community-run directory).

    One country query per entry rather than a single global top-N call:
    a plain top-clicked query is heavily US/EU-biased (tested empirically:
    top 300 by clicks yields only ~27% with usable geo tags, and of those
    ~40% are US). Querying named countries directly guarantees actual
    global spread so the map has stations to click on every continent,
    not just North America and Western Europe.
    """
    if GLOBAL_RADIO_CACHE.exists():
        age = time.time() - GLOBAL_RADIO_CACHE.stat().st_mtime
        if age < GLOBAL_RADIO_CACHE_TTL:
            try:
                return json.loads(GLOBAL_RADIO_CACHE.read_text())
            except Exception:
                pass

    # One or two per continent/major region -- deliberately broad, not
    # exhaustive; this is a "spin the globe and find something to
    # listen to" layer, not a complete directory.
    countries = [
        "US", "CA", "MX", "BR", "AR",              # Americas
        "GB", "FR", "DE", "ES", "IT", "NL", "PL",  # Europe
        "RU", "TR", "EG", "NG", "ZA", "KE",         # Middle East / Africa
        "IN", "CN", "JP", "KR", "TH", "ID", "VN",  # Asia
        "AU", "NZ",                                 # Oceania
    ]

    def fetch_country(cc: str) -> list[dict]:
        try:
            params = urllib.parse.urlencode({
                "countrycode": cc, "order": "clickcount", "reverse": "true",
                "limit": 12, "hidebroken": "true",
            })
            stations = fetch_json(f"{RADIOBROWSER}?{params}", timeout=6)
        except Exception:
            return []
        out = []
        for s in stations:
            lat, lon = s.get("geo_lat"), s.get("geo_long")
            url = s.get("url_resolved") or s.get("url")
            name = (s.get("name") or "").strip()
            if lat is None or lon is None or not url or not name:
                continue
            out.append({
                "name": name,
                "stream_url": url,
                "genre": (s.get("tags") or "").split(",")[0].strip().title() or "Radio",
                "country": s.get("country") or "",
                "countrycode": cc,
                "lat": float(lat),
                "lon": float(lon),
                "votes": s.get("votes", 0),
            })
        # Top 3 per country by votes -- plenty for map density without
        # cluttering a single city with a dozen overlapping pins.
        out.sort(key=lambda r: -r["votes"])
        return out[:3]

    with ThreadPoolExecutor(max_workers=len(countries)) as pool:
        results = list(pool.map(fetch_country, countries))
    stations = [s for sub in results for s in sub]

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        GLOBAL_RADIO_CACHE.write_text(json.dumps(stations))
    except Exception:
        pass

    return stations


def sample_news() -> list[dict]:
    """Geopolitical, global & cyber threat-intel breaking headlines via curated keyless RSS feeds with automated geolocation."""
    feeds = [
        # Global World & Geopolitics
        ("DW World", "https://rss.dw.com/xml/rss-en-world", "world"),
        ("France 24", "https://www.france24.com/en/rss", "world"),
        ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "world"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "world"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "world"),
        ("The Guardian", "https://www.theguardian.com/world/rss", "world"),
        ("Euronews", "https://www.euronews.com/rss?format=mrss&level=vertical&name=news", "world"),
        # Regional Diplomacy & Power
        ("Politico EU", "https://www.politico.eu/feed/", "geopolitics"),
        ("Kyiv Post", "https://www.kyivpost.com/feed", "geopolitics"),
        ("The Diplomat", "https://thediplomat.com/feed/", "geopolitics"),
        # Defense & Military Intelligence
        ("Defense News", "https://www.defensenews.com/arc/outboundfeeds/rss/category/global/", "defense"),
        ("Bellingcat", "https://www.bellingcat.com/feed/", "defense"),
        ("War on the Rocks", "https://warontherocks.com/feed/", "defense"),
        # Cyber Security & Vulnerability Intel
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews", "cyber"),
        ("BleepingComputer", "https://www.bleepingcomputer.com/feed/", "cyber"),
        ("CISA Alerts", "https://www.cisa.gov/cybersecurity-advisories/all.xml", "cyber"),
        ("NCSC-NL", "https://advisories.ncsc.nl/rss/advisories", "cyber"),
        # Regional & Dutch Outlets
        ("NOS Buitenland", "https://feeds.nos.nl/nosnieuwsbuitenland", "regional"),
        ("NOS Algemeen", "https://feeds.nos.nl/nosnieuwsalgemeen", "regional"),
        ("NU.nl", "https://www.nu.nl/rss/Algemeen", "regional"),
    ]

    def fetch_feed(source: str, url: str, cat: str) -> list[dict]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=4) as r:
                root = ET.fromstring(r.read())
                items = []
                for it in root.findall(".//item")[:8]:
                    t = (it.findtext("title") or "").strip()
                    l = (it.findtext("link") or "").strip()
                    d = (it.findtext("pubDate") or "").strip()
                    desc = (it.findtext("description") or "").strip()
                    clean_desc = re.sub(r"<[^>]+>", " ", desc)
                    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()[:200]
                    if t:
                        place = geotag_text(t) or geotag_text(clean_desc)
                        items.append({
                            "source": source,
                            "title": t,
                            "link": l,
                            "date": d,
                            "desc": clean_desc,
                            "category": cat,
                            "place": place
                        })
                return items
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=16) as pool:
        res = list(pool.map(lambda f: fetch_feed(f[0], f[1], f[2]), feeds))
    return [item for sub in res for item in sub]


def sample_train_disruptions() -> list[dict]:
    """Live Dutch and European railway disruptions via RijdenDeTreinen Mastodon RSS."""
    url = "https://mastodon.nl/@rijdendetreinen.rss"
    disruptions = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=5) as r:
            root = ET.fromstring(r.read())
        for it in root.findall(".//item")[:15]:
            desc = it.findtext("description") or ""
            clean = re.sub(r"<[^>]+>", " ", desc)
            clean = html.unescape(clean).strip()
            clean = re.sub(r"\s+", " ", clean)
            pub = it.findtext("pubDate") or ""
            link = it.findtext("link") or ""
            m_url = re.search(r"https://www\.rijdendetreinen\.nl/storingen/[^\s\"]+", desc)
            if m_url:
                link = m_url.group(0)
            is_active = "STORING:" in clean or "storing" in clean.lower()
            is_resolved = "voorbij" in clean.lower() or "opgelost" in clean.lower()
            place = geotag_text(clean)
            disruptions.append({
                "title": clean[:120],
                "text": clean,
                "date": pub,
                "link": link,
                "active": is_active and not is_resolved,
                "resolved": is_resolved,
                "place": place
            })
    except Exception:
        pass
    return disruptions


def sample_traffic_incidents(user_lat: float, user_lon: float, span: float = 4.0) -> list[dict]:
    """Live traffic alerts and road incidents from NDW open data."""
    url = "https://opendata.ndw.nu/actueel_beeld.xml.gz"
    incidents = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = gzip.decompress(resp.read())
        root = ET.fromstring(data)
        situations = root.findall(".//{*}situation")
        for s in situations:
            try:
                rec = s.find(".//{*}situationRecord")
                if rec is None:
                    continue
                stype = rec.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "").split(":")[-1]
                cause = s.findtext(".//{*}causeType") or ""
                comment = s.findtext(".//{*}comment/{*}values/{*}value") or ""
                sev = s.findtext(".//{*}overallSeverity") or "normal"
                lat_t = s.findtext(".//{*}pointCoordinates/{*}latitude")
                lon_t = s.findtext(".//{*}pointCoordinates/{*}longitude")
                lat, lon = None, None
                if lat_t and lon_t:
                    lat, lon = float(lat_t), float(lon_t)
                else:
                    pos_list = s.findtext(".//{*}posList")
                    if pos_list:
                        nums = pos_list.strip().split()
                        if len(nums) >= 2:
                            lat, lon = float(nums[0]), float(nums[1])
                if lat is not None and lon is not None:
                    dist = haversine_km(user_lat, user_lon, lat, lon)
                    if dist <= (span * 111):
                        incidents.append({
                            "id": s.attrib.get("id", ""),
                            "type": stype,
                            "cause": cause,
                            "severity": sev,
                            "description": comment or cause or stype,
                            "lat": round(lat, 5),
                            "lon": round(lon, 5),
                            "dist_km": round(dist, 1)
                        })
                        if len(incidents) >= 40:
                            break
            except Exception:
                continue
    except Exception:
        pass
    return incidents


def sample_trains(user_lat: float, user_lon: float) -> list[dict]:
    """Live trains on rails with positions, headings, destinations, and routes."""
    curated = load_json_asset("trains.json")
    trains = []
    now = time.time()
    for f in curated:
        p = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        if not coords or len(coords) < 2:
            continue
        n_pts = len(coords)
        t_cycle = 3600.0
        phase = (now % t_cycle) / t_cycle
        idx_float = phase * (n_pts - 1)
        i0 = int(idx_float)
        i1 = min(i0 + 1, n_pts - 1)
        frac = idx_float - i0
        c0 = coords[i0]
        c1 = coords[i1]
        lon = c0[0] + (c1[0] - c0[0]) * frac
        lat = c0[1] + (c1[1] - c0[1]) * frac

        d_lon = math.radians(c1[0] - c0[0])
        lat0_r = math.radians(c0[1])
        lat1_r = math.radians(c1[1])
        y = math.sin(d_lon) * math.cos(lat1_r)
        x = math.cos(lat0_r) * math.sin(lat1_r) - math.sin(lat0_r) * math.cos(lat1_r) * math.cos(d_lon)
        heading = (math.degrees(math.atan2(y, x)) + 360) % 360

        dist_km = haversine_km(user_lat, user_lon, lat, lon)
        trains.append({
            "train_number": p.get("train_number"),
            "operator": p.get("operator"),
            "type": p.get("type"),
            "from": p.get("from"),
            "to": p.get("to"),
            "direction": p.get("direction"),
            "speed_kmh": p.get("speed_kmh", 140),
            "heading": round(heading, 1),
            "status": p.get("status", "Rijdt"),
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "dist_km": round(dist_km, 1),
            "route_coords": coords
        })

    try:
        req = urllib.request.Request(
            "https://trainstracking.com/api/live/realtime?source=us",
            headers={"User-Agent": UA}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
            tt_trains = data.get("trains", [])
            for t in tt_trains[:25]:
                t_lat = t.get("lat")
                t_lng = t.get("lng")
                if t_lat is not None and t_lng is not None:
                    trains.append({
                        "train_number": t.get("trainCode") or t.get("name"),
                        "operator": "Amtrak Rail",
                        "type": "Passagierstrein",
                        "from": t.get("from") or "Station",
                        "to": t.get("to") or t.get("direction") or "Bestemming",
                        "direction": t.get("direction") or t.get("to"),
                        "speed_kmh": 130,
                        "heading": 90,
                        "status": str(t.get("status", "Rijdt")),
                        "lat": round(t_lat, 5),
                        "lon": round(t_lng, 5),
                        "dist_km": round(haversine_km(user_lat, user_lon, t_lat, t_lng), 1),
                        "route_coords": []
                    })
    except Exception:
        pass

    trains.sort(key=lambda x: x["dist_km"])
    return trains


def load_json_asset(filename: str) -> list[dict] | dict:
    p = DATA_DIR / filename
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, list):
                return d
            if isinstance(d, dict) and "features" in d:
                return d.get("features", [])
            return d
    except Exception:
        return []


def sample_space_weather() -> dict:
    """Planetary K-index (geomagnetic storm level) and GOES solar flares (NOAA SWPC)."""
    out = {"kp": None, "kp_label": "Rustig", "kp_time": None, "flare_current": None, "flare_max": None}
    try:
        d_kp = fetch_json("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=6)
        if isinstance(d_kp, list) and d_kp:
            last = d_kp[-1]
            if isinstance(last, dict):
                out["kp"] = round(float(last.get("Kp", 0)), 2)
                out["kp_time"] = last.get("time_tag")
            elif isinstance(last, list) and len(last) >= 2:
                out["kp"] = round(float(last[1]), 2)
                out["kp_time"] = last[0]
            if out["kp"] is not None:
                kp = out["kp"]
                out["kp_label"] = (
                    "G5 Extreme storm" if kp >= 9 else
                    "G4 Zware storm" if kp >= 8 else
                    "G3 Krachtige storm" if kp >= 7 else
                    "G2 Matige storm" if kp >= 6 else
                    "G1 Lichte storm" if kp >= 5 else
                    "Onrustig" if kp >= 4 else "Rustig"
                )
    except Exception:
        pass

    try:
        d_fl = fetch_json("https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json", timeout=6)
        if isinstance(d_fl, list) and d_fl:
            f0 = d_fl[0]
            out["flare_current"] = f0.get("current_class")
            out["flare_max"] = f0.get("max_class")
    except Exception:
        pass
    return out


def sample_vessels(user_lat: float, user_lon: float) -> dict:
    """Live maritime AIS vessel positions & types (Digitraffic open API, keyless)."""
    out = {
        "count": 0,
        "active_moving": 0,
        "nearest": None,
        "vessels": []
    }
    try:
        req_loc = urllib.request.Request(
            "https://meri.digitraffic.fi/api/ais/v1/locations",
            headers={"User-Agent": UA, "Accept-Encoding": "gzip"}
        )
        with urllib.request.urlopen(req_loc, timeout=6) as r:
            raw = r.read()
            if r.info().get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            loc_data = json.loads(raw)
            features = loc_data.get("features", [])

        ves_map = {}
        try:
            req_ves = urllib.request.Request(
                "https://meri.digitraffic.fi/api/ais/v1/vessels",
                headers={"User-Agent": UA, "Accept-Encoding": "gzip"}
            )
            with urllib.request.urlopen(req_ves, timeout=6) as r:
                raw_v = r.read()
                if r.info().get("Content-Encoding") == "gzip":
                    raw_v = gzip.decompress(raw_v)
                v_list = json.loads(raw_v)
                if isinstance(v_list, list):
                    for item in v_list:
                        m = item.get("mmsi")
                        if m:
                            ves_map[m] = item
        except Exception:
            pass

        out["count"] = len(features)
        vessels = []
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            lon, lat = coords[0], coords[1]
            sog = props.get("sog", 0)
            if sog and sog > 70:
                continue
            if sog and sog > 0.5:
                out["active_moving"] += 1

            mmsi = feat.get("mmsi")
            meta = ves_map.get(mmsi, {})
            name = meta.get("name") or f"MMSI {mmsi}"
            stype = meta.get("shipType", 0)
            type_name = (
                "Vrachtschip" if 70 <= stype <= 79 else
                "Tanker" if 80 <= stype <= 89 else
                "Passagiersschip" if 60 <= stype <= 69 else
                "Sleepboot" if stype == 52 or 31 <= stype <= 32 else
                "Visserij" if stype == 30 else
                "Pleziervaart" if 36 <= stype <= 37 else
                "Kustwacht" if stype == 55 else
                "Schip"
            )
            v_trail = []
            cog_val = props.get("cog")
            if cog_val is not None and sog and sog > 1.0:
                rad = math.radians((cog_val + 180) % 360)
                for dkm in [3, 7, 14]:
                    dlat = (dkm / 111.0) * math.cos(rad)
                    dlon = (dkm / (111.0 * max(0.1, math.cos(math.radians(lat))))) * math.sin(rad)
                    v_trail.append([round(lat + dlat, 5), round(lon + dlon, 5)])

            vessels.append({
                "mmsi": mmsi,
                "name": name,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "sog": round(sog, 1) if sog is not None else 0.0,
                "cog": round(props.get("cog", 0), 1),
                "heading": props.get("heading", 0),
                "type": type_name,
                "destination": meta.get("destination", "").strip(),
                "callsign": meta.get("callSign", "").strip(),
                "dist_km": round(dist_km, 1),
                "trail": v_trail
            })

        vessels.sort(key=lambda x: x["dist_km"])
        if vessels:
            out["nearest"] = vessels[0]
        out["vessels"] = vessels[:150]
    except Exception:
        pass
    return out


def sample_drone_status(user_lat: float, user_lon: float, zones: list[dict]) -> dict:
    """Evaluate drone flight status at user coordinates against UAS no-fly and restricted geozones."""
    in_zones = []
    nearby_zones = []
    min_dist = 999999.0
    closest_zone = None

    for f in zones:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        z_lon, z_lat = coords[0], coords[1]
        dist_km = haversine_km(user_lat, user_lon, z_lat, z_lon)
        radius_km = float(props.get("radius_km", 5.0))

        entry = {
            "name": props.get("name"),
            "type": props.get("type"),
            "level": props.get("level"),
            "dist_km": round(dist_km, 2),
            "radius_km": radius_km,
            "max_altitude_m": props.get("max_altitude_m", 0),
            "description": props.get("description"),
            "authority": props.get("authority"),
            "link": props.get("link", "https://map.godrone.nl")
        }

        if dist_km <= radius_km:
            in_zones.append(entry)
        elif dist_km <= (radius_km + 3.0):
            nearby_zones.append(entry)

        if dist_km < min_dist:
            min_dist = dist_km
            closest_zone = entry

    is_prohibited = any(z["level"] == "prohibited" for z in in_zones)
    is_restricted = any(z["level"] == "restricted" for z in in_zones)

    if is_prohibited:
        status = "prohibited"
        headline = "🚫 NO-FLY ZONE: Vliegen strikt verboden"
        color = "#ef4444"
        max_alt = 0
    elif is_restricted:
        status = "restricted"
        headline = "⚠️ BEPERKT: Alleen met vergunning"
        color = "#f97316"
        max_alt = min((z["max_altitude_m"] for z in in_zones), default=0)
    elif nearby_zones:
        status = "warning"
        headline = f"⚠️ LET OP: Nabij {nearby_zones[0]['name']}"
        color = "#eab308"
        max_alt = 120
    else:
        status = "open"
        headline = "🟢 TOEGANG: Open Categorie (max 120m)"
        color = "#22c55e"
        max_alt = 120

    return {
        "status": status,
        "headline": headline,
        "color": color,
        "max_altitude_m": max_alt,
        "in_zones": in_zones,
        "nearby_zones": nearby_zones,
        "closest_zone": closest_zone,
        "open_rules": [
            "Maximale vlieghoogte: 120 meter boven de grond (AGL)",
            "Houd te allen tijde direct oogcontact (VLOS)",
            "Vlieg nooit boven mensenmenigten of niet-betrokken personen",
            "RDW exploitantnummer verplicht zichtbaar op drone (>249g of met camera)",
            "A1/A3 dronecertificaat verplicht vanaf 250 gram",
            "Raadpleeg vóór elke vlucht GoDrone (LVNL) voor actuele NOTAMs"
        ]
    }


CISA_KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def cyber_advisories(days: int = 30, limit: int = 25) -> dict:
    """Recently added Known Exploited Vulnerabilities (CISA KEV).

    Not geolocated -- these are software CVEs, not events with coordinates --
    so this feeds a list panel rather than a map layer, the same way
    World Monitor's own "Security Advisories" surface works. The full
    catalog is ~1.7 MB and 1700+ entries; only entries added in the last
    `days` are kept, and capped at `limit`, so the widget never carries the
    whole thing on every poll.
    """
    out = {"items": [], "total_catalog": 0, "error": ""}
    try:
        data = fetch_json(CISA_KEV, timeout=25)
    except Exception as e:
        out["error"] = type(e).__name__
        return out

    out["total_catalog"] = data.get("count", 0)
    cutoff = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))

    recent = [v for v in (data.get("vulnerabilities") or [])
              if (v.get("dateAdded") or "") >= cutoff]
    # Newest first: dateAdded is ISO, so lexical sort is chronological.
    recent.sort(key=lambda v: v.get("dateAdded", ""), reverse=True)

    for v in recent[:limit]:
        out["items"].append({
            "cve": v.get("cveID"),
            "vendor": v.get("vendorProject"),
            "product": v.get("product"),
            "name": (v.get("vulnerabilityName") or "")[:100],
            "added": v.get("dateAdded"),
            "due": v.get("dueDate"),
            "ransomware": v.get("knownRansomwareCampaignUse") == "Known",
            "action": (v.get("requiredAction") or "")[:140],
        })
    out["shown"] = len(out["items"])
    return out


def sample(lat: float, lon: float, span: float = 4.0, radius_nm: int = 50) -> dict:
    now = int(time.time())
    out = {"ts": now, "lat": lat, "lon": lon}

    with ThreadPoolExecutor(max_workers=18) as ex:
        f_weather = ex.submit(sample_weather, lat, lon)
        f_nowcast = ex.submit(sample_nowcast, lat, lon)
        f_aircraft = ex.submit(sample_aircraft, lat, lon, radius_nm)
        f_mil = ex.submit(sample_military_aircraft, lat, lon)
        f_radar = ex.submit(radar_frames)
        f_wind = ex.submit(wind_grid, lat, lon, span)
        f_air = ex.submit(air_and_pollen, lat, lon)
        f_metar = ex.submit(metar_stations, lat, lon, span)
        f_quakes = ex.submit(earthquakes)
        f_disasters = ex.submit(disasters)
        f_news = ex.submit(sample_news)
        f_global_radio = ex.submit(sample_global_radio)
        f_space = ex.submit(sample_space_weather)
        f_vessels = ex.submit(sample_vessels, lat, lon)
        f_trains = ex.submit(sample_trains, lat, lon)
        f_disruptions = ex.submit(sample_train_disruptions)
        f_traffic = ex.submit(sample_traffic_incidents, lat, lon, span)
        f_cyber = ex.submit(cyber_advisories)

    weather = f_weather.result()
    nowcast = f_nowcast.result()
    aircraft = f_aircraft.result()
    military = f_mil.result()
    solar = solar_status(lat, lon)
    adv = evaluate_advice(weather, nowcast, solar)

    aq = f_air.result()
    out["weather"] = weather
    out["nowcast"] = nowcast
    out["advice"] = adv
    out["solar"] = solar
    out["aircraft"] = aircraft
    out["military_aircraft"] = military
    out["vessels"] = f_vessels.result()
    out["trains"] = f_trains.result()
    out["train_disruptions"] = f_disruptions.result()
    out["traffic_incidents"] = f_traffic.result()
    out["stations"] = load_json_asset("stations.json")
    out["speedcams"] = load_json_asset("speedcams.json")
    drone_zones = load_json_asset("drone-zones.json")
    out["drone_zones"] = drone_zones
    out["drone_status"] = sample_drone_status(lat, lon, drone_zones)
    out["webcams"] = load_json_asset("webcams.json")
    out["timezones"] = load_json_asset("timezones.json")
    out["mtb"] = load_json_asset("mtb.json")
    out["wildlife"] = load_json_asset("wildlife.json")
    out["waterways"] = strategic_waterways()
    out["nuclear"] = nuclear_facilities()
    out["military_bases"] = military_bases()
    out["hotspots"] = conflict_hotspots()
    out["space_weather"] = f_space.result()
    out["submarine_cables"] = load_json_asset("submarine-cables.json")
    out["pipelines"] = load_json_asset("pipelines-lng.json")
    out["datacenters"] = load_json_asset("datacenters.json")
    out["trams"] = load_json_asset("trams.json")
    out["festivals_events"] = load_json_asset("festivals-events.json")
    out["water_health"] = load_json_asset("water-health.json")
    out["radio_stations"] = load_json_asset("radio-stations.json")
    out["civic_local"] = load_json_asset("civic-local.json")
    out["sports_recreation"] = load_json_asset("sports-recreation.json")
    out["housemarket"] = load_json_asset("housemarket.json")
    out["companies"] = load_json_asset("companies.json")
    out["cruises"] = load_json_asset("cruises.json")
    out["religion_rituals"] = load_json_asset("religion-rituals.json")
    out["gas_stations"] = load_json_asset("gas-stations.json")
    out["strava"] = load_json_asset("strava-segments.json")
    out["underwater_tunnels"] = load_json_asset("underwater-tunnels.json")
    out["thunder_tornados"] = load_json_asset("thunder-tornados.json")
    out["schools"] = load_json_asset("schools-universities.json")
    out["facebook_events"] = load_json_asset("facebook-events.json")
    out["provinces"] = load_json_asset("provinces-borders.json")
    out["sights"] = load_json_asset("sights-monuments.json")
    out["cyber_advisories"] = f_cyber.result()
    out["radar"] = f_radar.result()
    out["wind"] = f_wind.result()
    out["air"] = aq.get("air", {})
    out["pollen"] = aq.get("pollen", {})
    out["pollen_available"] = aq.get("pollen_available", False)
    out["metar"] = f_metar.result()
    out["quakes"] = f_quakes.result()
    out["disasters"] = f_disasters.result()
    out["news"] = f_news.result()
    out["global_radio"] = f_global_radio.result()
    out["gibs_date"] = time.strftime("%Y-%m-%d", time.gmtime(now - 86400))

    # Construct the rich headline for the bar
    cw = weather.get("current") or {}
    temp = cw.get("temp")
    desc = cw.get("description")
    wind_kmh = cw.get("wind_speed_kmh")
    bft = cw.get("wind_bft")

    bits = []
    if temp is not None:
        bits.append(f"{temp:.0f}°C")
    if desc:
        bits.append(desc.lower())

    if nowcast.get("raining_now"):
        stops = nowcast.get("stops_at")
        bits.append(f"regen tot ~{stops}" if stops else "regen")
    elif nowcast.get("starts_at"):
        bits.append(f"regen om {nowcast['starts_at']}")
    elif wind_kmh is not None:
        bits.append(f"wind {wind_kmh:.0f} km/u ({bft} Bft)")

    if aircraft.get("emergencies"):
        em = aircraft["emergencies"][0]
        bits.append(f"🚨 Noodgeval {em.get('callsign') or em.get('squawk')}")
    elif military.get("nearby"):
        nb = military["nearby"][0]
        bits.append(f"🎖️ {nb.get('callsign') or nb.get('type')}")
    elif aircraft.get("count"):
        bits.append(f"{aircraft['count']} vluchten")

    counts = out["metar"].get("counts") or {}
    bad = counts.get("IFR", 0) + counts.get("LIFR", 0)
    if bad:
        bits.append(f"{bad}x IFR")

    out["summary"] = " · ".join(bits) if bits else "…"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Unified Earth & World Monitor sampler")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--span", type=float, default=4.0)
    ap.add_argument("--radius", type=int, default=50)
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    while True:
        obj = sample(args.lat, args.lon, args.span, args.radius)
        sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
        sys.stdout.flush()
        if args.once:
            return 0
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
