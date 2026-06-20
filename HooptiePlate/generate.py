# 113.267

import fontforge
import xml.etree.ElementTree as ET
import tempfile
import os

# Configuration
SVG_FILE = "Plate-Game-Mono.svg"
OUTPUT_OTF = "Plate-Game-Mono.otf"
OUTPUT_WOFF2 = "Plate-Game-Mono.woff2"

# Create font
font = fontforge.font()
font.fontname = "PlateGameMono"
font.familyname = "Plate Game Mono"
font.fullname = "Plate Game Mono"

font.em = 1000
font.ascent = 1000
font.descent = 0

# SVG namespace handling
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

# Load SVG
tree = ET.parse(SVG_FILE)
root = tree.getroot()
paths = root.findall(f".//{{{SVG_NS}}}path")

# Import glyphs
for i, path in enumerate(paths):
	label = path.get(f"{{{INKSCAPE_NS}}}label")
	match label:
		case "Period":
			char = "."
		case "Comma":
			char = ","
		case "Exclamation Point":
			char = "!"
		case "Apostrophe":
			char = "'"
		case "Hyphen Minus":
			char = "-"
		case "Bullet":
			char = "•"
		case _:
			char = label
	
	glyph = font.createChar(ord(char))
	glyph.glyphname = char

	# Build a temporary SVG containing only this path
	svg_data = f"""
	<svg xmlns="http://www.w3.org/2000/svg">
		<path d="{path.attrib.get('d', '')}"/>
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
		glyph.removeOverlap()
		glyph.correctDirection()

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
		font[left].addPosSub("kern_subtable", right, 100)

space = font.createChar(ord(' '))
space.glyphname = "space"
space.width = 427

# Generate font
font.generate(OUTPUT_OTF)
font.generate(OUTPUT_WOFF2)
print(f"Generated: {OUTPUT_OTF} and {OUTPUT_WOFF2}")
