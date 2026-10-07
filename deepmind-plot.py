# ============================================================
# DeepMind Weather Lab Ensemble Cyclone -> KML
# ============================================================

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import StringIO
from xml.sax.saxutils import escape


# ============================================================
# SETTINGS
# ============================================================

MODEL = "FNV3P2"

RAW_DIR = "../../data/raw"
OUTPUT_DIR = "../../data/output"

raw_file = os.path.join(RAW_DIR, "deepmind.csv")
kml_file = os.path.join(OUTPUT_DIR, "deepmind.kml")


# ============================================================
# INTENSITY COLORS
# ============================================================

INTENSITY_COLORS = [
    (34,  (150, 232, 251)),   # TD: <34 kt
    (64,  (45, 242, 75)),     # TS: 34–63 kt
    (83,  (255, 255, 18)),    # CAT 1: 64–82 kt
    (96,  (255, 139, 17)),    # CAT 2: 83–95 kt
    (113, (255, 0, 0)),       # CAT 3: 96–112 kt
    (137, (255, 15, 255)),    # CAT 4: 113–136 kt
    (9999, (249, 190, 255)),  # CAT 5: 137+ kt
]


def get_intensity_color(wind):
    """Return RGB color based on wind speed in knots."""

    if pd.isna(wind):
        return (160, 160, 160)

    wind = float(wind)

    for upper_limit, color in INTENSITY_COLORS:

        if wind < upper_limit:
            return color

    return (255, 96, 255)


# ============================================================
# KML COLOR CONVERSION
# ============================================================

def kml_color(rgb, opacity=1.0):
    """
    Convert RGB tuple to KML AABBGGRR format.
    """

    r, g, b = rgb

    alpha = int(opacity * 255)

    return f"{alpha:02x}{b:02x}{g:02x}{r:02x}"


# ============================================================
# BUILD WEATHER LAB URL
# ============================================================

def build_url(date_string, cycle):

    year = date_string[0:4]
    month = date_string[4:6]
    day = date_string[6:8]

    return (
        f"https://deepmind.google.com/science/weatherlab/download/"
        f"cyclones/{MODEL}/ensemble/paired/csv/"
        f"{MODEL}_{year}_{month}_{day}T{cycle}_00_paired.csv"
    )


# ============================================================
# DATELINE HANDLING
# ============================================================

def split_segment(lon1, lat1, lon2, lat2):
    """
    Split a line if it crosses the international dateline.
    """

    def line_string(points):

        coordinates = " ".join(
            f"{lon:.2f},{lat:.2f},0"
            for lon, lat in points
        )

        return (
            "<LineString>"
            "<tessellate>1</tessellate>"
            f"<coordinates>{coordinates}</coordinates>"
            "</LineString>"
        )

    if abs(lon2 - lon1) <= 180:

        return line_string([
            (lon1, lat1),
            (lon2, lat2)
        ])

    edge = 180 if lon1 > 0 else -180

    lon2_adjusted = (
        lon2 + 360
        if lon2 < lon1
        else lon2 - 360
    )

    fraction = (
        (edge - lon1)
        / (lon2_adjusted - lon1)
    )

    lat_cross = (
        lat1
        + fraction * (lat2 - lat1)
    )

    return (
        line_string([
            (lon1, lat1),
            (edge, lat_cross)
        ])
        +
        line_string([
            (-edge, lat_cross),
            (lon2, lat2)
        ])
    )


# ============================================================
# DETERMINE RUNS TO CHECK
# ============================================================

today = datetime.now().date()

tomorrow = today + timedelta(days=1)

today_string = today.strftime("%Y%m%d")
tomorrow_string = tomorrow.strftime("%Y%m%d")


# Newest first:
# Tomorrow 00Z
# Today 18Z
# Today 12Z
# Today 06Z
# Today 00Z

runs_to_check = [
    (tomorrow_string, "00"),
    (today_string, "18"),
    (today_string, "12"),
    (today_string, "06"),
    (today_string, "00"),
]


# ============================================================
# CHECK AVAILABLE WEATHER LAB RUNS
# ============================================================

print()
print("============================================================")
print("DEEP MIND WEATHER LAB")
print("============================================================")
print()
print(f"Model: {MODEL}")
print()

available_runs = []

for date_string, cycle in runs_to_check:

    url = build_url(
        date_string,
        cycle
    )

    display_date = (
        f"{date_string[0:4]}-"
        f"{date_string[4:6]}-"
        f"{date_string[6:8]}"
    )

    print(
        f"Checking {display_date} {cycle}Z..."
    )

    try:

        response = requests.get(
            url,
            timeout=60
        )

        if response.status_code != 200:

            print(
                f"  Not available "
                f"(HTTP {response.status_code})"
            )

            continue

        df = pd.read_csv(
            StringIO(response.text),
            comment="#"
        )

        available_runs.append(
            {
                "date": date_string,
                "cycle": cycle,
                "display_date": display_date,
                "url": url,
                "data": df
            }
        )

        storm_count = df["track_id"].nunique()

        print(
            f"  Available — "
            f"{storm_count} cyclone(s)"
        )

    except requests.RequestException as e:

        print(f"  Download error: {e}")

    except Exception as e:

        print(f"  Error reading data: {e}")


# ============================================================
# CHECK FOR AVAILABLE RUNS
# ============================================================

if not available_runs:

    print()
    print("============================================================")
    print("NO WEATHER LAB DATA FOUND")
    print("============================================================")
    raise SystemExit


# ============================================================
# SELECT MODEL RUN
# ============================================================

print()
print("============================================================")
print("AVAILABLE MODEL RUNS")
print("============================================================")
print()

for i, run in enumerate(
    available_runs,
    start=1
):

    print(
        f"{i}. "
        f"{run['display_date']} "
        f"{run['cycle']}Z"
    )

print()

while True:

    try:

        selection = int(
            input("Select model run: ")
        )

        if 1 <= selection <= len(available_runs):
            break

    except ValueError:
        pass

    print(
        f"Please enter a number from "
        f"1 to {len(available_runs)}."
    )


selected_run = available_runs[
    selection - 1
]

df = selected_run["data"]

CYCLE = (
    selected_run["date"]
    + selected_run["cycle"]
)


# ============================================================
# SELECT STORM
# ============================================================

storms = []

for track_id, group in df.groupby("track_id"):

    members = group["sample"].nunique()

    points = len(group)

    first_time = group["valid_time"].min()

    last_time = group["valid_time"].max()

    storms.append(
        {
            "track_id": track_id,
            "members": members,
            "points": points,
            "first_time": first_time,
            "last_time": last_time
        }
    )


storms = sorted(
    storms,
    key=lambda x: x["track_id"]
)


print()
print("============================================================")
print(
    f"CYCLONES IN "
    f"{selected_run['display_date']} "
    f"{selected_run['cycle']}Z"
)
print("============================================================")
print()

print(
    f"{'No.':<5}"
    f"{'Track ID':<15}"
    f"{'Members':>10}"
    f"{'Points':>10}"
)

print("-" * 40)

for i, storm_info in enumerate(
    storms,
    start=1
):

    print(
        f"{i:<5}"
        f"{storm_info['track_id']:<15}"
        f"{storm_info['members']:>10}"
        f"{storm_info['points']:>10}"
    )

print()

while True:

    try:

        selection = int(
            input("Select cyclone: ")
        )

        if 1 <= selection <= len(storms):
            break

    except ValueError:
        pass

    print(
        f"Please enter a number from "
        f"1 to {len(storms)}."
    )


TRACK_ID = storms[
    selection - 1
]["track_id"]


# ============================================================
# SAVE SELECTED RAW DATA
# ============================================================

os.makedirs(
    RAW_DIR,
    exist_ok=True
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

with open(
    raw_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        requests.get(
            selected_run["url"],
            timeout=60
        ).text
    )

print()
print("============================================================")
print("SELECTED DATA")
print("============================================================")
print()
print(f"Cycle:       {CYCLE}")
print(f"Storm:       {TRACK_ID}")
print(f"Raw CSV:     {raw_file}")


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

df["lead_time_hours"] = pd.to_numeric(
    df["lead_time_hours"],
    errors="coerce"
)

df["lat"] = pd.to_numeric(
    df["lat"],
    errors="coerce"
)

df["lon"] = pd.to_numeric(
    df["lon"],
    errors="coerce"
)

df["maximum_sustained_wind_speed_knots"] = pd.to_numeric(
    df["maximum_sustained_wind_speed_knots"],
    errors="coerce"
)


# ============================================================
# SELECT STORM DATA
# ============================================================

storm = df[
    df["track_id"] == TRACK_ID
].copy()

if storm.empty:

    raise ValueError(
        f"No data found for TRACK_ID = {TRACK_ID}"
    )


print(f"Rows:        {len(storm):,}")

print(
    f"Ensembles:   "
    f"{storm['sample'].nunique()}"
)


# ============================================================
# KML HEADER
# ============================================================

kml_parts = []

kml_parts.append(
    '<?xml version="1.0" encoding="UTF-8"?>'
)

kml_parts.append(
    '<kml xmlns="http://www.opengis.net/kml/2.2">'
)

kml_parts.append(
    "<Document>"
)

kml_parts.append(
    f"<name>DeepMind — {escape(TRACK_ID)}</name>"
)


# ============================================================
# CREATE INTENSITY STYLES
# ============================================================

style_colors = {}

for _, color in INTENSITY_COLORS:

    color_name = (
        f"{color[0]:02x}"
        f"{color[1]:02x}"
        f"{color[2]:02x}"
    )

    style_id = (
        f"intensity_{color_name}"
    )

    style_colors[color] = style_id

    kml_parts.append(
        f'<Style id="{style_id}">'
        f'<LineStyle>'
        f'<color>{kml_color(color, 0.75)}</color>'
        f'<width>3.5</width>'
        f'</LineStyle>'
        f'</Style>'
    )


# ============================================================
# MEAN STYLE
# ============================================================

kml_parts.append(
    '<Style id="ensemble_mean">'
    '<LineStyle>'
    '<color>ffffffff</color>'
    '<width>4</width>'
    '</LineStyle>'
    '</Style>'
)


# ============================================================
# ENSEMBLE MEMBER FOLDERS
# ============================================================

samples = sorted(
    storm["sample"].unique()
)

for sample in samples:

    member = storm[
        storm["sample"] == sample
    ].copy()

    member = member.sort_values(
        "lead_time_hours"
    )

    sample_name = str(sample)

    try:

        sample_number = int(
            float(sample_name)
        )

        folder_name = (
            f"Ensemble {sample_number:02d}"
        )

    except ValueError:

        folder_name = (
            f"Ensemble {sample_name}"
        )

    print(
        f"Creating {folder_name}"
    )

    kml_parts.append(
        "<Folder>"
    )

    kml_parts.append(
        f"<name>{escape(folder_name)}</name>"
    )

    rows = member[
        [
            "lead_time_hours",
            "lat",
            "lon",
            "maximum_sustained_wind_speed_knots"
        ]
    ].to_dict("records")

    for i in range(
        len(rows) - 1
    ):

        p1 = rows[i]
        p2 = rows[i + 1]

        if (
            pd.isna(p1["lat"])
            or pd.isna(p1["lon"])
            or pd.isna(p2["lat"])
            or pd.isna(p2["lon"])
        ):

            continue

        lon1 = float(
            p1["lon"]
        )

        lat1 = float(
            p1["lat"]
        )

        lon2 = float(
            p2["lon"]
        )

        lat2 = float(
            p2["lat"]
        )

        # Color segment based on
        # ending point intensity.

        wind = p1[
            "maximum_sustained_wind_speed_knots"
        ]

        color = get_intensity_color(
            wind
        )

        style_id = style_colors[
            color
        ]

        geometry = split_segment(
            lon1,
            lat1,
            lon2,
            lat2
        )

        kml_parts.append(
            "<Placemark>"
        )

        kml_parts.append(
            "<styleUrl>"
            f"#{style_id}"
            "</styleUrl>"
        )

        kml_parts.append(
            geometry
        )

        kml_parts.append(
            "</Placemark>"
        )

    kml_parts.append(
        "</Folder>"
    )


# ============================================================
# ENSEMBLE MEAN
# ============================================================

print(
    "Creating Ensemble Mean"
)

kml_parts.append(
    "<Folder>"
)

kml_parts.append(
    "<name>Ensemble Mean</name>"
)


mean_points = []

for lead_time, group in storm.groupby(
    "lead_time_hours"
):

    group = group.dropna(
        subset=["lat", "lon"]
    )

    if group.empty:
        continue

    mean_lat = group["lat"].mean()

    # Circular mean longitude

    lon_radians = np.radians(
        group["lon"].values
    )

    mean_lon = np.degrees(
        np.arctan2(
            np.mean(
                np.sin(lon_radians)
            ),
            np.mean(
                np.cos(lon_radians)
            )
        )
    )

    mean_points.append(
        {
            "lead_time_hours": lead_time,
            "lat": mean_lat,
            "lon": mean_lon
        }
    )


mean_points = sorted(
    mean_points,
    key=lambda x:
        x["lead_time_hours"]
)


for i in range(
    len(mean_points) - 1
):

    p1 = mean_points[i]
    p2 = mean_points[i + 1]

    geometry = split_segment(
        float(p1["lon"]),
        float(p1["lat"]),
        float(p2["lon"]),
        float(p2["lat"])
    )

    kml_parts.append(
        "<Placemark>"
    )

    kml_parts.append(
        "<styleUrl>"
        "#ensemble_mean"
        "</styleUrl>"
    )

    kml_parts.append(
        geometry
    )

    kml_parts.append(
        "</Placemark>"
    )


kml_parts.append(
    "</Folder>"
)


# ============================================================
# CLOSE KML
# ============================================================

kml_parts.append(
    "</Document>"
)

kml_parts.append(
    "</kml>"
)


# ============================================================
# WRITE KML
# ============================================================

with open(
    kml_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "\n".join(kml_parts)
    )

# ============================================================
# DONE
# ============================================================

print()
print("============================================")
print("DeepMind KML COMPLETE")
print("============================================")
print(f"Cycle:       {CYCLE}")
print(f"Storm:       {TRACK_ID}")
print(f"Ensembles:   {len(samples)}")
print(f"Mean points: {len(mean_points)}")
print()
print(f"Raw CSV:     {raw_file}")
print(f"KML:         {kml_file}")
print("============================================")
