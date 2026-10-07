# ============================================================
# Modify DeepMind KML Line Settings
# ============================================================

import os
import re


# ============================================================
# SETTINGS
# ============================================================

KML_FILE = "../../data/output/deepmind.kml"


# ============================================================
# READ KML
# ============================================================

if not os.path.exists(KML_FILE):

    raise FileNotFoundError(
        f"KML file not found: {KML_FILE}"
    )


with open(
    KML_FILE,
    "r",
    encoding="utf-8"
) as f:

    kml = f.read()


# ============================================================
# FIND CURRENT ENSEMBLE MEMBER SETTINGS
# ============================================================

member_match = re.search(
    r'(<Style id="intensity_[^"]+">.*?<LineStyle>'
    r'<color>)([0-9a-fA-F]{8})(</color>'
    r'<width>)([^<]+)(</width>)',
    kml,
    re.DOTALL
)

if not member_match:

    raise ValueError(
        "Could not find ensemble member line settings."
    )


member_color = member_match.group(2)
member_width = float(member_match.group(4))

member_alpha = int(
    member_color[0:2],
    16
)

member_transparency = (
    member_alpha / 255 * 100
)


# ============================================================
# FIND CURRENT ENSEMBLE MEAN SETTINGS
# ============================================================

mean_match = re.search(
    r'(<Style id="ensemble_mean">.*?<LineStyle>'
    r'<color>)([0-9a-fA-F]{8})(</color>'
    r'<width>)([^<]+)(</width>)',
    kml,
    re.DOTALL
)

if not mean_match:

    raise ValueError(
        "Could not find ensemble mean line settings."
    )


mean_color = mean_match.group(2)
mean_width = float(mean_match.group(4))

mean_alpha = int(
    mean_color[0:2],
    16
)

mean_transparency = (
    mean_alpha / 255 * 100
)


# ============================================================
# DISPLAY CURRENT SETTINGS
# ============================================================

print()
print("============================================================")
print("DEEP MIND KML — LINE SETTINGS")
print("============================================================")
print()


# ============================================================
# ENSEMBLE MEMBER WIDTH
# ============================================================

print("Ensemble member line width")
print(f"Current: {member_width}")

new_member_width = input(
    "Enter new width (Enter = keep current): "
).strip()

if new_member_width:

    try:
        new_member_width = float(
            new_member_width
        )

        if new_member_width <= 0:
            raise ValueError

        member_width = new_member_width

    except ValueError:

        raise ValueError(
            "Invalid ensemble member width."
        )


print()


# ============================================================
# ENSEMBLE MEMBER TRANSPARENCY
# ============================================================

print("Ensemble member transparency")
print(
    f"Current: "
    f"{member_transparency:.0f}%"
)

new_member_transparency = input(
    "Enter new transparency % "
    "(Enter = keep current): "
).strip()

if new_member_transparency:

    try:

        new_member_transparency = float(
            new_member_transparency
        )

        if not 0 <= new_member_transparency <= 100:
            raise ValueError

        member_transparency = (
            new_member_transparency
        )

    except ValueError:

        raise ValueError(
            "Transparency must be between 0 and 100."
        )


print()


# ============================================================
# ENSEMBLE MEAN WIDTH
# ============================================================

print("Ensemble mean line width")
print(f"Current: {mean_width}")

new_mean_width = input(
    "Enter new width (Enter = keep current): "
).strip()

if new_mean_width:

    try:

        new_mean_width = float(
            new_mean_width
        )

        if new_mean_width <= 0:
            raise ValueError

        mean_width = new_mean_width

    except ValueError:

        raise ValueError(
            "Invalid ensemble mean width."
        )


print()


# ============================================================
# ENSEMBLE MEAN TRANSPARENCY
# ============================================================

print("Ensemble mean transparency")
print(
    f"Current: "
    f"{mean_transparency:.0f}%"
)

new_mean_transparency = input(
    "Enter new transparency % "
    "(Enter = keep current): "
).strip()

if new_mean_transparency:

    try:

        new_mean_transparency = float(
            new_mean_transparency
        )

        if not 0 <= new_mean_transparency <= 100:
            raise ValueError

        mean_transparency = (
            new_mean_transparency
        )

    except ValueError:

        raise ValueError(
            "Transparency must be between 0 and 100."
        )


# ============================================================
# CONVERT TRANSPARENCY TO KML ALPHA
# ============================================================

member_alpha = round(
    member_transparency / 100 * 255
)

mean_alpha = round(
    mean_transparency / 100 * 255
)


# ============================================================
# UPDATE ENSEMBLE MEMBER STYLES
# ============================================================

new_member_color = (
    f"{member_alpha:02x}"
    f"{member_color[2:]}"
)


def replace_member_style(
    match
):

    old_color = match.group(2)

    new_color = (
        f"{member_alpha:02x}"
        f"{old_color[2:]}"
    )

    return (
        match.group(1)
        + new_color
        + match.group(3)
        + str(member_width)
        + match.group(5)
    )


kml = re.sub(
    r'(<Style id="intensity_[^"]+">.*?<LineStyle>'
    r'<color>)([0-9a-fA-F]{8})(</color>'
    r'<width>)([^<]+)(</width>)',
    replace_member_style,
    kml,
    flags=re.DOTALL
)


# ============================================================
# UPDATE ENSEMBLE MEAN STYLE
# ============================================================

def replace_mean_style(
    match
):

    old_color = match.group(2)

    new_color = (
        f"{mean_alpha:02x}"
        f"{old_color[2:]}"
    )

    return (
        match.group(1)
        + new_color
        + match.group(3)
        + str(mean_width)
        + match.group(5)
    )


kml = re.sub(
    r'(<Style id="ensemble_mean">.*?<LineStyle>'
    r'<color>)([0-9a-fA-F]{8})(</color>'
    r'<width>)([^<]+)(</width>)',
    replace_mean_style,
    kml,
    flags=re.DOTALL
)


# ============================================================
# WRITE UPDATED KML
# ============================================================

with open(
    KML_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(kml)


# ============================================================
# DONE
# ============================================================

print()
print("============================================================")
print("KML UPDATED")
print("============================================================")
print()
print(
    f"Ensemble member width:        "
    f"{member_width}"
)

print(
    f"Ensemble member transparency: "
    f"{member_transparency:.0f}%"
)

print(
    f"Ensemble mean width:           "
    f"{mean_width}"
)

print(
    f"Ensemble mean transparency:    "
    f"{mean_transparency:.0f}%"
)

print()
print(f"KML: {KML_FILE}")
print("============================================================")
