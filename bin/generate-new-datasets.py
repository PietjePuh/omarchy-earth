#!/usr/bin/env python3
"""Generate additional geospatial datasets for Omarchy Earth:
- Gas stations (Tankstations) with fuel prices (Euro 95/E10, Super 98/E5, Diesel, LPG, Fastned 300kW)
- Strava popular cycling & running segments with elevation, KOM, grade %
- Underwater subsea tunnels (Eurotunnel London-Brussels, Fehmarnbelt, Storebælt Denmark, Westerschelde, Ryfast)
- Thunder & lightning strikes and tornado severe storm indicators
- Educational institutions: Universities, colleges, and top secondary schools
- Facebook community events, street markets & cultural gatherings
- Provinces & national border administrative lines
"""
import json
import pathlib

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# 1. GAS STATIONS & FUEL PRICES (Tankstations & Fastned / IONITY EV)
gas_stations = [
    {
        "id": "gas-shell-amstel",
        "brand": "Shell",
        "name": "Shell Amstelveenseweg",
        "address": "Amstelveenseweg 598",
        "city": "Amsterdam",
        "lat": 52.3321, "lon": 4.8564,
        "highway": "A10 West",
        "prices": {
            "e10": 1.979, "e5": 2.189, "diesel": 1.719, "lpg": 0.849, "ev_kwh": 0.69
        },
        "has_carwash": True, "has_shop": True, "has_air": True, "open_24h": True,
        "services": ["Shell Select", "Deli2Go", "EV Recharge 150kW", "Carwash"]
    },
    {
        "id": "gas-bp-zuidas",
        "brand": "BP",
        "name": "BP De Lucht (A2)",
        "address": "Rijksweg A2 Oostzijde",
        "city": "Bruchem / Zaltbommel",
        "lat": 51.7821, "lon": 5.2894,
        "highway": "A2",
        "prices": {
            "e10": 2.019, "e5": 2.229, "diesel": 1.749, "lpg": 0.899, "ev_kwh": 0.69
        },
        "has_carwash": False, "has_shop": True, "has_air": True, "open_24h": True,
        "services": ["Wild Bean Cafe", "Truck Diesel", "Fastned 300kW", "Bakkerij"]
    },
    {
        "id": "gas-fastned-sloterdijk",
        "brand": "Fastned",
        "name": "Fastned Snellaadstation Sloterdijk",
        "address": "Basisweg 2",
        "city": "Amsterdam",
        "lat": 52.3912, "lon": 4.8405,
        "highway": "A10 / N200",
        "prices": {
            "e10": None, "e5": None, "diesel": None, "lpg": None, "ev_kwh": 0.59
        },
        "has_carwash": False, "has_shop": True, "has_air": False, "open_24h": True,
        "services": ["300kW HPC Chargers", "Solar Canopy", "Autocharge", "Coffee"]
    },
    {
        "id": "gas-total-rotterdam",
        "brand": "TotalEnergies",
        "name": "TotalEnergies Maasboulevard",
        "address": "Maasboulevard 100",
        "city": "Rotterdam",
        "lat": 51.9162, "lon": 4.4985,
        "highway": "Centrum",
        "prices": {
            "e10": 1.969, "e5": 2.169, "diesel": 1.699, "lpg": None, "ev_kwh": 0.65
        },
        "has_carwash": True, "has_shop": True, "has_air": True, "open_24h": True,
        "services": ["Bonjour Café", "WashTec Carwash", "Excellium Brandstof"]
    },
    {
        "id": "gas-tango-utrecht",
        "brand": "Tango",
        "name": "Tango Onbemand Utrecht Noord",
        "address": "Einsteindreef 12",
        "city": "Utrecht",
        "lat": 52.1185, "lon": 5.1092,
        "highway": "N230 / Zuilense Ring",
        "prices": {
            "e10": 1.889, "e5": 2.079, "diesel": 1.639, "lpg": 0.799, "ev_kwh": None
        },
        "has_carwash": False, "has_shop": False, "has_air": True, "open_24h": True,
        "services": ["Goedkoop tanken", "Onbemand voordeel", "Contactloos pinnen"]
    },
    {
        "id": "gas-tinq-eindhoven",
        "brand": "TinQ",
        "name": "TinQ Eindhoven Meerenakker",
        "address": "Meerenakkerweg 1",
        "city": "Eindhoven",
        "lat": 51.4182, "lon": 5.4385,
        "highway": "N2 / A67",
        "prices": {
            "e10": 1.879, "e5": 2.069, "diesel": 1.629, "lpg": None, "ev_kwh": None
        },
        "has_carwash": True, "has_shop": False, "has_air": True, "open_24h": True,
        "services": ["TinQ Maxkorting", "Carwash boxen", "Pinnen aan de pomp"]
    },
    {
        "id": "gas-esso-denhaag",
        "brand": "Esso",
        "name": "Esso Schenkkade",
        "address": "Schenkkade 45",
        "city": "Den Haag",
        "lat": 52.0792, "lon": 4.3385,
        "highway": "A12 Utrechtsebaan",
        "prices": {
            "e10": 1.959, "e5": 2.159, "diesel": 1.699, "lpg": 0.839, "ev_kwh": 0.65
        },
        "has_carwash": True, "has_shop": True, "has_air": True, "open_24h": True,
        "services": ["Synergy Fuel", "Tijgerbrood Shop", "Carwash Express"]
    },
    {
        "id": "gas-fastned-haarlem",
        "brand": "Fastned",
        "name": "Fastned Haarlem Schipholweg",
        "address": "Schipholweg 1",
        "city": "Haarlem",
        "lat": 52.3685, "lon": 4.6542,
        "highway": "N205",
        "prices": {
            "e10": None, "e5": None, "diesel": None, "lpg": None, "ev_kwh": 0.59
        },
        "has_carwash": False, "has_shop": False, "has_air": False, "open_24h": True,
        "services": ["4x 300kW CCS", "100% Groene Stroom"]
    },
    {
        "id": "gas-shell-breukelen",
        "brand": "Shell",
        "name": "Shell Haarrijn (A2)",
        "address": "Rijksweg A2 Oostzijde km 47.3",
        "city": "Breukelen",
        "lat": 52.1712, "lon": 4.9985,
        "highway": "A2 Amsterdam-Utrecht",
        "prices": {
            "e10": 2.029, "e5": 2.239, "diesel": 1.759, "lpg": 0.889, "ev_kwh": 0.69
        },
        "has_carwash": True, "has_shop": True, "has_air": True, "open_24h": True,
        "services": ["Starbucks", "Burger King", "Shell Recharge 300kW", "Douches"]
    },
    {
        "id": "gas-ionity-zevenaar",
        "brand": "IONITY",
        "name": "IONITY Zevenaar (A12)",
        "address": "Doesburgseweg 41",
        "city": "Zevenaar",
        "lat": 51.9385, "lon": 6.0821,
        "highway": "A12 / Grens Duitsland",
        "prices": {
            "e10": None, "e5": None, "diesel": None, "lpg": None, "ev_kwh": 0.65
        },
        "has_carwash": False, "has_shop": True, "has_air": False, "open_24h": True,
        "services": ["350kW Ultra Fast Charging", "Restaurant", "Grensstop"]
    }
]

# 2. STRAVA POPULAR SEGMENTS & CYCLING CLIMBS
strava_segments = [
    {
        "id": "strava-cauberg",
        "name": "Cauberg (Amstel Gold Race Finish)",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 0.85,
        "avg_grade_pct": 7.2,
        "max_grade_pct": 12.8,
        "elevation_gain_m": 61,
        "lat": 50.8601, "lon": 5.8262,
        "city": "Valkenburg",
        "country": "Netherlands",
        "kom_time": "1m 18s",
        "qom_time": "1m 34s",
        "attempts": 482910,
        "url": "https://www.strava.com/segments/628741",
        "description": "De beroemdste heuvel van Nederland, finish van de Amstel Gold Race en WK Wielrennen."
    },
    {
        "id": "strava-amerongse-berg",
        "name": "Amerongse Berg (Zuidzijde)",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 1.22,
        "avg_grade_pct": 4.5,
        "max_grade_pct": 7.8,
        "elevation_gain_m": 55,
        "lat": 52.0082, "lon": 5.4618,
        "city": "Amerongen",
        "country": "Netherlands",
        "kom_time": "2m 04s",
        "qom_time": "2m 31s",
        "attempts": 320480,
        "url": "https://www.strava.com/segments/1296585",
        "description": "Het dak van de Utrechtse Heuvelrug. Prachtig asfalt door het bos."
    },
    {
        "id": "strava-posbank",
        "name": "Posbank Klim (Zijpenberg)",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 2.10,
        "avg_grade_pct": 3.8,
        "max_grade_pct": 9.2,
        "elevation_gain_m": 78,
        "lat": 52.0292, "lon": 6.0212,
        "city": "Rheden",
        "country": "Netherlands",
        "kom_time": "3m 42s",
        "qom_time": "4m 19s",
        "attempts": 284190,
        "url": "https://www.strava.com/segments/669894",
        "description": "Kronkelende klim door de bloeiende heide van Nationaal Park Veluwezoom."
    },
    {
        "id": "strava-kopje-bloemendaal",
        "name": "Kopje van Bloemendaal",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 0.74,
        "avg_grade_pct": 5.9,
        "max_grade_pct": 10.5,
        "elevation_gain_m": 44,
        "lat": 52.4042, "lon": 4.6205,
        "city": "Bloemendaal",
        "country": "Netherlands",
        "kom_time": "1m 12s",
        "qom_time": "1m 28s",
        "attempts": 412090,
        "url": "https://www.strava.com/segments/646272",
        "description": "De ultieme trainingsklim voor wielrenners uit Amsterdam en Haarlem."
    },
    {
        "id": "strava-keutenberg",
        "name": "Keutenberg (Steilste van NL)",
        "category": "Cat 3",
        "sport": "ride",
        "distance_km": 1.20,
        "avg_grade_pct": 5.9,
        "max_grade_pct": 22.0,
        "elevation_gain_m": 71,
        "lat": 50.8524, "lon": 5.8821,
        "city": "Schin op Geul",
        "country": "Netherlands",
        "kom_time": "2m 18s",
        "qom_time": "2m 54s",
        "attempts": 219800,
        "url": "https://www.strava.com/segments/638914",
        "description": "Berucht om de openingsstrook van 22% met het gele waarschuwingsbord."
    },
    {
        "id": "strava-vam-berg",
        "name": "VAM-berg (Col du VAM)",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 0.50,
        "avg_grade_pct": 8.0,
        "max_grade_pct": 15.0,
        "elevation_gain_m": 40,
        "lat": 52.7985, "lon": 6.5292,
        "city": "Wijster",
        "country": "Netherlands",
        "kom_time": "58s",
        "qom_time": "1m 15s",
        "attempts": 178400,
        "url": "https://www.strava.com/segments/18791054",
        "description": "Kunstmatige heuvel op voormalige afvalberg met kasseienstrook. NK en EK parcours."
    },
    {
        "id": "strava-alpe-dhuez",
        "name": "Alpe d'Huez (21 Bochten)",
        "category": "HC",
        "sport": "ride",
        "distance_km": 13.80,
        "avg_grade_pct": 8.1,
        "max_grade_pct": 13.0,
        "elevation_gain_m": 1110,
        "lat": 45.0921, "lon": 6.0685,
        "city": "Bourg d'Oisans",
        "country": "France",
        "kom_time": "37m 35s (Sepp Kuss)",
        "qom_time": "44m 21s (Illi Gardner)",
        "attempts": 594200,
        "url": "https://www.strava.com/segments/661401",
        "description": "De Nederlandse berg van de Tour de France met 21 genummerde haarspeldbochten."
    },
    {
        "id": "strava-muur-geraardsbergen",
        "name": "Muur van Geraardsbergen (Kapelmuur)",
        "category": "Cat 4",
        "sport": "ride",
        "distance_km": 0.92,
        "avg_grade_pct": 9.0,
        "max_grade_pct": 19.8,
        "elevation_gain_m": 83,
        "lat": 50.7712, "lon": 3.8834,
        "city": "Geraardsbergen",
        "country": "Belgium",
        "kom_time": "1m 49s",
        "qom_time": "2m 21s",
        "attempts": 389000,
        "url": "https://www.strava.com/segments/628817",
        "description": "Kasseienmonument uit de Ronde van Vlaanderen naar de kapel op de top."
    },
    {
        "id": "strava-mont-ventoux",
        "name": "Mont Ventoux (Bédoin)",
        "category": "HC",
        "sport": "ride",
        "distance_km": 21.40,
        "avg_grade_pct": 7.5,
        "max_grade_pct": 12.5,
        "elevation_gain_m": 1600,
        "lat": 44.1738, "lon": 5.2785,
        "city": "Bédoin",
        "country": "France",
        "kom_time": "55m 24s",
        "qom_time": "1h 06m",
        "attempts": 432100,
        "url": "https://www.strava.com/segments/1297593",
        "description": "De Kale Berg in de Provence, bekend om genadeloze hitte en mistralwind."
    }
]

# 3. UNDERWATER TUNNELS & MEGACROSSINGS (Channel Tunnel, Fehmarnbelt, Storebælt, Westerschelde, etc.)
underwater_tunnels = [
    {
        "id": "tunnel-chunnel",
        "name": "Channel Tunnel (Eurotunnel / Kanaaltunnel)",
        "link_route": "Folkestone (UK) ⇄ Coquelles / Calais (France) ⇄ London & Brussels",
        "type": "Rail & Eurostar Shuttle",
        "length_km": 50.45,
        "underwater_length_km": 37.90,
        "max_depth_m": 75,
        "year_opened": 1994,
        "country": "UK / France",
        "path": [
            [51.0934, 1.1524], [51.0742, 1.2584], [51.0312, 1.4521],
            [50.9624, 1.6821], [50.9242, 1.8105]
        ],
        "description": "Onderzeese spoorwegtunnel onder Het Kanaal. Verbindt Londen rechtstreeks met Brussel en Parijs via Eurostar.",
        "url": "https://www.getlinkgroup.com"
    },
    {
        "id": "tunnel-fehmarnbelt",
        "name": "Fehmarnbelt Fixed Link (Fehmarnbelttunnel)",
        "link_route": "Rødbyhavn (Denmark) ⇄ Puttgarden (Germany)",
        "type": "Immersed Road & Rail Tunnel",
        "length_km": 18.10,
        "underwater_length_km": 17.60,
        "max_depth_m": 40,
        "year_opened": 2029,
        "country": "Denmark / Germany",
        "path": [
            [54.6542, 11.3524], [54.5821, 11.2821], [54.5024, 11.2215]
        ],
        "description": "In aanbouw zijnde langste afgezonken tunnel ter wereld. Verkort de treinreis Hamburg-Kopenhagen naar 2,5 uur.",
        "url": "https://femern.com"
    },
    {
        "id": "tunnel-great-belt",
        "name": "Great Belt Fixed Link (Storebælt Spoorwegtunnel)",
        "link_route": "Halsskov (Zealand) ⇄ Sprogø Island ⇄ Funen (Denmark)",
        "type": "Subsea Bored Rail Tunnel",
        "length_km": 8.02,
        "underwater_length_km": 8.00,
        "max_depth_m": 75,
        "year_opened": 1997,
        "country": "Denmark",
        "path": [
            [55.3421, 11.0821], [55.3342, 11.0121], [55.3312, 10.9524]
        ],
        "description": "Onderzeese geboorde dubbelbuizige spoortunnel onder de Grote Belt in Denemarken.",
        "url": "https://storebaelt.dk"
    },
    {
        "id": "tunnel-oresund-drogden",
        "name": "Øresund Drogden Tunnel",
        "link_route": "Kastrup / Kopenhagen (Denmark) ⇄ Peberholm Island ⇄ Malmö (Sweden)",
        "type": "Immersed Motorway & Rail Tunnel",
        "length_km": 4.05,
        "underwater_length_km": 3.51,
        "max_depth_m": 22,
        "year_opened": 2000,
        "country": "Denmark / Sweden",
        "path": [
            [55.6212, 12.6582], [55.6021, 12.7121], [55.5892, 12.7682]
        ],
        "description": "Afgezonken tunnelverbinding die Denemarken met Zweden verbindt, eindigend op het kunstmatige eiland Peberholm.",
        "url": "https://www.oresundsbron.com"
    },
    {
        "id": "tunnel-westerschelde",
        "name": "Westerscheldetunnel",
        "link_route": "Borsele (Zuid-Beveland) ⇄ Terneuzen (Zeeuws-Vlaanderen)",
        "type": "Road (N62, 2x2)",
        "length_km": 6.60,
        "underwater_length_km": 5.80,
        "max_depth_m": 60,
        "year_opened": 2003,
        "country": "Netherlands",
        "path": [
            [51.4621, 3.8214], [51.4112, 3.8285], [51.3652, 3.8342]
        ],
        "description": "Langste verkeerstunnel van Nederland onder de Westerschelde, tot 60 meter diep onder NAP.",
        "url": "https://www.westerscheldetunnel.nl"
    },
    {
        "id": "tunnel-maasdeltatunnel",
        "name": "Maasdeltatunnel (Blankenburgverbinding A24)",
        "link_route": "Vlaardingen ⇄ Rozenburg (Rotterdam Haven)",
        "type": "Road (A24 Motorway)",
        "length_km": 0.945,
        "underwater_length_km": 0.90,
        "max_depth_m": 26,
        "year_opened": 2024,
        "country": "Netherlands",
        "path": [
            [51.8985, 4.2821], [51.8892, 4.2912]
        ],
        "description": "Nieuwste afgezonken snelwegtunnel onder Het Scheur bij Rotterdam ter ontlasting van de Beneluxtunnel.",
        "url": "https://www.blankenburgverbinding.nl"
    },
    {
        "id": "tunnel-ijtunnel",
        "name": "IJtunnel Amsterdam",
        "link_route": "Centrum Amsterdam ⇄ Amsterdam-Noord",
        "type": "Road (s116)",
        "length_km": 1.68,
        "underwater_length_km": 1.04,
        "max_depth_m": 20,
        "year_opened": 1968,
        "country": "Netherlands",
        "path": [
            [52.3732, 4.9085], [52.3842, 4.9182]
        ],
        "description": "Historische verkeerstunnel onder het IJ in Amsterdam.",
        "url": "https://amsterdam.nl"
    },
    {
        "id": "tunnel-beneluxtunnel",
        "name": "Beneluxtunnel Rotterdam",
        "link_route": "Schiedam / Vlaardingen ⇄ Pernis / Hoogvliet",
        "type": "Road (A4), Metro & Fiets",
        "length_km": 1.30,
        "underwater_length_km": 1.05,
        "max_depth_m": 23,
        "year_opened": 1967,
        "country": "Netherlands",
        "path": [
            [51.9021, 4.3821], [51.8885, 4.3892]
        ],
        "description": "Multimodale tunnel onder de Nieuwe Maas met snelwegbuizen, metrotunnel en fietstunnel.",
        "url": "https://rws.nl"
    },
    {
        "id": "tunnel-seikan",
        "name": "Seikan Tunnel (Japan)",
        "link_route": "Honshu Island ⇄ Hokkaido Island (Tsugaru Strait)",
        "type": "High Speed Rail (Shinkansen)",
        "length_km": 53.85,
        "underwater_length_km": 23.30,
        "max_depth_m": 240,
        "year_opened": 1988,
        "country": "Japan",
        "path": [
            [41.1821, 140.3521], [41.2542, 140.2821], [41.4212, 140.2215]
        ],
        "description": "Op een na langste onderzeese spoortunnel ter wereld, 100m onder de zeebodem van de Tsugaru-straat.",
        "url": "https://www.jrhokkaido.co.jp"
    },
    {
        "id": "tunnel-ryfast",
        "name": "Ryfylke Tunnel / Ryfast (Norway)",
        "link_route": "Stavanger ⇄ Strand (Hidle & Tau)",
        "type": "Road (National Road 13)",
        "length_km": 14.40,
        "underwater_length_km": 14.00,
        "max_depth_m": 292,
        "year_opened": 2019,
        "country": "Norway",
        "path": [
            [58.9821, 5.7521], [59.0212, 5.8214], [59.0542, 5.9121]
        ],
        "description": "Diepste onderzeese wegtunnel ter wereld op 292 meter onder zeeniveau.",
        "url": "https://vegvesen.no"
    },
    {
        "id": "tunnel-marmaray",
        "name": "Marmaray Tunnel (Istanbul)",
        "link_route": "Kazlıçeşme (Europe) ⇄ Ayrılık Çeşmesi (Asia)",
        "type": "Immersed Rail (Bosphorus)",
        "length_km": 13.50,
        "underwater_length_km": 1.40,
        "max_depth_m": 60,
        "year_opened": 2013,
        "country": "Turkey",
        "path": [
            [41.0021, 28.9821], [40.9985, 29.0185]
        ],
        "description": "Diepste afgezonken spoortunnel ter wereld onder de Bosporus, die Europa met Azië verbindt.",
        "url": "https://marmaray.gov.tr"
    }
]

# 4. THUNDER & LIGHTNING AND TORNADO RISK
thunder_tornados = {
    "blitzortung_source": "https://data.blitzortung.org",
    "recent_strikes": [
        {"lat": 52.12, "lon": 5.34, "age_min": 8, "current_ka": -24.5, "city": "Amersfoort", "type": "CG-"},
        {"lat": 51.98, "lon": 5.89, "age_min": 14, "current_ka": 38.2, "city": "Arnhem", "type": "CG+"},
        {"lat": 51.68, "lon": 5.29, "age_min": 22, "current_ka": -16.0, "city": "'s-Hertogenbosch", "type": "CG-"},
        {"lat": 52.42, "lon": 6.12, "age_min": 31, "current_ka": -31.4, "city": "Zwolle", "type": "CG-"},
        {"lat": 51.45, "lon": 5.52, "age_min": 45, "current_ka": 42.0, "city": "Helmond", "type": "CG+"}
    ],
    "severe_convective_cells": [
        {
            "name": "Supercell Convective Cluster Gelderland",
            "lat": 52.05, "lon": 5.95,
            "threat_level": "Orange",
            "lightning_rate_per_min": 48,
            "hail_risk_cm": 2.5,
            "gust_kmh": 95,
            "direction": "NNE",
            "speed_kmh": 50,
            "estofex_level": 2
        }
    ],
    "historical_tornadoes": [
        {
            "name": "Tornado Chaam & Borculo (F4)",
            "date": "1927-06-01 / 1925-08-10",
            "f_scale": "F4 (Catastrofaal)",
            "lat": 52.1167, "lon": 6.5167,
            "city": "Borculo / Chaam",
            "description": "Zwaarste tornado's uit de Nederlandse geschiedenis. Kerken en honderden huizen volledig verwoest."
        },
        {
            "name": "Windhoos Zierikzee (F2)",
            "date": "2022-06-27",
            "f_scale": "F2 (180-220 km/u)",
            "lat": 51.6502, "lon": 3.9167,
            "city": "Zierikzee",
            "description": "Destructieve windhoos door het centrum van Zierikzee met 1 dode en 150 beschadigde woningen."
        },
        {
            "name": "Waterhoos & Windhoos Vlieland",
            "date": "2023-08-14",
            "f_scale": "F1 / Waterhoos",
            "lat": 53.2985, "lon": 5.0682,
            "city": "Vlieland Strand",
            "description": "Spectaculaire waterhoos die aan land kwam op het Noordzeestrand."
        }
    ]
}

# 5. SCHOOLS & UNIVERSITIES (Universiteiten, Hogescholen & Lycea)
schools_universities = [
    {
        "id": "uni-tudelft",
        "name": "Technische Universiteit Delft (TU Delft)",
        "type": "University of Technology",
        "city": "Delft",
        "lat": 52.0022, "lon": 4.3724,
        "students": 27500,
        "ranking": "Top 10 Wereldwijd Engineering",
        "faculties": ["Luchtvaart- & Ruimtevaart", "Bouwkunde", "Elektrotechniek, Wiskunde & Informatica", "Civiele Techniek"],
        "url": "https://www.tudelft.nl",
        "campus_library": "TU Delft Library met iconisch grasdak"
    },
    {
        "id": "uni-uva-science",
        "name": "Universiteit van Amsterdam (UvA) Science Park",
        "type": "Research University",
        "city": "Amsterdam",
        "lat": 52.3548, "lon": 4.9542,
        "students": 42000,
        "ranking": "#58 QS World Ranking",
        "faculties": ["Faculteit der Natuurwetenschappen", "Informatica & AI", "FNWI"],
        "url": "https://www.uva.nl",
        "campus_library": "Science Park Bibliotheek"
    },
    {
        "id": "uni-vu",
        "name": "Vrije Universiteit Amsterdam (VU)",
        "type": "University",
        "city": "Amsterdam (Zuidas)",
        "lat": 52.3339, "lon": 4.8656,
        "students": 31500,
        "ranking": "Top 125 Wereldwijd",
        "faculties": ["Geneeskunde (VUmc)", "Rechtsgeleerdheid", "Economie & Bedrijfskunde", "Sociale Wetenschappen"],
        "url": "https://www.vu.nl",
        "campus_library": "VU Hoofdgebouw Campus Bibliotheek"
    },
    {
        "id": "uni-utrecht",
        "name": "Universiteit Utrecht (Utrecht Science Park)",
        "type": "Research University",
        "city": "Utrecht",
        "lat": 52.0862, "lon": 5.1742,
        "students": 38000,
        "ranking": "#1 van Nederland (Shanghai Ranking)",
        "faculties": ["Diergeneeskunde", "Geowetenschappen", "Geneeskunde (UMC Utrecht)", "Bètawetenschappen"],
        "url": "https://www.uu.nl",
        "campus_library": "Universiteitsbibliotheek De Uithof"
    },
    {
        "id": "uni-erasmus",
        "name": "Erasmus Universiteit Rotterdam (EUR)",
        "type": "University",
        "city": "Rotterdam",
        "lat": 51.9182, "lon": 4.5262,
        "students": 33000,
        "ranking": "Rotterdam School of Management Top 10 EU",
        "faculties": ["Erasmus School of Economics", "Rotterdam School of Management (RSM)", "Erasmus MC"],
        "url": "https://www.eur.nl",
        "campus_library": "Universiteitsbibliotheek Woudestein"
    },
    {
        "id": "uni-tue",
        "name": "Technische Universiteit Eindhoven (TU/e)",
        "type": "University of Technology",
        "city": "Eindhoven",
        "lat": 51.4485, "lon": 5.4905,
        "students": 14000,
        "ranking": "Brainport High-Tech Hub",
        "faculties": ["Werktuigbouwkunde", "Biomedische Technologie", "Electrical Engineering", "Applied Physics"],
        "url": "https://www.tue.nl",
        "campus_library": "MetaForum Bibliotheek"
    },
    {
        "id": "uni-wageningen",
        "name": "Wageningen University & Research (WUR)",
        "type": "Agriculture & Life Sciences",
        "city": "Wageningen",
        "lat": 51.9852, "lon": 5.6642,
        "students": 13200,
        "ranking": "#1 Wereldwijd Agriculture & Forestry",
        "faculties": ["Agrotechnologie", "Milieuwetenschappen", "Levensmiddelentechnologie"],
        "url": "https://www.wur.nl",
        "campus_library": "Forum Bibliotheek Wageningen Campus"
    },
    {
        "id": "uni-leiden",
        "name": "Universiteit Leiden (Oudste van NL)",
        "type": "Research University",
        "city": "Leiden",
        "lat": 52.1572, "lon": 4.4821,
        "students": 34000,
        "ranking": "Opgericht 1575 door Willem van Oranje",
        "faculties": ["Archeologie", "Geesteswetenschappen", "Rechtsgeleerdheid", "LUMC Geneeskunde"],
        "url": "https://www.universiteitleiden.nl",
        "campus_library": "Universiteitsbibliotheek Leiden (UB)"
    },
    {
        "id": "school-barlaeus",
        "name": "Barlaeus Gymnasium",
        "type": "Gymnasium (VWO)",
        "city": "Amsterdam",
        "lat": 52.3621, "lon": 4.8821,
        "students": 850,
        "ranking": "Top categoraal gymnasium",
        "faculties": ["Klassieke talen (Latijn & Grieks)", "VWO"],
        "url": "https://www.barlaeus.nl",
        "campus_library": "Weteringschans Bibliotheek"
    },
    {
        "id": "school-isa",
        "name": "International School of Amsterdam (ISA)",
        "type": "International School (IB)",
        "city": "Amstelveen",
        "lat": 52.2895, "lon": 4.8621,
        "students": 1300,
        "ranking": "International Baccalaureate World School",
        "faculties": ["Primary Years", "Middle Years", "IB Diploma"],
        "url": "https://www.isa.nl",
        "campus_library": "ISA Media Center"
    }
]

# 6. FACEBOOK EVENTS & COMMUNITY GATHERINGS
facebook_events = [
    {
        "id": "fb-ijhallen",
        "name": "IJ-Hallen Vlooienmarkt (Grootste van Europa)",
        "category": "Market & Vintage",
        "venue": "NDSM-Plein 1",
        "city": "Amsterdam",
        "lat": 52.4012, "lon": 4.8932,
        "schedule": "Eens per maand weekend (09:00 - 16:30)",
        "attending": 12500,
        "url": "https://ijhallen.nl",
        "fb_search_url": "https://www.facebook.com/events/search/?q=IJ-Hallen%20Amsterdam",
        "description": "Met 750 kramen de grootste vlooienmarkt van Europa in de monumentale scheepsbouwhallen van NDSM."
    },
    {
        "id": "fb-swan-market",
        "name": "Swan Market Rotterdam",
        "category": "Lifestyle & Food",
        "venue": "Museumpark / Binnenrotte",
        "city": "Rotterdam",
        "lat": 51.9135, "lon": 4.4721,
        "schedule": "Zondagen maandelijks (11:00 - 17:00)",
        "attending": 6200,
        "url": "https://swanmarket.nl",
        "fb_search_url": "https://www.facebook.com/events/search/?q=Swan%20Market%20Rotterdam",
        "description": "Creatieve lifestyle markt met handgemaakte sieraden, kunst, mode, live muziek en foodtrucks."
    },
    {
        "id": "fb-rollende-keukens",
        "name": "Het Weekend van de Rollende Keukens",
        "category": "Food & Festival",
        "venue": "Westergasfabriek",
        "city": "Amsterdam",
        "lat": 52.3858, "lon": 4.8712,
        "schedule": "Hemelvaartweekend jaarlijks (13:00 - 23:00)",
        "attending": 45000,
        "url": "https://rollendekeukens.amsterdam",
        "fb_search_url": "https://www.facebook.com/events/search/?q=Rollende%20Keukens%20Amsterdam",
        "description": "Honderden mobiele keukens en foodtrucks toveren het Westerpark om tot één groot openluchtrestaurant."
    },
    {
        "id": "fb-feelgood-eindhoven",
        "name": "FeelGood Market Strijp-S",
        "category": "Design & Music",
        "venue": "Klokgebouw / Ketelhuisplein",
        "city": "Eindhoven",
        "lat": 51.4485, "lon": 5.4572,
        "schedule": "Elke 3e zondag van de maand (12:00 - 18:00)",
        "attending": 7500,
        "url": "https://feelgoodmarket.nl",
        "fb_search_url": "https://www.facebook.com/events/search/?q=FeelGood%20Market%20Eindhoven",
        "description": "Bruisende markt met duurzame streekproducten, design, workshops en live optredens op Strijp-S."
    }
]

# 7. PROVINCES & BORDERS (12 Nederlandse Provincies met data & hoofdstad)
provinces_borders = [
    {
        "name": "Noord-Holland", "capital": "Haarlem", "population": 2920000, "area_km2": 4092,
        "lat": 52.60, "lon": 4.85, "commissaris": "Arthur van Dijk",
        "color": "#38bdf8", "url": "https://www.noord-holland.nl",
        "bounds": [[52.15, 4.50], [53.00, 5.30]]
    },
    {
        "name": "Zuid-Holland", "capital": "Den Haag", "population": 3750000, "area_km2": 3308,
        "lat": 52.00, "lon": 4.50, "commissaris": "Jaap Smit",
        "color": "#f59e0b", "url": "https://www.zuid-holland.nl",
        "bounds": [[51.70, 4.00], [52.30, 5.00]]
    },
    {
        "name": "Utrecht", "capital": "Utrecht", "population": 1380000, "area_km2": 1560,
        "lat": 52.09, "lon": 5.18, "commissaris": "Hans Oosters",
        "color": "#ef4444", "url": "https://www.provincie-utrecht.nl",
        "bounds": [[51.95, 4.85], [52.28, 5.50]]
    },
    {
        "name": "Gelderland", "capital": "Arnhem", "population": 2110000, "area_km2": 5136,
        "lat": 52.05, "lon": 5.95, "commissaris": "John Berends",
        "color": "#22c55e", "url": "https://www.gelderland.nl",
        "bounds": [[51.75, 5.00], [52.45, 6.75]]
    },
    {
        "name": "Noord-Brabant", "capital": "'s-Hertogenbosch", "population": 2600000, "area_km2": 5082,
        "lat": 51.55, "lon": 5.15, "commissaris": "Ina Adema",
        "color": "#ec4899", "url": "https://www.brabant.nl",
        "bounds": [[51.25, 4.20], [51.85, 6.00]]
    },
    {
        "name": "Limburg", "capital": "Maastricht", "population": 1120000, "area_km2": 2210,
        "lat": 51.05, "lon": 5.85, "commissaris": "Emile Roemer",
        "color": "#eab308", "url": "https://www.limburg.nl",
        "bounds": [[50.75, 5.60], [51.75, 6.20]]
    },
    {
        "name": "Overijssel", "capital": "Zwolle", "population": 1175000, "area_km2": 3421,
        "lat": 52.45, "lon": 6.45, "commissaris": "Andries Heidema",
        "color": "#8b5cf6", "url": "https://www.overijssel.nl",
        "bounds": [[52.15, 5.85], [52.75, 7.05]]
    },
    {
        "name": "Friesland (Fryslân)", "capital": "Leeuwarden", "population": 655000, "area_km2": 5749,
        "lat": 53.15, "lon": 5.80, "commissaris": "Arno Brok",
        "color": "#06b6d4", "url": "https://www.fryslan.frl",
        "bounds": [[52.80, 5.20], [53.50, 6.40]]
    },
    {
        "name": "Groningen", "capital": "Groningen", "population": 590000, "area_km2": 2960,
        "lat": 53.25, "lon": 6.75, "commissaris": "René Paas",
        "color": "#14b8a6", "url": "https://www.provinciegroningen.nl",
        "bounds": [[53.05, 6.20], [53.50, 7.20]]
    },
    {
        "name": "Drenthe", "capital": "Assen", "population": 495000, "area_km2": 2680,
        "lat": 52.85, "lon": 6.60, "commissaris": "Jetta Klijnsma",
        "color": "#f97316", "url": "https://www.provinciedrenthe.nl",
        "bounds": [[52.60, 6.20], [53.20, 7.00]]
    },
    {
        "name": "Zeeland", "capital": "Middelburg", "population": 388000, "area_km2": 2933,
        "lat": 51.50, "lon": 3.80, "commissaris": "Han Polman",
        "color": "#3b82f6", "url": "https://www.zeeland.nl",
        "bounds": [[51.20, 3.35], [51.75, 4.30]]
    },
    {
        "name": "Flevoland", "capital": "Lelystad", "population": 435000, "area_km2": 2412,
        "lat": 52.55, "lon": 5.55, "commissaris": "Arjen Gerritsen",
        "color": "#a855f7", "url": "https://www.flevoland.nl",
        "bounds": [[52.25, 5.20], [52.85, 5.95]]
    }
]

def save(filename: str, data):
    p = DATA_DIR / filename
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Generated {filename} ({p.stat().st_size:,} bytes)")

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save("gas-stations.json", gas_stations)
    save("strava-segments.json", strava_segments)
    save("underwater-tunnels.json", underwater_tunnels)
    save("thunder-tornados.json", thunder_tornados)
    save("schools-universities.json", schools_universities)
    save("facebook-events.json", facebook_events)
    save("provinces-borders.json", provinces_borders)

if __name__ == "__main__":
    main()
