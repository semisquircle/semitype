import fontforge
import os
import shutil


def export_glyphs(ttf_path, output_dir="glyphs"):
    font = fontforge.open(ttf_path)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    count = 0
    for glyph in font.glyphs():
        print(glyph.unicode)
        glyph.export(f"{output_dir}/{glyph.unicode}.svg")
        count += 1

    print(f"Exported {count} glyphs to '{output_dir}'")


if __name__ == "__main__":
    export_glyphs("../../pluto-timer/assets/fonts/hades/hades_tall_fat.ttf")
