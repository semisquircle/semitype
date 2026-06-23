import json
import fontforge
import xml.etree.ElementTree as ET
import tempfile
import os
import shutil
import re
import psMat

OUTPUT_PATH = "download"

# SVG namespace handling
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"


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


def italicize(font, family):
    # Select all glyphs in the font
    font.selection.all()

    # Apply the Italic transformation
    # angle = slant in degrees (defaults to -13 if left empty)
    font.italicize(-10) 
    font.macstyle |= 2
    font.appendSFNTName("English (US)", "SubFamily", "Italic")

    # Update the font metadata so OS identifies it as an Italic variant
    font.fontname = font.fontname + "-Italic"
    font.fullname = font.fullname + " Italic"

    # Set TTF/OTF specific style maps
    font.os2_stylemap = 1 # Bit 0 signifies Italic in OS/2 table

    # Generate
    font.generate(f"{OUTPUT_PATH}/{family}/ttf/{font.fontname}.ttf")
    font.generate(f"{OUTPUT_PATH}/{family}/otf/{font.fontname}.otf")
    font.generate(f"{OUTPUT_PATH}/{family}/woff2/{font.fontname}.woff2")


def generate_font(font_pref, descenders, family):
    svg_file = f'svg/{font_pref["name"]}.svg'

    # Create font
    family_name = "Tombaugh Display" if family == "display" else "Tombaugh"
    full_name = f'{family_name} {font_pref["name"]}'

    font = fontforge.font()
    font.familyname = family_name
    font.fontname = f'{font.familyname.replace(" ", "")}-{font_pref["name"]}'
    font.fullname = full_name
    font.os2_weight = font_pref["weight"]
    font.weight = font_pref["name"]
    font.version = "1.0"

    cap_top = 2 * (font_pref["square_size"] + font_pref["space_size"])
    descent = 2 * (font_pref["square_size"] + font_pref["space_size"])

    if family == "regular":
        font.em = font_pref["em"]
        font.ascent = font_pref["em"] - cap_top
        font.descent = descent
    else:
        font.em = font_pref["em"] - cap_top - descent
        font.ascent = font_pref["em"] - cap_top - descent
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

    # Kerning/spacing
    font.addLookup("kern_lookup", "gpos_pair", None, [["kern", [["latn", ["dflt"]]]]])
    font.addLookupSubtable("kern_lookup", "kern_subtable")
    glyph_names = [g.glyphname for g in font.glyphs() if g.unicode != -1]
    for left in glyph_names:
        for right in glyph_names:
            font[left].addPosSub("kern_subtable", right, font_pref["space_size"])

    # Special handling for descenders
    if family == "regular":
        for descender in descenders:
            char = descender["char"]
            kerning_string = descender.get("kerning", None)

            if kerning_string is not None:
                kerning = -(kerning_string.count("1") * font_pref["square_size"]) - (kerning_string.count("0") * font_pref["space_size"])
                exceptions = descender.get("exceptions", None)

                if exceptions is not None:
                    for left in glyph_names:
                        if left not in exceptions:
                            font[left].addPosSub("kern_subtable", char, kerning)

    # Space character
    space = font.createChar(ord(" "))
    space.glyphname = "space"
    space.width = font_pref["square_size"]

    # Generate
    font.generate(f"{OUTPUT_PATH}/{family}/ttf/{font.fontname}.ttf")
    font.generate(f"{OUTPUT_PATH}/{family}/otf/{font.fontname}.otf")
    font.generate(f"{OUTPUT_PATH}/{family}/woff2/{font.fontname}.woff2")

    italicize(font, family)

    font.close()

    print(f"✅ Generated TTF, OTF, and WOFF2 for {full_name}!")


if __name__ == "__main__":
    with open("tombaugh.json", "r") as f:
        font_prefs = json.load(f)

    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
        
    for family in ["regular", "display"]:
        os.makedirs(f'{OUTPUT_PATH}/{family}/ttf')
        os.makedirs(f'{OUTPUT_PATH}/{family}/otf')
        os.makedirs(f'{OUTPUT_PATH}/{family}/woff2')

    for font_pref in font_prefs["fonts"]:
        generate_font(font_pref, font_prefs["descenders"], "regular")
        generate_font(font_pref, font_prefs["descenders"], "display")
