# DeepMind Weather Lab Ensemble Cyclone → KML

Python workflow for downloading **Google DeepMind Weather Lab** ensemble cyclone data and converting an ensemble forecast into a KML file for visualization in Google Earth and other KML-compatible graphics/mapping systems.

The workflow was developed for operational weather visualization, with the goal of making the individual ensemble tracks easy to toggle on/off and making the ensemble mean easy to identify.

---

## What This Does

The workflow has two Python scripts:

### 1. `deepmind.py`

Downloads an available DeepMind Weather Lab ensemble run, allows the user to select a cyclone, and creates a KML containing:

* All available ensemble members
* Individual ensemble-member folders
* Track segments colored by forecast intensity
* An ensemble-mean track
* A separate folder for the ensemble mean
* Dateline-crossing protection

The resulting KML can be opened in Google Earth or imported into a compatible weather graphics/mapping system.

### 2. `modify_deepmind_kml.py`

Provides a simple way to modify the visual appearance of the generated KML without having to manually edit the KML XML.

It allows the user to change:

* Ensemble-member line width
* Ensemble-member transparency
* Ensemble-mean line width
* Ensemble-mean transparency

The script modifies the existing KML in place.

---

# DeepMind Weather Lab Data

The workflow uses the DeepMind Weather Lab cyclone ensemble CSV download.

The URL pattern used by the script is:

```text
https://deepmind.google.com/science/weatherlab/download/cyclones/FNV3P2/ensemble/paired/csv/
```

with a filename corresponding to the model run.

For example:

```text
FNV3P2_2026_10_04T18_00_paired.csv
```

The script automatically checks the newest potential model cycles rather than requiring a run to be manually entered.

---

# Model

The current script uses:

```python
MODEL = "FNV3P2"
```

`FNV3P2` is the Weather Lab model/data product used for the cyclone ensemble tracks in this workflow.

If DeepMind changes the available model or URL structure, the download portion of the script may need to be updated.

---

# How the Download Script Works

The script checks five potential runs:

1. Tomorrow 00Z
2. Today 18Z
3. Today 12Z
4. Today 06Z
5. Today 00Z

It checks whether each CSV is available.

For each available run, it reports the number of cyclone tracks found.

Example:

```text
============================================================
DEEP MIND WEATHER LAB
============================================================

Model: FNV3P2

Checking 2026-10-07 18Z...
  Available — 4 cyclone(s)

Checking 2026-10-07 12Z...
  Available — 4 cyclone(s)

Checking 2026-10-07 06Z...
  Not available (HTTP 404)
```

The user then selects which model run to use.

---

# Selecting a Cyclone

After selecting the model run, the script examines the `track_id` values in the dataset.

It displays:

* Track ID
* Number of ensemble members
* Number of forecast points

Example:

```text
============================================================
CYCLONES IN 2026-10-07 12Z
============================================================

No. Track ID          Members    Points
----------------------------------------
1    AL092026              50       ...
2    EP182026              50       ...
3    WP942026              50       ...
```

The user selects the cyclone to convert to KML.

The selected `track_id` becomes the storm used for the remainder of the process.

---

# Project Structure

The original script was written inside a larger weather-graphics project.

The relevant structure was:

```text
Python_Projects/
│
├── src/
│   └── weather_graphics/
│       ├── deepmind.py
│       └── modify_deepmind_kml.py
│
├── data/
│   ├── raw/
│   │   └── deepmind.csv
│   │
│   └── output/
│       └── deepmind.kml
│
└── ...
```

The scripts use:

```python
RAW_DIR = "../../data/raw"
OUTPUT_DIR = "../../data/output"
```

These are **relative paths** based on the scripts being located in:

```text
src/weather_graphics/
```

If you clone these scripts into a different directory structure, these paths will need to be changed.

For example, you could instead use:

```python
RAW_DIR = "./data/raw"
OUTPUT_DIR = "./data/output"
```

if your scripts and data directories are arranged differently.

---

# Required Python Packages

The main script uses:

```text
requests
pandas
numpy
```

Install them with:

```bash
pip install requests pandas numpy
```

The KML generation itself does not require a specialized KML package. The script builds the KML XML directly.

The second script uses only Python's built-in:

```text
os
re
```

modules.

---

# DeepMind CSV Data

The Weather Lab paired CSV contains information such as:

```text
init_time
track_id
sample
valid_time
lead_time_hours
lat
lon
minimum_slp_hpa
maximum_sustained_wind_speed_knots
...
```

The workflow primarily uses:

* `track_id`
* `sample`
* `valid_time`
* `lead_time_hours`
* `lat`
* `lon`
* `maximum_sustained_wind_speed_knots`

`sample` identifies the individual ensemble member.

---

# Ensemble Tracks

Each ensemble member is placed into its own KML folder.

For example:

```text
Ensemble 00
Ensemble 01
Ensemble 02
...
Ensemble 49
```

This is intentional.

It allows the user to turn individual ensemble members on and off independently in Google Earth or another KML viewer.

The workflow does not create point markers for each forecast position.

Instead, it creates line segments between forecast positions.

---

# Intensity-Based Track Colors

Each ensemble track is divided into line segments.

The segment color is determined from the forecast maximum sustained wind.

The current intensity categories are:

|       Wind | Category            | Color      |
| ---------: | ------------------- | ---------- |
|     <34 kt | Tropical Depression | Light blue |
|   34–63 kt | Tropical Storm      | Green      |
|   64–82 kt | Category 1          | Yellow     |
|   83–95 kt | Category 2          | Orange     |
|  96–112 kt | Category 3          | Red        |
| 113–136 kt | Category 4          | Magenta    |
|    137+ kt | Category 5          | Light pink |

These colors are controlled by:

```python
INTENSITY_COLORS
```

at the top of the script.

For example:

```python
INTENSITY_COLORS = [
    (34,  (150, 232, 251)),
    (64,  (45, 242, 75)),
    (83,  (255, 255, 18)),
    (96,  (255, 139, 17)),
    (113, (255, 0, 0)),
    (137, (255, 15, 255)),
    (9999, (249, 190, 255)),
]
```

The colors are specified as RGB values.

---

# KML Color Format

KML does not use normal RGB notation.

KML uses:

```text
AABBGGRR
```

where:

* `AA` = alpha/transparency
* `BB` = blue
* `GG` = green
* `RR` = red

The script therefore converts normal RGB values using:

```python
def kml_color(rgb, opacity=1.0):
```

This makes it easier to specify colors using normal RGB values while generating the required KML format automatically.

---

# Ensemble Mean

In addition to the individual ensemble members, the script calculates an **ensemble-mean track**.

For each forecast lead time:

1. All available ensemble-member positions are collected.
2. Mean latitude is calculated.
3. Longitude is calculated using a circular mean.
4. The resulting points are connected into a separate track.

The circular longitude calculation is important because simple averaging of longitude can produce incorrect results near the international dateline.

The ensemble mean is placed in its own folder:

```text
Ensemble Mean
```

The mean track is currently:

* White
* Thicker than the ensemble members
* Separate from the individual ensemble folders

This makes it easy to identify the central tendency of the ensemble.

---

# Dateline Handling

The script includes a `split_segment()` function to handle tracks that cross the international dateline.

Without this, a KML line could incorrectly draw a huge line across the map from approximately +180° longitude to -180° longitude.

The function splits the line at the dateline instead.

This is particularly useful because the same workflow can potentially be used for tropical cyclones anywhere in the world.

---

# KML Output

The final file is:

```text
deepmind.kml
```

The basic structure is:

```text
DeepMind — AL092026
│
├── Ensemble 00
├── Ensemble 01
├── Ensemble 02
├── ...
├── Ensemble 49
│
└── Ensemble Mean
```

Each folder can be independently enabled or disabled.

---

# Modifying the KML

After creating the KML, run:

```text
modify_deepmind_kml.py
```

The script reads the existing:

```text
deepmind.kml
```

and finds the KML `<Style>` definitions.

It then asks for new settings.

For example:

```text
============================================================
DEEP MIND KML — LINE SETTINGS
============================================================

Ensemble member line width
Current: 3.5
Enter new width (Enter = keep current):

Ensemble member transparency
Current: 75%
Enter new transparency % (Enter = keep current):

Ensemble mean line width
Current: 4.0
Enter new width (Enter = keep current):

Ensemble mean transparency
Current: 100%
Enter new transparency % (Enter = keep current):
```

Pressing Enter keeps the existing setting.

---

# Transparency

Transparency is entered as a percentage:

```text
0%   = completely opaque
50%  = 50% transparent
100% = completely transparent
```

The script converts this percentage to the alpha value required by KML.

---

# Important: The Modifier Changes the Existing KML

`modify_deepmind_kml.py` does not create a second KML.

It modifies:

```text
deepmind.kml
```

directly.

Therefore, if you want to preserve an original version, make a copy before running the modifier.

---

# Running the Workflow

A typical workflow is:

### Step 1 — Run the download/KML script

```bash
python deepmind.py
```

Select:

1. Model run
2. Cyclone

The script downloads the selected data and creates:

```text
deepmind.csv
deepmind.kml
```

### Step 2 — Open the KML

Open `deepmind.kml` in Google Earth or another KML-compatible application.

### Step 3 — Adjust the line appearance

Run:

```bash
python modify_deepmind_kml.py
```

Enter new widths/transparencies as desired.

### Step 4 — Reopen/reload the KML

The modified KML contains the updated line styles.

---

# Separate Center-Passage Probability Analysis

A separate script was also developed to analyze the ensemble geometrically and produce a **center-passage probability field**.

That script is separate from the track KML generator.

It uses the ensemble tracks to calculate the percentage of ensemble members whose storm center passes within a specified radius of each grid point.

The current configuration uses:

```python
PASSAGE_RADIUS_MILES = 75
```

The basic calculation is:

> For each grid point, determine how many ensemble members have at least one forecast position within 75 miles of that point.

The resulting percentage is converted into a probability field and exported as a KML contour.

This is **not** an intensity-weighted probability and does not use:

* Storm speed
* Pressure
* Intensity
* Track weighting

It is purely based on ensemble track geometry.

---

# Important Interpretation

The center-passage probability product should not be interpreted as a conventional official tropical cyclone probability product.

It is an experimental visualization of:

> **Ensemble agreement on the potential location of the storm center.**

For example, a 70% area means that approximately 70% of the ensemble members have a track passing within the specified radius of that location.

The result depends on:

* Number of ensemble members
* Forecast track geometry
* Grid spacing
* Passage radius
* Interpolation
* Probability-field smoothing

---

# Why I Built It This Way

The main goal was to turn the DeepMind ensemble data into something more useful for operational visualization.

The raw ensemble CSV is valuable for analysis, but it is not immediately convenient for visual inspection.

The KML workflow provides:

* Individual member tracks
* Intensity information
* Ensemble mean
* Easy folder control
* Geographic visualization
* A format that can be brought into Google Earth and compatible graphics systems

The separate probability analysis then provides another way to look at the same ensemble:

**Individual tracks → What are the possible solutions?**

**Ensemble mean → What is the average solution?**

**Center-passage probability → Where do the ensemble members most strongly agree on the potential center location?**

---

# Limitations

This is an experimental analysis workflow and is not intended to replace official National Hurricane Center products.

The KML represents the DeepMind Weather Lab ensemble data available at the time the script is run.

The ensemble mean is a mathematical average of the available positions and should not necessarily be interpreted as a forecast track.

The center-passage probability calculation is also dependent on the selected radius and smoothing parameters.

---

# Files

The core files in this repository are:

```text
deepmind.py
modify_deepmind_kml.py
README.md
```

The scripts can be adapted to other project structures by changing the input/output paths near the top of the files.

---

## Summary

The workflow is essentially:

```text
DeepMind Weather Lab
        ↓
Check available model runs
        ↓
Select model run
        ↓
List available cyclones
        ↓
Select cyclone
        ↓
Download paired ensemble CSV
        ↓
Process ensemble members
        ↓
Create intensity-colored KML tracks
        ↓
Calculate ensemble mean
        ↓
Create deepmind.kml
        ↓
Optional KML style modification
        ↓
Google Earth / Graphics / Mapping
```

The separate probability workflow takes the same ensemble tracks and produces:

```text
50 ensemble tracks
        ↓
Interpolate tracks
        ↓
Create geographic grid
        ↓
Find members passing within 75 miles
        ↓
Calculate percentage
        ↓
Smooth probability field
        ↓
Create probability contours
        ↓
Export probability KML
```
