import os
import sys
import fontforge


def export_glyphs(ttf_path, output_dir="glyphs"):
	font = fontforge.open(ttf_path)
	os.rmdir(output_dir)
	os.makedirs(output_dir)

	count = 0
	for glyph in font.glyphs():
		# Skip empty glyphs
		if glyph.foreground.isEmpty() is False:
			glyph.export(f'{output_dir}/{glyph.unicode}.svg')
			count += 1

	print(f"Exported {count} glyphs to '{output_dir}'")


if __name__ == "__main__":
	export_glyphs("download/hades_tall_fat.ttf")
