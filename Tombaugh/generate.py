import fontforge
import xml.etree.ElementTree as ET
import tempfile
import os
import shutil
import re
import psMat

FONT_PREFS = [
    {"name": "b", "num_squares": 13, "square_size": 64, "space_size": 14},
    {"name": "c", "num_squares": 11, "square_size": 80, "space_size": 12},
    {"name": "d", "num_squares": 11, "square_size": 70, "space_size": 23},
    {"name": "e", "num_squares": 9, "square_size": 104, "space_size": 8},
    {"name": "f", "num_squares": 9, "square_size": 96, "space_size": 17}
]

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


def generate_font(font_pref, family):
    svg_file = f'svg/{font_pref["name"]}.svg'

    # Create font
    font = fontforge.font()
    font.familyname = "Tombaugh Display" if family == "display" else "Tombaugh"
    font.fontname = f'{font.familyname.replace(" ", "")}-{font_pref["name"]}'
    font.fullname = f'{font.familyname} {font_pref["name"]}'
    font.weight = font_pref["name"]
    font.version = "1.0"

    cap_top = 2 * (font_pref["square_size"] + font_pref["space_size"])
    descent = 2 * (font_pref["square_size"] + font_pref["space_size"])

    if family == "regular":
        font.em = 1000
        font.ascent = 1000 - cap_top
        font.descent = descent
    else:
        font.em = 1000 - cap_top - descent
        font.ascent = 1000 - cap_top - descent
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

    # Space character
    space = font.createChar(ord(" "))
    space.glyphname = "space"
    space.width = font_pref["square_size"]

    # Generate
    font.generate(f"{OUTPUT_PATH}/{family}/ttf/{font.fontname}.ttf")
    font.generate(f"{OUTPUT_PATH}/{family}/otf/{font.fontname}.otf")
    font.generate(f"{OUTPUT_PATH}/{family}/woff2/{font.fontname}.woff2")

    print(f"✅ Generated TTF, OTF, and WOFF2 for {font.fullname}!")


if __name__ == "__main__":
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
        
    for family in ["regular", "display"]:
        os.makedirs(f'{OUTPUT_PATH}/{family}/ttf')
        os.makedirs(f'{OUTPUT_PATH}/{family}/otf')
        os.makedirs(f'{OUTPUT_PATH}/{family}/woff2')

    for font_pref in FONT_PREFS:
        generate_font(font_pref, "regular")
        generate_font(font_pref, "display")
