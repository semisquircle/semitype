import json
from termcolor import colored


JSON_PATH = "tombaugh.json"
TARGET_SQUARE_SPACE_RATIOS = [3.25, 5.5]


def intify(num):
    return int(num) if num.is_integer() else num


def derive(weight_category, em, cap_height):
    num_squares_cap = weight_category["num_squares_cap"]
    num_spaces_cap = weight_category["num_squares_cap"] - 1

    usables = []

    scale = 100
    start = int(cap_height * scale / num_squares_cap) + 1
    end = int(cap_height * scale / num_spaces_cap)

    for k_int in range(start, end):
        k = k_int / scale

        a_int = int(cap_height * scale) - num_spaces_cap * k_int
        b_int = num_squares_cap * k_int - int(cap_height * scale)

        if a_int <= 0 or b_int <= 0 or a_int <= b_int:
            continue

        col_2_int = 2 * a_int + b_int
        col_3_int = 3 * a_int + 2 * b_int
        # cap_height_int = cap_height * scale - 4 * k_int

        if (
            col_2_int % scale != 0
            or col_3_int % scale != 0
            # or cap_height_int % scale != 0
        ):
            continue

        a = a_int / scale
        b = b_int / scale
        corner = a / 2
        cusp_offset = corner * (23.2 / 27.5)

        body_height = (weight_category["num_squares_diacritics"] + weight_category["num_squares_descent"]) * (a + b) + cap_height
        if body_height > em:
            continue
        x_height = (weight_category["num_squares_x"] * a) + ((weight_category["num_squares_x"] - 1) * b)

        usables.append(weight_category | {
            "square_size": intify(a),
            "space_size": intify(b),
            "corner_size": intify(corner),
            "cusp_offset": intify(cusp_offset),
            "body_height": intify(body_height),
            "x_height": intify(x_height),
            "square_space_ratio": a / b,
            "k": k,
        })

    # usables.sort(key=lambda x: x["usability"], reverse=True)
    return usables


def compile_derived(weight_category_list):
    min_cap_height = 0
    em = 2048
    best_cap_height = min_cap_height
    best_target_derived = []

    for cap_height in range(min_cap_height, em, 2):
        all_derived = []
        target_derived = []
        for weight_category in weight_category_list:
            derived_list = derive(weight_category, em, cap_height)
            all_derived.extend(derived_list)
        for weight_category in weight_category_list:
            num_squares_cap = weight_category["num_squares_cap"]
            matching_squares_list = [d for d in all_derived if d["num_squares_cap"] == num_squares_cap]
            if matching_squares_list:
                for target_ratio in TARGET_SQUARE_SPACE_RATIOS:
                    closest_derived = min(matching_squares_list, key=lambda d: abs(d["square_space_ratio"] - target_ratio))
                    target_derived.append(closest_derived)
        if (
            len(target_derived) == len(TARGET_SQUARE_SPACE_RATIOS) * len(weight_category_list)
            and target_derived[1]["square_space_ratio"] == TARGET_SQUARE_SPACE_RATIOS[1]
        ):
            best_cap_height = cap_height
            best_target_derived = target_derived

    with open(JSON_PATH, "r") as f:
        font_prefs = json.load(f)

        cap_top = (em - best_cap_height) / 2
        ascent = em - cap_top
        descent = em - ascent

        font_prefs["em"] = em
        font_prefs["cap_height"] = best_cap_height
        font_prefs["cap_top"] = intify(cap_top)
        font_prefs["ascent"] = intify(ascent)
        font_prefs["descent"] = intify(descent)
        font_prefs["weights"] = []

        for i, derived in enumerate(best_target_derived):
            derived = { "name": chr(ord("b") + i), "weight": 100 + (100 * i) } | derived

            # del derived["square_space_ratio"]
            del derived["k"]

            font_prefs["weights"].append(derived)

    with open(JSON_PATH, "w") as f:
        json.dump(font_prefs, f, indent=4)

    print(colored(f"⚖️ Derived {len(best_target_derived)} weights in {JSON_PATH}!", "light_green"))


if __name__ == "__main__":
    compile_derived([
        {
            "num_squares_cap": 9,
            "num_squares_x": 7,
            "num_squares_diacritics": 2,
            "num_squares_descent": 2,
        },
        {
            "num_squares_cap": 7,
            "num_squares_x": 5,
            "num_squares_diacritics": 2,
            "num_squares_descent": 2,
        },
        {
            "num_squares_cap": 5,
            "num_squares_x": 4,
            "num_squares_diacritics": 1,
            "num_squares_descent": 1,
        }
    ])
