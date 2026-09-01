import json
import fontforge
import xml.etree.ElementTree as ET
import tempfile
import os
import shutil
import re
import psMat
import math
import unicodedata


DOWNLOAD_OUTPUT_PATH = "C:/Users/shawn/Desktop/code/semitype/Tombaugh/download"
PLUTO_TIMER_OUTPUT_PATH = "C:/Users/shawn/Desktop/code/pluto-timer/assets/fonts/tombaugh-display"

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

WEIGHT_CLASSES = [
    {
        "number": 100,
        "name": "Thin",
        "panose": 2
    },
    {
        "number": 200,
        "name": "Extra-Light",
        "panose": 3
    },
    {
        "number": 300,
        "name": "Light",
        "panose": 4
    },
    {
        "number": 400,
        "name": "Regular",
        "panose": 5
    },
    {
        "number": 500,
        "name": "Medium",
        "panose": 6
    },
    {
        "number": 600,
        "name": "Semi-Bold",
        "panose": 7
    },
    {
        "number": 700,
        "name": "Bold",
        "panose": 8
    },
    {
        "number": 800,
        "name": "Extra-Bold",
        "panose": 9
    },
    {
        "number": 900,
        "name": "Black",
        "panose": 10
    }
]


def snake_casify(s):
    # Normalize unicode to decompose accents (e.g., 'é' becomes 'e' + accent mark)
    s = unicodedata.normalize('NFKD', s)
    # Encode to ASCII bytes, ignoring non-ASCII characters, then decode back to string
    s = s.encode('ascii', 'ignore').decode('utf-8')
    # Lowercase and strip whitespace
    s = s.lower().strip()
    # Replace spaces and hyphens with underscores
    s = re.sub(r'[\s-]+', '_', s)
    # Remove any character that isn't alphanumeric or a hyphen
    s = re.sub(r'[^\w-]', '', s)
    # Strip any leading or trailing hyphens
    return s.strip('-')


def round_path(d, decimals=2):
    # Matches SVG numeric values
    number_re = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")

    def repl(match):
        value = float(match.group(0))
        rounded = round(value, decimals)

        # Remove trailing zeros and decimal point if possible
        text = f"{rounded:.{decimals}f}"
        text = text.rstrip("0").rstrip(".")

        # Avoid "-0"
        if text == "-0":
            text = "0"

        return text

    return number_re.sub(repl, d)


def obliquify(font, family):
    angle_deg = 15

    for glyph in font.glyphs():
        if glyph.unicode != -1:
            glyph.transform(psMat.skew(angle_deg * math.pi / 180))

    font.italicangle = angle_deg
    font.macstyle |= 2
    font.os2_stylemap = 1

    font.fontname += "-Oblique"
    font.fullname += " Oblique"
    # font.appendSFNTName("English (US)", "SubFamily", "Oblique")

    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/ttf/{font.fontname}.ttf")
    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/otf/{font.fontname}.otf")
    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/woff2/{font.fontname}.woff2")

    print(f"✅ Generated TTF, OTF, and WOFF2 for {font.fullname}!")


def generate_font(weight, version, em, cap_height, cap_top, ascent, descent, family):
    svg_file = f'svg/{weight["name"]}.svg'

    # Create font
    family_name = "Tombaugh Display" if family == "display" else "Tombaugh"
    full_name = f'{family_name} {weight["name"]}'

    weight_class = next((w for w in WEIGHT_CLASSES if w["number"] == weight["weight"]), None)

    font = fontforge.font()
    font.familyname = family_name
    font.fontname = f'{font.familyname.replace(" ", "")}-{weight["name"]}'
    font.fullname = full_name
    font.weight = weight["name"]
    font.version = version
    font.copyright = "Copyright (c) 2026, semisquircle"

    font.os2_weight = weight_class["number"]
    font.os2_family_class = 0x0800
    font.os2_panose = (2, 11, weight_class["panose"], 3, 6, 5, 2, 2, 2, 3)

    if family == "regular":
        font.em = em
        font.ascent = ascent
        font.descent = descent
    else:
        font.em = cap_height
        font.ascent = cap_height
        font.descent = 0

    # Load SVG
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Find all "ref" groups and their paths
    ref_groups = root.findall(f".//{{{SVG_NS}}}g[@{{{INKSCAPE_NS}}}label='ref']")
    ref_paths = set()
    for group in ref_groups:
        ref_paths.update(group.findall(f".//{{{SVG_NS}}}path"))

    # Get all paths excluding those in ref groups
    all_paths = root.findall(f".//{{{SVG_NS}}}path")
    paths = [p for p in all_paths if p not in ref_paths]

    # Import glyphs
    for i, path in enumerate(paths):
        label = path.get(f"{{{INKSCAPE_NS}}}label")

        # Descender check for display
        potential_descender_label = label.split()
        glyph_family = potential_descender_label[-1]
        if glyph_family in ["regular", "display"]:
            if glyph_family != family:
                continue
            else:
                label = potential_descender_label[0]

        match label:
            case "Period":
                char = "."
            case "Exclamation Point":
                char = "!"
            case "Question Mark":
                char = "?"
            case "Colon":
                char = ":"
            case _:
                char = label

        glyph = font.createChar(ord(char))
        glyph.glyphname = char

        # Build a temporary SVG containing only this path
        path_d = round_path(path.attrib.get("d", ""), 2)
        svg_data = f"""
		<svg xmlns="http://www.w3.org/2000/svg">
			<path d="{path_d}"/>
		</svg>
		"""

        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(svg_data)
            tmp_svg = tmp.name

        try:
            glyph.importOutlines(tmp_svg)

            # Normalize size and position
            glyph.removeOverlap()
            glyph.correctDirection()

            xmin, ymin, xmax, ymax = glyph.boundingBox()
            if family == "display":
                glyph.transform(psMat.translate(-xmin, cap_top))
            glyph.width = int(xmax - xmin)

        finally:
            try:
                os.remove(tmp_svg)
            except OSError:
                pass

    def string_to_width(s):
        return int(
            (s.count("1") * weight["square_size"])
            + (s.count("0") * weight["space_size"])
            + (s.count("2") * (((weight["square_size"] + weight["space_size"]) / 2) - weight["space_size"]))
        )

    # Kerning
    lookup_name = "kern_lookup"
    subtable_name = "kern_subtable"
    desired_kern = weight["space_size"]
    glyph_list = [g.glyphname for g in font.glyphs() if not g.glyphname.startswith(" ")]
    font.addLookup(lookup_name, "gpos_pair", None, [("kern", [("latn", ["dflt"])])])
    font.addLookupSubtable(lookup_name, subtable_name)
    font.autoKern(subtable_name, desired_kern, glyph_list, glyph_list, minKern=desired_kern, onlyCloser=False, touch=True)

    # Manual rounding to bypass optical inconsistencies
    targets = [
        weight["space_size"],
        -weight["square_size"],
        -(((weight["square_size"] + weight["space_size"]) / 2) - weight["space_size"])
    ]
    for glyph in font.glyphs():
        for lookup in glyph.getPosSub("*"):
            partner = lookup[2]
            value = lookup[5]

            # Find the closest target value
            new_value = round(min(targets, key=lambda t: abs(value - t)))

            if new_value != value:
                # print(f'{value} -> {new_value}')
                # glyph.removePosSub(partner)
                glyph.addPosSub(lookup[0], partner, new_value)

    # Manual kerning
    # font.addLookup(lookup_name, "gpos_pair", None, [("kern", [("latn", ["dflt"])])])
    # font.addLookupSubtable(lookup_name, subtable_name)
    # glyph_names = [g.glyphname for g in font.glyphs() if g.unicode != -1]
    # for left in glyph_names:
    #     for right in glyph_names:
    #         font[left].addPosSub(subtable_name, right, font_pref["space_size"])

    # # Special handling for ascenders
    # for ascender in ascenders:
    #     char = ascender["char"]

    #     left_kerning_string = ascender["left"]["anti_kerning"]
    #     left_kerning = -string_to_width(left_kerning_string)
    #     for left in ascender["left"]["lowers"]:
    #         font[left].addPosSub(subtable_name, char, left_kerning)

    #     right_kerning_string = ascender["right"]["anti_kerning"]
    #     right_kerning = -string_to_width(right_kerning_string)
    #     for right in ascender["right"]["lowers"]:
    #         font[char].addPosSub(subtable_name, right, right_kerning)

    # # Special handling for descenders
    # if family == "regular":
    #     for descender in descenders:
    #         char = descender["char"]
    #         kerning_string = descender.get("anti_kerning", None)

    #         if kerning_string is not None:
    #             kerning = -string_to_width(kerning_string)
    #             exceptions = descender.get("exceptions", None)

    #             if exceptions is not None:
    #                 for left in glyph_names:
    #                     if left not in exceptions:
    #                         font[left].addPosSub(subtable_name, char, kerning)

    # Space character
    space = font.createChar(ord(" "))
    space.glyphname = "space"
    space.width = weight["square_size"] + weight["space_size"]

    # Generate
    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/ttf/{font.fontname}.ttf")
    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/otf/{font.fontname}.otf")
    font.generate(f"{DOWNLOAD_OUTPUT_PATH}/{family}/woff2/{font.fontname}.woff2")
    if family == "display":
        font.generate(f"{PLUTO_TIMER_OUTPUT_PATH}/{snake_casify(full_name)}.ttf")

    print(f"✅ Generated TTF, OTF, and WOFF2 for {full_name}!")

    obliquify(font, family)

    font.close()


if __name__ == "__main__":
    with open("tombaugh.json", "r") as f:
        font_prefs = json.load(f)

    if os.path.exists(DOWNLOAD_OUTPUT_PATH):
        shutil.rmtree(DOWNLOAD_OUTPUT_PATH)
    if os.path.exists(PLUTO_TIMER_OUTPUT_PATH):
        shutil.rmtree(PLUTO_TIMER_OUTPUT_PATH)
        
    for family in ["regular", "display"]:
        os.makedirs(f'{DOWNLOAD_OUTPUT_PATH}/{family}/ttf')
        os.makedirs(f'{DOWNLOAD_OUTPUT_PATH}/{family}/otf')
        os.makedirs(f'{DOWNLOAD_OUTPUT_PATH}/{family}/woff2')
    os.makedirs(PLUTO_TIMER_OUTPUT_PATH)

    for weight in font_prefs["weights"]:
        generate_font(weight, font_prefs["version"], font_prefs["em"], font_prefs["cap_height"], font_prefs["cap_top"], font_prefs["ascent"], font_prefs["descent"], "regular")
        generate_font(weight, font_prefs["version"], font_prefs["em"], font_prefs["cap_height"], font_prefs["cap_top"], font_prefs["ascent"], font_prefs["descent"], "display")
