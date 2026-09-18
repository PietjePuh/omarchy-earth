#!/usr/bin/env python3
"""Generate curated datasets for omarchy-earth extended capabilities:
- Trams (GVB, RET, HTM, U-OV)
- Festivals, Concert Arenas & Pokemon GO Hotspots
- Water Quality & Swimming Lakes (zwemwater)
- Radio Stations with direct streaming URLs
- Civic Info (Garbage schedule, street markets, police stations)
- Sports & Recreation (Pools, Darts, Ski, Skydive, Sailing)
- Housing Market Index
- Corporate HQs & Tech Campuses
- Cruise Lines & Terminals
- Religion & Rituals (Pilgrim ways, cathedrals, temples)
"""
import json
import pathlib

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# 1. TRAMS (Amsterdam GVB, Rotterdam RET, Den Haag HTM, Utrecht U-OV, Antwerp, Brussels)
trams_data = [
    {
        "network": "GVB Amsterdam",
        "line": "1",
        "name": "Tram 1: Muiderpoortstation &harr; Osdorp De Aker",
        "city": "Amsterdam",
        "color": "#22c55e",
        "coords": [
            [52.3605, 4.9312], [52.3615, 4.9198], [52.3638, 4.9085],
            [52.3647, 4.8912], [52.3621, 4.8834], [52.3612, 4.8711],
            [52.3582, 4.8524], [52.3551, 4.8215], [52.3512, 4.7942]
        ],
        "stops": ["Muiderpoortstation", "Weesperplein", "Leidseplein", "Overtoom", "Surinameplein", "Osdorp De Aker"]
    },
    {
        "network": "GVB Amsterdam",
        "line": "2",
        "name": "Tram 2: Centraal Station &harr; Nieuw Sloten",
        "city": "Amsterdam",
        "color": "#ef4444",
        "coords": [
            [52.3785, 4.8998], [52.3742, 4.8912], [52.3685, 4.8872],
            [52.3621, 4.8834], [52.3581, 4.8772], [52.3515, 4.8621],
            [52.3481, 4.8421], [52.3412, 4.8185]
        ],
        "stops": ["Centraal Station", "Dam", "Spui", "Leidseplein", "Museumplein", "Hoofddorpplein", "Nieuw Sloten"]
    },
    {
        "network": "GVB Amsterdam",
        "line": "5",
        "name": "Tram 5: Westergasfabriek &harr; Amstelveen Stadshart",
        "city": "Amsterdam / Amstelveen",
        "color": "#3b82f6",
        "coords": [
            [52.3852, 4.8712], [52.3785, 4.8792], [52.3621, 4.8834],
            [52.3581, 4.8772], [52.3412, 4.8721], [52.3021, 4.8612]
        ],
        "stops": ["Westergasfabriek", "Elandsgracht", "Leidseplein", "Museumplein", "Station Zuid", "Amstelveen Stadshart"]
    },
    {
        "network": "GVB Amsterdam",
        "line": "26",
        "name": "Tram 26: IJtram Centraal Station &harr; IJburg",
        "city": "Amsterdam",
        "color": "#8b5cf6",
        "coords": [
            [52.3785, 4.9015], [52.3775, 4.9215], [52.3762, 4.9482],
            [52.3651, 4.9782], [52.3581, 5.0085]
        ],
        "stops": ["Centraal Station", "Muziekgebouw", "Rietlandpark", "Zeeburgereiland", "IJburg"]
    },
    {
        "network": "RET Rotterdam",
        "line": "7",
        "name": "Tram 7: Willemsplein &harr; Woudestein (Erasmus Univ)",
        "city": "Rotterdam",
        "color": "#eab308",
        "coords": [
            [51.9125, 4.4785], [51.9215, 4.4721], [51.9251, 4.4852],
            [51.9212, 4.5115], [51.9181, 4.5285]
        ],
        "stops": ["Willemsplein", "Eendrachtsplein", "Centraal Station", "Oostplein", "Woudestein (Erasmus Univ)"]
    },
    {
        "network": "RET Rotterdam",
        "line": "23",
        "name": "Tram 23: Marconiplein &harr; Beverwaard (De Kuip)",
        "city": "Rotterdam",
        "color": "#ec4899",
        "coords": [
            [51.9152, 4.4325], [51.9215, 4.4721], [51.9151, 4.4892],
            [51.8941, 4.5215], [51.8785, 4.5512]
        ],
        "stops": ["Marconiplein", "Centraal Station", "Leuvehaven", "Stadion Feyenoord (De Kuip)", "Beverwaard"]
    },
    {
        "network": "HTM Den Haag",
        "line": "1",
        "name": "Tram 1: Scheveningen Noorderstrand &harr; Delft Tanthof",
        "city": "Den Haag / Delft",
        "color": "#06b6d4",
        "coords": [
            [52.1145, 4.2812], [52.0915, 4.3015], [52.0785, 4.3185],
            [52.0512, 4.3512], [52.0085, 4.3582], [51.9892, 4.3412]
        ],
        "stops": ["Scheveningen Strand", "Vredespaleis", "Centrum", "Station Hollands Spoor", "Delft Station", "Delft Tanthof"]
    },
    {
        "network": "HTM Den Haag",
        "line": "9",
        "name": "Tram 9: Scheveningen Noorderstrand &harr; Vrederust",
        "city": "Den Haag",
        "color": "#14b8a6",
        "coords": [
            [52.1145, 4.2812], [52.1021, 4.2982], [52.0812, 4.3215],
            [52.0715, 4.3225], [52.0412, 4.2715]
        ],
        "stops": ["Scheveningen Noorderstrand", "Madurodam", "Centraal Station", "Station Hollands Spoor", "Zuiderpark", "Vrederust"]
    },
    {
        "network": "U-OV Utrecht",
        "line": "22",
        "name": "Tram 22: Utrecht Centraal &harr; Science Park (Uithoflijn)",
        "city": "Utrecht",
        "color": "#f97316",
        "coords": [
            [52.0885, 5.1102], [52.0851, 5.1215], [52.0825, 5.1482],
            [52.0841, 5.1685], [52.0862, 5.1852]
        ],
        "stops": ["Utrecht Centraal Centrumzijde", "Vaartsche Rijn", "Galgenwaard", "UMC Utrecht", "Science Park P+R"]
    },
    {
        "network": "De Lijn Antwerpen",
        "line": "15",
        "name": "Tram 15: Linkeroever P+R &harr; Boechout P+R",
        "city": "Antwerpen",
        "color": "#10b981",
        "coords": [
            [51.2185, 4.3685], [51.2195, 4.4021], [51.2145, 4.4215],
            [51.1985, 4.4412], [51.1612, 4.4892]
        ],
        "stops": ["Linkeroever", "Groenplaats (Premetro)", "Diamant (Centraal)", "Mortsel", "Boechout"]
    }
]

# 2. FESTIVALS, CONCERTS & POKEMON GO HOTSPOTS
festivals_data = [
    {
        "id": "FEST-LOWLANDS",
        "type": "festival",
        "name": "Evenemententerrein Biddinghuizen (Lowlands & Defqon.1)",
        "city": "Biddinghuizen",
        "capacity": 65000,
        "lat": 52.4412,
        "lon": 5.7512,
        "description": "Legendarisch festivalterrein van Lowlands, Defqon.1 Weekend Festival en Walibi Holland.",
        "url": "https://lowlands.nl"
    },
    {
        "id": "FEST-PINKPOP",
        "type": "festival",
        "name": "Megaland Landgraaf (Pinkpop)",
        "city": "Landgraaf",
        "capacity": 70000,
        "lat": 50.8845,
        "lon": 6.0215,
        "description": "Oudste onafgebroken popfestival ter wereld (sinds 1970).",
        "url": "https://pinkpop.nl"
    },
    {
        "id": "FEST-MYSTERYLAND",
        "type": "festival",
        "name": "Voormalig Floriadeterrein (Mysteryland)",
        "city": "Haarlemmermeer",
        "capacity": 100000,
        "lat": 52.3485,
        "lon": 4.6985,
        "description": "Toonaangevend festivalterrein voor electronic music en kunstinstallaties.",
        "url": "https://mysteryland.nl"
    },
    {
        "id": "FEST-AWAKENINGS",
        "type": "festival",
        "name": "Spaarnwoude Park (Awakenings & Dance Valley)",
        "city": "Velsen / Haarlem",
        "capacity": 80000,
        "lat": 52.4215,
        "lon": 4.6912,
        "description": "Icoon voor techno en outdoor dancefestivals.",
        "url": "https://awakenings.com"
    },
    {
        "id": "FEST-BKS",
        "type": "festival",
        "name": "Beekse Bergen (Best Kept Secret & Decibel)",
        "city": "Hilvarenbeek",
        "capacity": 45000,
        "lat": 51.5215,
        "lon": 5.1285,
        "description": "Festival aan het meer omringd door safari en bos.",
        "url": "https://bestkeptsecret.nl"
    },
    {
        "id": "FEST-ZWARTECROSS",
        "type": "festival",
        "name": "De Schans Lichtenvoorde (Zwarte Cross)",
        "city": "Lichtenvoorde",
        "capacity": 220000,
        "lat": 51.9815,
        "lon": 6.5712,
        "description": "Grootste betaalde festival van Nederland: motorcross, muziek en spektakel.",
        "url": "https://zwartecross.nl"
    },
    {
        "id": "FEST-TOMORROWLAND",
        "type": "festival",
        "name": "De Schorre Boom (Tomorrowland)",
        "city": "Boom, België",
        "capacity": 400000,
        "lat": 51.0915,
        "lon": 4.3785,
        "description": "Grootste dancefestival ter wereld met magische decors.",
        "url": "https://tomorrowland.com"
    },
    {
        "id": "FEST-GLASTONBURY",
        "type": "festival",
        "name": "Worthy Farm (Glastonbury Festival)",
        "city": "Pilton, Somerset, UK",
        "capacity": 210000,
        "lat": 51.1551,
        "lon": -2.5855,
        "description": "Wereldberoemd muziek- en podiumkunstenfestival.",
        "url": "https://glastonburyfestivals.co.uk"
    },
    # Concert Arenas
    {
        "id": "VENUE-ZIGGODOME",
        "type": "venue",
        "name": "Ziggo Dome",
        "city": "Amsterdam",
        "capacity": 17000,
        "lat": 52.3135,
        "lon": 4.9368,
        "description": "Concertzaal voor internationale topartiesten.",
        "url": "https://ziggodome.nl"
    },
    {
        "id": "VENUE-ARENA",
        "type": "venue",
        "name": "Johan Cruijff ArenA",
        "city": "Amsterdam",
        "capacity": 55000,
        "lat": 52.3144,
        "lon": 4.9419,
        "description": "Stadionconcerten van wereldsterren.",
        "url": "https://johancruijffarena.nl"
    },
    {
        "id": "VENUE-AHOY",
        "type": "venue",
        "name": "Rotterdam Ahoy",
        "city": "Rotterdam",
        "capacity": 16400,
        "lat": 51.8831,
        "lon": 4.4885,
        "description": "Evenementencomplex en concertarena.",
        "url": "https://ahoy.nl"
    },
    # Pokemon GO Hotspots & Live Events
    {
        "id": "POGO-VONDELPARK",
        "type": "pokemon_go",
        "name": "Vondelpark Pokémon GO Hub",
        "city": "Amsterdam",
        "lat": 52.3585,
        "lon": 4.8685,
        "description": "Hoogste dichtheid van PokéStops, gyms en lures in Nederland. Vaste verzamelplek voor Community Day en Raid Hours.",
        "url": "https://pokemongolive.com"
    },
    {
        "id": "POGO-MUSEUMPLEIN",
        "type": "pokemon_go",
        "name": "Museumplein Gym Cluster",
        "city": "Amsterdam",
        "lat": 52.3581,
        "lon": 4.8812,
        "description": "Vaste raid-hotspot voor Legendary Raids bij het Rijksmuseum en Van Gogh.",
        "url": "https://pokemongolive.com"
    },
    {
        "id": "POGO-ZUIDERPARK",
        "type": "pokemon_go",
        "name": "Zuiderpark Nest & Safari Hotspot",
        "city": "Den Haag",
        "lat": 52.0585,
        "lon": 4.2912,
        "description": "Groot nestpark met tientallen gyms en actieve Pokémon GO community raids.",
        "url": "https://pokemongolive.com"
    },
    {
        "id": "POGO-WILHELMINAPARK",
        "type": "pokemon_go",
        "name": "Wilhelminapark Lure Hub",
        "city": "Utrecht",
        "lat": 52.0865,
        "lon": 5.1385,
        "description": "Populair park voor Pokémon GO evenementen en community meetings.",
        "url": "https://pokemongolive.com"
    }
]

# 3. WATER QUALITY & SWIMMING LAKES (zwemwater.nl open data)
water_health_data = [
    {
        "id": "WATER-SLOTERPLAS",
        "name": "Sloterplas Zwemstrand",
        "water_body": "Sloterplas",
        "city": "Amsterdam",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Geen blauwalgen geconstateerd",
        "temp_c": 19.4,
        "lat": 52.3652,
        "lon": 4.8215,
        "facilities": "Zandstrand, toezicht, horeca, douches",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-GAASPERPLAS",
        "name": "Gaasperplas Noordzijde",
        "water_body": "Gaasperplas",
        "city": "Amsterdam Zuidoost",
        "quality": "Goed",
        "status_code": "good",
        "algae_risk": "Laag",
        "temp_c": 19.8,
        "lat": 52.3115,
        "lon": 4.9985,
        "facilities": "Grote ligweide, zandstrand, watersportverhuur",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-KRALINGEN",
        "name": "Kralingse Plas Strandbad",
        "water_body": "Kralingse Plas",
        "city": "Rotterdam",
        "quality": "Aanvaardbaar",
        "status_code": "warning",
        "algae_risk": "Incidenteel lichte blauwalgontwikkeling bij hitte",
        "temp_c": 20.1,
        "lat": 51.9352,
        "lon": 4.5125,
        "facilities": "Zandstrand, peuterbad, horeca, toezicht",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-HAARRIJN",
        "name": "Haarrijnseplas Strand",
        "water_body": "Haarrijnseplas",
        "city": "Utrecht",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Geen blauwalgen",
        "temp_c": 19.2,
        "lat": 52.1285,
        "lon": 4.9982,
        "facilities": "Schoon diep water, strandpaviljoen Key West, toezicht",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-LOOSDRECHT",
        "name": "Loosdrechtse Plassen (Strook)",
        "water_body": "Loosdrechtse Plassen",
        "city": "Wijdemeren",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Geen risico",
        "temp_c": 20.4,
        "lat": 52.1985,
        "lon": 5.0785,
        "facilities": "Zwemsteigers, zeilbootverhuur, jachthavens",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-VINKEVEEN",
        "name": "Vinkeveense Plassen (Zandeiland 4)",
        "water_body": "Vinkeveense Plassen",
        "city": "De Ronde Venen",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Helder veen- en grondwater, geen blauwalg",
        "temp_c": 19.6,
        "lat": 52.2352,
        "lon": 4.9485,
        "facilities": "Duiklocatie, zandeilanden, jachthavens",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-IJSSELMEER",
        "name": "Enkhuizen Enkhuizerzand",
        "water_body": "IJsselmeer",
        "city": "Enkhuizen",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Veilig zoet zwemwater",
        "temp_c": 18.9,
        "lat": 52.7085,
        "lon": 5.2985,
        "facilities": "Breed zandstrand, surflocatie",
        "url": "https://www.zwemwater.nl"
    },
    {
        "id": "WATER-VEERSEMEER",
        "name": "Veerse Meer (De Schotsman)",
        "water_body": "Veerse Meer",
        "city": "Kamperland, Zeeland",
        "quality": "Uitstekend",
        "status_code": "good",
        "algae_risk": "Brak zilt water, geen blauwalgen",
        "temp_c": 19.0,
        "lat": 51.5785,
        "lon": 3.6512,
        "facilities": "Waterskibaan, zeilschool, strand",
        "url": "https://www.zwemwater.nl"
    }
]

# 4. RADIO STATIONS WITH DIRECT AUDIO STREAMS
radio_stations_data = [
    {
        "id": "RADIO-NPO1",
        "name": "NPO Radio 1",
        "frequency": "98.9 FM / DAB+",
        "genre": "Nieuws, Achtergronden & Sport",
        "stream_url": "https://icecast.omroep.nl/radio1-bb-mp3",
        "transmitter": "Lopik (Gerbrandytoren)",
        "power_kw": 100,
        "lat": 52.0115,
        "lon": 5.0538
    },
    {
        "id": "RADIO-NPO2",
        "name": "NPO Radio 2",
        "frequency": "92.6 FM / DAB+",
        "genre": "Pop, Rock & Top 2000",
        "stream_url": "https://icecast.omroep.nl/radio2-bb-mp3",
        "transmitter": "Lopik (Gerbrandytoren)",
        "power_kw": 100,
        "lat": 52.0115,
        "lon": 5.0538
    },
    {
        "id": "RADIO-3FM",
        "name": "NPO 3FM",
        "frequency": "96.8 FM / DAB+",
        "genre": "Alternative & Pop",
        "stream_url": "https://icecast.omroep.nl/3fm-bb-mp3",
        "transmitter": "Lopik (Gerbrandytoren)",
        "power_kw": 100,
        "lat": 52.0115,
        "lon": 5.0538
    },
    {
        "id": "RADIO-538",
        "name": "Radio 538",
        "frequency": "102.1 FM / DAB+",
        "genre": "Hits, Dance & Top 40",
        "stream_url": "https://stream.talparadio.nl/538/mp3",
        "transmitter": "Hilversum",
        "power_kw": 50,
        "lat": 52.2351,
        "lon": 5.1785
    },
    {
        "id": "RADIO-QMUSIC",
        "name": "Qmusic Nederland",
        "frequency": "100.4 FM / DAB+",
        "genre": "Pop & Foute Uur",
        "stream_url": "https://stream.qmusic.nl/qmusic/mp3",
        "transmitter": "Amsterdam",
        "power_kw": 80,
        "lat": 52.3385,
        "lon": 4.9285
    },
    {
        "id": "RADIO-SKY",
        "name": "Sky Radio",
        "frequency": "101.2 FM / DAB+",
        "genre": "Non-stop Hits & Pop",
        "stream_url": "https://stream.talparadio.nl/skyradio/mp3",
        "transmitter": "Lopik",
        "power_kw": 100,
        "lat": 52.0115,
        "lon": 5.0538
    },
    {
        "id": "RADIO-SLAM",
        "name": "SLAM!",
        "frequency": "DAB+ / Online",
        "genre": "EDM, Dance & Club",
        "stream_url": "https://stream.slam.nl/slam-mp3",
        "transmitter": "Naarden",
        "power_kw": 25,
        "lat": 52.2985,
        "lon": 5.1612
    },
    {
        "id": "RADIO-STU BRU",
        "name": "Studio Brussel",
        "frequency": "100.9 FM / DAB+",
        "genre": "Alternative & Rock (België)",
        "stream_url": "https://icecast.vrtcdn.be/stubru-high.mp3",
        "transmitter": "Brussel / Schoten",
        "power_kw": 50,
        "lat": 51.2685,
        "lon": 4.5125
    },
    {
        "id": "RADIO-BBC1",
        "name": "BBC Radio 1",
        "frequency": "97-99 FM UK / Online",
        "genre": "Current UK Pop & Electronic",
        "stream_url": "https://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
        "transmitter": "London Crystal Palace",
        "power_kw": 250,
        "lat": 51.4242,
        "lon": -0.0752
    },
    {
        "id": "RADIO-SOMAFM",
        "name": "SomaFM: Groove Salad",
        "frequency": "Worldwide Ambient / Downtempo",
        "genre": "Ambient & Chillout",
        "stream_url": "https://ice1.somafm.com/groovesalad-128-mp3",
        "transmitter": "San Francisco, CA",
        "power_kw": 0,
        "lat": 37.7749,
        "lon": -122.4194
    }
]

# 5. CIVIC LOCAL (Afvalkalender, Weekmarkten, Politiebureaus)
civic_local_data = {
    "municipalities": [
        {
            "name": "Gemeente Amsterdam",
            "city": "Amsterdam",
            "phone": "14020",
            "office_lat": 52.3675,
            "office_lon": 4.9015,
            "afval_schema": {
                "restafval": "Ondergrondse containers 24/7 met afvalpas",
                "papier": "Woensdag (karton & papier)",
                "gft": "Vrijdag",
                "grofvuil": "Op afspraak of vaste inzameldag per buurt"
            },
            "markten": [
                {"name": "Albert Cuypmarkt", "days": "Maandag t/m Zaterdag 09:30-17:00", "lat": 52.3558, "lon": 4.8942, "type": "Algemene dagmarkt (260 kramen)"},
                {"name": "Dappermarkt", "days": "Maandag t/m Zaterdag 09:00-17:00", "lat": 52.3615, "lon": 4.9282, "type": "Wereldmarkt"},
                {"name": "Noordermarkt", "days": "Maandag (vintage) & Zaterdag (biologische boerenmarkt)", "lat": 52.3795, "lon": 4.8865, "type": "Biologisch & Antiek"}
            ],
            "police_stations": [
                {"name": "Politiebureau Nieuwezijds Voorburgwal", "address": "Nieuwezijds Voorburgwal 104", "phone": "0900-8844", "lat": 52.3735, "lon": 4.8912},
                {"name": "Politiebureau Linnaeusstraat", "address": "Linnaeusstraat 221", "phone": "0900-8844", "lat": 52.3552, "lon": 4.9285},
                {"name": "Politiebureau Flierbosdreef Zuidoost", "address": "Flierbosdreef 1", "phone": "0900-8844", "lat": 52.3165, "lon": 4.9721}
            ]
        },
        {
            "name": "Gemeente Rotterdam",
            "city": "Rotterdam",
            "phone": "14010",
            "office_lat": 51.9225,
            "office_lon": 4.4792,
            "afval_schema": {
                "restafval": "Ondergrondse restafvalcontainers",
                "papier": "Donderdag",
                "gft": "Dinsdag",
                "grofvuil": "Gratis inleveren milieupark of ophaalafspraak"
            },
            "markten": [
                {"name": "Binnenrotte Centrummarkt", "days": "Dinsdag & Zaterdag 08:00-17:30", "lat": 51.9205, "lon": 4.4885, "type": "Grootste warenmarkt van Nederland (400 kramen)"},
                {"name": "Markthal Rotterdam", "days": "Dagelijks 10:00-20:00", "lat": 51.9201, "lon": 4.4871, "type": "Overdekte food- en versmarkt"}
            ],
            "police_stations": [
                {"name": "Hoofdbureau Politie Doelwater", "address": "Doelwater 5", "phone": "0900-8844", "lat": 51.9235, "lon": 4.4785},
                {"name": "Politiebureau Zuidplein", "address": "Zuidplein 111", "phone": "0900-8844", "lat": 51.8862, "lon": 4.4895}
            ]
        },
        {
            "name": "Gemeente Utrecht",
            "city": "Utrecht",
            "phone": "14030",
            "office_lat": 52.0902,
            "office_lon": 5.1219,
            "afval_schema": {
                "restafval": "Ondergronds / tweewekelijks kliko",
                "papier": "Dinsdag (even weken)",
                "gft": "Vrijdag",
                "grofvuil": "Meldpunt openbare ruimte of afvalscheidingsstation"
            },
            "markten": [
                {"name": "Vredenburg Warenmarkt", "days": "Woensdag, Vrijdag & Zaterdag 10:00-17:00", "lat": 52.0915, "lon": 5.1145, "type": "Kleding, vis, kaas & bloemen"},
                {"name": "Bloemenmarkt Janskerkhof", "days": "Zaterdag 08:00-17:00", "lat": 52.0935, "lon": 5.1221, "type": "Grootste bloemen- en plantenmarkt"}
            ],
            "police_stations": [
                {"name": "Politiebureau Kroonstraat (Centrum)", "address": "Kroonstraat 25", "phone": "0900-8844", "lat": 52.0945, "lon": 5.1121},
                {"name": "Politiebureau Paardenveld", "address": "Paardenveld 1", "phone": "0900-8844", "lat": 52.0965, "lon": 5.1115}
            ]
        },
        {
            "name": "Gemeente Den Haag",
            "city": "Den Haag",
            "phone": "14070",
            "office_lat": 52.0785,
            "office_lon": 4.3185,
            "afval_schema": {
                "restafval": "Ondergrondse restafvalcontainers",
                "papier": "Maandag",
                "gft": "Donderdag",
                "grofvuil": "Gratis ophaalafspraak via denhaag.nl"
            },
            "markten": [
                {"name": "De Haagse Markt", "days": "Maandag, Woensdag, Vrijdag, Zaterdag 09:00-17:00", "lat": 52.0612, "lon": 4.2985, "type": "Grootste onoverdekte markt van Europa (500 kramen)"}
            ],
            "police_stations": [
                {"name": "Hoofdbureau Jan Hendrikstraat", "address": "Jan Hendrikstraat 10", "phone": "0900-8844", "lat": 52.0775, "lon": 4.3075}
            ]
        }
    ]
}

# 6. SPORTS & RECREATION (Pools, Darts, Ski, Skydive, Sailing)
sports_recreation_data = [
    # Pools
    {"id": "POOL-01", "type": "pool", "name": "De Mirandabad", "city": "Amsterdam", "lat": 52.3385, "lon": 4.8992, "description": "Subtropisch golfslagbad, 50m buitenbad en wedstrijdbad."},
    {"id": "POOL-02", "type": "pool", "name": "Noorderparkbad", "city": "Amsterdam Noord", "lat": 52.3912, "lon": 4.9185, "description": "Duurzaamste zwembad van Europa met binnen- en buitenbaden."},
    {"id": "POOL-03", "type": "pool", "name": "Zwemcentrum Rotterdam", "city": "Rotterdam Zuid", "lat": 51.8845, "lon": 4.4912, "description": "Olympisch 50m topsportzwembad."},
    {"id": "POOL-04", "type": "pool", "name": "Zwembad Den Hommel", "city": "Utrecht", "lat": 52.0845, "lon": 5.0921, "description": "Groot wedstrijdbad, recreatiebad en glijbaan."},
    # Darts
    {"id": "DART-01", "type": "darts", "name": "Café De Vrijbuiter Darts Arena", "city": "Nijmegen", "lat": 51.8385, "lon": 5.8612, "description": "Legendarische dartslocatie van Nederlandse kampioenen (o.a. Raymond van Barneveld & Michael van Gerwen)."},
    {"id": "DART-02", "type": "darts", "name": "Dartcenter De Schakel", "city": "Vlaardingen", "lat": 51.9125, "lon": 4.3412, "description": "Regionaal dartscompetitie centrum met 18 professionele banen."},
    # Indoor Ski
    {"id": "SKI-01", "type": "ski", "name": "SnowWorld Landgraaf", "city": "Landgraaf", "lat": 50.8712, "lon": 6.0185, "description": "Grootste overdekte wintersportresort ter wereld met 5 pistes en FIS-afdaling."},
    {"id": "SKI-02", "type": "ski", "name": "SnowWorld Zoetermeer", "city": "Zoetermeer", "lat": 52.0612, "lon": 4.4685, "description": "Steilste overdekte piste van Europa (20% hellingspercentage)."},
    {"id": "SKI-03", "type": "ski", "name": "Val Thorens (Les 3 Vallées)", "city": "Savoie, Frankrijk", "lat": 45.2985, "lon": 6.5812, "description": "Hoogstgelegen skiresort van Europa (2300m - 3200m)."},
    # Skydive Dropzones
    {"id": "SKY-01", "type": "skydive", "name": "National Paracentrum Teuge", "city": "Teuge (nabij Apeldoorn)", "lat": 52.2415, "lon": 6.0485, "description": "Grootste parachutespringcentrum van Nederland. Tandemsprongen vanaf 12.000 ft."},
    {"id": "SKY-02", "type": "skydive", "name": "Paracentrum Texel", "city": "De Cocksdorp, Texel", "lat": 53.1185, "lon": 4.8312, "description": "Skydive boven het waddengebied en de Noordzeekust."},
    {"id": "SKY-03", "type": "skydive", "name": "Skydive Breda (Seppe Airport)", "city": "Breda International Airport", "lat": 51.5585, "lon": 4.5512, "description": "Tandemsprongen en vrije val opleidingen."},
    # Sailing & Marinas
    {"id": "SAIL-01", "type": "sail", "name": "Koninklijke Nederlandsche Zeil- & Roeivereeniging", "city": "Muiden", "lat": 52.3312, "lon": 5.0685, "description": "Historische jachthaven bij het Muiderslot met directe toegang tot het IJmeer."},
    {"id": "SAIL-02", "type": "sail", "name": "Compagnieshaven Enkhuizen", "city": "Enkhuizen", "lat": 52.7015, "lon": 5.2912, "description": "Toonaangevende jachthaven aan het IJsselmeer met 700 ligplaatsen."},
    {"id": "SAIL-03", "type": "sail", "name": "Jachthaven Sneekerhof", "city": "Sneek (Sneekermeer)", "lat": 53.0312, "lon": 5.7185, "description": "Hart van de Friese zeilsport en de Sneekweek."}
]

# 7. HOUSING MARKET (m² prijzen, WOZ trends, Funda links)
housemarket_data = [
    {"city": "Amsterdam", "avg_m2_eur": 7850, "avg_woz_eur": 512000, "market_status": "Overspannen verkopersmarkt", "trend_pct": 5.8, "lat": 52.3675, "lon": 4.9015, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22amsterdam%22%5D"},
    {"city": "Utrecht", "avg_m2_eur": 5420, "avg_woz_eur": 448000, "market_status": "Sterk concurrerend", "trend_pct": 6.2, "lat": 52.0902, "lon": 5.1219, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22utrecht%22%5D"},
    {"city": "Rotterdam", "avg_m2_eur": 4650, "avg_woz_eur": 365000, "market_status": "Gematigd stijgend", "trend_pct": 4.5, "lat": 51.9225, "lon": 4.4792, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22rotterdam%22%5D"},
    {"city": "Den Haag", "avg_m2_eur": 4500, "avg_woz_eur": 372000, "market_status": "Actieve markt", "trend_pct": 4.8, "lat": 52.0785, "lon": 4.3185, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22den-haag%22%5D"},
    {"city": "Eindhoven", "avg_m2_eur": 4250, "avg_woz_eur": 395000, "market_status": "Hoge vraag door Brainport tech", "trend_pct": 7.1, "lat": 51.4412, "lon": 5.4692, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22eindhoven%22%5D"},
    {"city": "Groningen", "avg_m2_eur": 3600, "avg_woz_eur": 298000, "market_status": "Stabiele studenten- en gezinsmarkt", "trend_pct": 4.2, "lat": 53.2192, "lon": 6.5662, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22groningen%22%5D"},
    {"city": "Haarlem", "avg_m2_eur": 5850, "avg_woz_eur": 485000, "market_status": "Zeer populair als alternatief voor Amsterdam", "trend_pct": 5.5, "lat": 52.3812, "lon": 4.6385, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22haarlem%22%5D"},
    {"city": "Almere", "avg_m2_eur": 3750, "avg_woz_eur": 382000, "market_status": "Veel eengezinswoningen, snelle doorloop", "trend_pct": 5.1, "lat": 52.3702, "lon": 5.2142, "funda_url": "https://www.funda.nl/zoeken/koop?selected_area=%5B%22almere%22%5D"}
]

# 8. COMPANIES & TECH CAMPUSES
companies_data = [
    {
        "name": "ASML Wereldwijde Campus",
        "industry": "Semiconductors & Lithografie",
        "city": "Veldhoven",
        "employees": 42000,
        "lat": 51.4085,
        "lon": 5.4185,
        "website": "https://www.asml.com",
        "description": "Exclusieve producent van geavanceerde EUV-lithografiemachines voor de wereldwijde chipindustrie."
    },
    {
        "name": "High Tech Campus Eindhoven (HTCE)",
        "industry": "Tech R&D & AI Ecosystem",
        "city": "Eindhoven",
        "employees": 12500,
        "lat": 51.4112,
        "lon": 5.4612,
        "website": "https://www.hightechcampus.com",
        "description": "Slimste vierkante kilometer van Europa: Philips, NXP, Intel, Shimano en 280 techbedrijven."
    },
    {
        "name": "Booking.com Global Headquarters",
        "industry": "Travel Tech & E-Commerce",
        "city": "Amsterdam Oosterdokseiland",
        "employees": 6000,
        "lat": 52.3762,
        "lon": 4.9085,
        "website": "https://www.booking.com",
        "description": "Hoofdkantoor van het wereldwijde online reisplatform."
    },
    {
        "name": "Adyen Global Headquarters",
        "industry": "Fintech & Global Payments",
        "city": "Amsterdam Rokin",
        "employees": 4000,
        "lat": 52.3685,
        "lon": 4.8912,
        "website": "https://www.adyen.com",
        "description": "Wereldwijd betalingsplatform voor Meta, Uber, Spotify en Microsoft."
    },
    {
        "name": "Havenbedrijf Rotterdam (World Port Center)",
        "industry": "Maritieme Logistiek & Energiehub",
        "city": "Rotterdam Wilhelminapier",
        "employees": 1300,
        "lat": 51.9052,
        "lon": 4.4852,
        "website": "https://www.portofrotterdam.com",
        "description": "Grootste zeehaven van Europa, overslag van 440 miljoen ton goederen per jaar."
    },
    {
        "name": "ESA ESTEC Space Tech Centre",
        "industry": "Ruimtevaart & Satellietontwikkeling",
        "city": "Noordwijk",
        "employees": 2800,
        "lat": 52.2185,
        "lon": 4.4215,
        "website": "https://www.esa.int",
        "description": "Grootste faciliteit van de Europese Ruimtevaartorganisatie (ESA)."
    }
]

# 9. VACATION CRUISE LINES & TERMINALS
cruises_data = [
    {
        "name": "Passenger Terminal Amsterdam (PTA)",
        "type": "terminal",
        "city": "Amsterdam",
        "lat": 52.3775,
        "lon": 4.9185,
        "capacity": "350.000 passagiers/jaar",
        "description": "Centrale cruiseterminal aan het IJ voor oceaancruiseschepen en riviercruises.",
        "url": "https://www.ptamsterdam.nl"
    },
    {
        "name": "Cruise Port Rotterdam",
        "type": "terminal",
        "city": "Rotterdam Wilhelminapier",
        "lat": 51.9035,
        "lon": 4.4851,
        "capacity": "Aanlegplaats voor schepen tot 360m",
        "description": "Historische vertreklocatie van de Holland-Amerika Lijn (HAL).",
        "url": "https://www.cruiseportrotterdam.com"
    },
    {
        "name": "Rotterdam (Holland America Line)",
        "type": "ship",
        "operator": "Holland America Line",
        "passengers": 2668,
        "route": "Noorse Fjorden & Baltische Staten",
        "lat": 54.2185,
        "lon": 5.6512,
        "status": "Op open zee (19.4 knopen, koers 020°)"
    },
    {
        "name": "MSC Euribia",
        "type": "ship",
        "operator": "MSC Cruises",
        "passengers": 6334,
        "route": "West-Europa Metropolen & Noordzee",
        "lat": 52.8512,
        "lon": 3.4215,
        "status": "Onderweg naar Rotterdam (18.1 knopen)"
    }
]

# 10. RELIGION & RITUALS (Sacred heritage & pilgrim routes)
religion_rituals_data = [
    {
        "name": "Pieterpad Pelgrims- & Wandelroute",
        "type": "pilgrim_way",
        "distance_km": 500,
        "start": "Pieterburen (Groningen)",
        "end": "Sint-Pietersberg (Maastricht)",
        "coords": [
            [53.4012, 6.4512], [53.2195, 6.5662], [52.9912, 6.5612],
            [52.6812, 6.7812], [52.3512, 6.6512], [52.0112, 6.3212],
            [51.8412, 5.8612], [51.5212, 6.0812], [50.8352, 5.6912]
        ],
        "description": "Bekendste lange-afstandswandelpad en hedendaagse pelgrimsroute van Nederland."
    },
    {
        "name": "Sint-Janskathedraal",
        "type": "cathedral",
        "city": "'s-Hertogenbosch",
        "lat": 51.6885,
        "lon": 5.3085,
        "description": "Hoogtepunt van de Brabantse gotiek met de befaamde Zoete Moeder van Den Bosch."
    },
    {
        "name": "Domkerk & Domtoren",
        "type": "cathedral",
        "city": "Utrecht",
        "lat": 52.0908,
        "lon": 5.1215,
        "description": "Historisch hart van kerkelijk Nederland met de hoogste kerktoren van het land (112m)."
    },
    {
        "name": "Westerkerk",
        "type": "church",
        "city": "Amsterdam",
        "lat": 52.3745,
        "lon": 4.8835,
        "description": "Beroemde kerk aan de Prinsengracht naast het Anne Frank Huis, begraafplaats van Rembrandt."
    },
    {
        "name": "Ulu Moskee Utrecht",
        "type": "mosque",
        "city": "Utrecht Lombok",
        "lat": 52.0915,
        "lon": 5.1012,
        "description": "Moderne islamitische gebedsruimte met een glazen minaret en interreligieuze ontmoetingsruimte."
    },
    {
        "name": "Portugese Synagoge (Esnoga)",
        "type": "synagogue",
        "city": "Amsterdam",
        "lat": 52.3672,
        "lon": 4.9045,
        "description": "17e-eeuwse monumentale synagoge, verlicht met duizend kaarsen."
    },
    {
        "name": "Fo Guang Shan He Hua Tempel",
        "type": "temple",
        "city": "Amsterdam Zeedijk",
        "lat": 52.3735,
        "lon": 4.9012,
        "description": "Grootste boeddhistische tempel in traditionele Chinese paleisstijl in Europa."
    }
]

# Write all to DATA_DIR
files = [
    ("trams.json", trams_data),
    ("festivals-events.json", festivals_data),
    ("water-health.json", water_health_data),
    ("radio-stations.json", radio_stations_data),
    ("civic-local.json", civic_local_data),
    ("sports-recreation.json", sports_recreation_data),
    ("housemarket.json", housemarket_data),
    ("companies.json", companies_data),
    ("cruises.json", cruises_data),
    ("religion-rituals.json", religion_rituals_data),
]

for fname, payload in files:
    out_path = DATA_DIR / fname
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Generated {fname} ({out_path.stat().st_size:,} bytes)")
