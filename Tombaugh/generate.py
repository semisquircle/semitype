import fontforge
import xml.etree.ElementTree as ET
import tempfile
import os
import shutil
import re

FONT_PREFS = [
	{ "name": "b", "spacing": 12, "space": 66 },
	{ "name": "c", "spacing": 12, "space": 66 },
	{ "name": "d", "spacing": 12, "space": 66 },
	{ "name": "e", "spacing": 12, "space": 66 }
]

# SVG namespace handling
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

TTF_PATH = "download/ttf"
OTF_PATH = "download/otf"
WOFF2_PATH = "download/woff2"

def round_svg_path(d, decimals=2):
    # Matches SVG numeric values
    number_re = re.compile(
        r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?'
    )

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

def generate_font(index):
	font_pref = FONT_PREFS[index]
	svg_file = f'{font_pref["name"]}.svg'

	# Create font
	font = fontforge.font()
	font.fontname = "Tombaugh-" + font_pref["name"]
	font.familyname = "Tombaugh"
	font.fullname = "Tombaugh " + font_pref["name"]

	font.em = 1000
	font.ascent = 800
	font.descent = 200

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
		path_d = round_svg_path(path.attrib.get("d", ""), 2)
		print(path_d)
		svg_data = f"""
		<svg xmlns="http://www.w3.org/2000/svg">
			<path d="{path_d}"/>
		</svg>
		"""

		with tempfile.NamedTemporaryFile(
			suffix=".svg",
			delete=False,
			mode="w",
			encoding="utf-8"
		) as tmp:
			tmp.write(svg_data)
			tmp_svg = tmp.name

		try:
			glyph.importOutlines(tmp_svg)

			# Normalize size and position
			# glyph.removeOverlap()
			# glyph.correctDirection()

			xmin, ymin, xmax, ymax = glyph.boundingBox()
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
			font[left].addPosSub("kern_subtable", right, font_pref["spacing"])

	# Space character
	space = font.createChar(ord(' '))
	space.glyphname = "space"
	space.width = font_pref["space"]

	# Generate
	if os.path.exists(TTF_PATH): shutil.rmtree(TTF_PATH)
	if os.path.exists(OTF_PATH): shutil.rmtree(OTF_PATH)
	if os.path.exists(WOFF2_PATH): shutil.rmtree(WOFF2_PATH)
	os.makedirs(TTF_PATH)
	os.makedirs(OTF_PATH)
	os.makedirs(WOFF2_PATH)
	font.generate(f'{TTF_PATH}/{font.fontname}.ttf')
	font.generate(f'{OTF_PATH}/{font.fontname}.otf')
	font.generate(f'{WOFF2_PATH}/{font.fontname}.woff2')

	print(f'✅ Generated TTF, OTF, and WOFF2 for {font.fullname}!')

if __name__ == "__main__":
	# for f in range(len(font_prefs)):
		# generate_font(f)
	generate_font(3)
