import json
import time
from termcolor import colored


JSON_PATH = "tombaugh.json"
style_string = "fill:#134340;fill-opacity:0.5;stroke-width:0;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:20;paint-order:stroke fill markers"


def generate_guide(em, x, y, orient, color="blue"):
    orientation = "-1,0" if orient == "vert" else "0,1"

    match color:
        case "blue":
            rgb = "rgb(0,134,229)"
        case "red":
            rgb = "rgb(246,97,81)"
        case "green":
            rgb = "rgb(143,240,164)"
    
    return f"""
        <sodipodi:guide
            position="{x},{em - y}"
            orientation="{orientation}"
            id="guide{time.time_ns()}"
            inkscape:locked="false"
            inkscape:label=""
            inkscape:color="{rgb}"
        />
    """


def generate_svg(weight, em, cap_height, cap_top, ascent, descent):
    svg_path = f"svg/{weight["name"]}.svg"

    body_top = (em - weight["body_height"]) / 2
    x_height_center = ascent - (weight["x_height"] / 2)
    num_squares_body = weight["num_squares_cap"] + weight["num_squares_diacritics"] + weight["num_squares_descent"]

    template_horiz_rects_string = ""
    for c in range(3):
        for r in range(num_squares_body - 1):
            template_horiz_rects_string += f"""
                <rect
                    x="{c * (weight["square_size"] + weight["space_size"])}"
                    y="{body_top + weight["square_size"] + r * (weight["square_size"] + weight["space_size"])}"
                    width="{weight["square_size"]}"
                    height="{weight["space_size"]}"
                    style="{style_string}"
                />
            """

    template_vert_rects_string = ""
    for c in range(2):
        for r in range(num_squares_body):
            template_vert_rects_string += f"""
                <rect
                    x="{weight["square_size"] + (c * (weight["square_size"] + weight["space_size"]))}"
                    y="{body_top + r * (weight["square_size"] + weight["space_size"])}"
                    width="{weight["space_size"]}"
                    height="{weight["square_size"]}"
                    style="{style_string}"
                />
            """

    template_string = f"""
        <g inkscape:label="template" style="display:none;">
            <rect
                x="0"
                y="{body_top}"
                width="{2 * (weight["square_size"] + weight["space_size"]) + weight["square_size"]}"
                height="{weight["body_height"]}"
                style="{style_string}"
            />
            {template_horiz_rects_string}
            {template_vert_rects_string}
        </g>
    """

    with open(svg_path, "w") as f:
        f.write(f"""
            <svg
                width="{em}pt"
                height="{em}pt"
                viewBox="0 0 {em} {em}"
                version="1.1"
                id="svg1"
                inkscape:version="1.4.4 (dcaf3e7, 2026-05-05)"
                xml:space="preserve"
                sodipodi:docname="{weight["name"]}.svg"
                xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
                xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
                xmlns="http://www.w3.org/2000/svg"
                xmlns:svg="http://www.w3.org/2000/svg"
            >
                <sodipodi:namedview
                    id="namedview1"
                    pagecolor="#ffffff"
                    bordercolor="#000000"
                    borderopacity="1"
                    inkscape:showpageshadow="0"
                    inkscape:pageopacity="0"
                    inkscape:pagecheckerboard="0"
                    inkscape:deskcolor="#505050"
                    inkscape:document-units="pt"
                    inkscape:zoom="0.57994252"
                    inkscape:cx="368.13993"
                    inkscape:cy="686.27491"
                    inkscape:current-layer="svg1"
                    showguides="true"
                >
                    {generate_guide(em, 0, cap_top, "horiz")}
                    {generate_guide(em, 0, ascent, "horiz")}

                    {generate_guide(em, 0, (em / 2) - (weight["square_size"] / 2), "horiz")}
                    {generate_guide(em, 0, (em / 2) - (weight["space_size"] / 2), "horiz")}
                    {generate_guide(em, 0, em / 2, "horiz")}
                    {generate_guide(em, 0, (em / 2) + (weight["space_size"] / 2), "horiz")}
                    {generate_guide(em, 0, (em / 2) + (weight["square_size"] / 2), "horiz")}

                    {generate_guide(em, 0, x_height_center - (weight["square_size"] / 2), "horiz", "green")}
                    {generate_guide(em, 0, x_height_center - (weight["space_size"] / 2), "horiz", "green")}
                    {generate_guide(em, 0, x_height_center, "horiz", "green")}
                    {generate_guide(em, 0, x_height_center + (weight["space_size"] / 2), "horiz", "green")}
                    {generate_guide(em, 0, x_height_center + (weight["square_size"] / 2), "horiz", "green")}

                    {generate_guide(em, (weight["square_size"] + weight["space_size"]) / 2, 0, "vert")}
                    {generate_guide(em, (3 * weight["square_size"] + weight["space_size"]) / 2, 0, "vert")}

                    {generate_guide(em, weight["square_size"] + weight["space_size"], 0, "vert", "red")}
                    {generate_guide(em, 0, ascent - weight["square_size"], "horiz", "red")}
                </sodipodi:namedview>
                
                <g inkscape:label="ref">
                    {template_string}

                    <rect
                        x="0"
                        y="0"
                        width="{weight["corner_size"]}"
                        height="{weight["corner_size"] + weight["cusp_offset"]}"
                        style="{style_string}"
                    />
                    <path
                        inkscape:label="cusp quarter circle"
                        d="M 0,0 H {weight["corner_size"]} A {weight["corner_size"]},{weight["corner_size"]} 0 0 1 0,{weight["corner_size"]} Z"
                        style="{style_string}"
                    />
                    <path
                        inkscape:label="cusp quarter circle"
                        d="M 0,{weight["corner_size"]} H {weight["corner_size"]} A {weight["corner_size"]},{weight["corner_size"]} 0 0 0 0,0 Z"
                        style="{style_string}"
                        transform="translate(0, {weight["cusp_offset"]})"
                    />
                </g>

                {(26 + 26 + 5 + 10 + 4) * template_string}
            </svg>
        """)

    print(colored(f"✒️ Generated {weight["name"]}.svg!", "light_green"))


if __name__ == "__main__":
    with open(JSON_PATH, "r") as f:
        font_prefs = json.load(f)
        print()
        for weight in font_prefs["weights"]:
            # if weight["name"] == "f":
                generate_svg(weight, font_prefs["em"], font_prefs["cap_height"], font_prefs["cap_top"], font_prefs["ascent"], font_prefs["descent"])
        print()
