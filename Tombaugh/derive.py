def derive(num_squares, em=1000):
    print(f'{num_squares} squares, {num_squares - 1} spaces')

    k = 0
    k_delta = 0.01
    k_dig = 2
    for i in range(int(10000 / k_delta)):
        k += k_delta

        a = round(em - (num_squares - 1) * k, k_dig)
        b = round(num_squares * k - em, k_dig)

        corner = round(a / 2, k_dig)
        space_space = a / b
        usability = min(space_space, 5.5) / max(space_space, 5.5)

        col_2 = round(a + b + a, k_dig)
        col_3 = round(a + b + a + b + a, k_dig)
        cap_top = a + b + a + b
        descent = a + b + a + b
        cap_height = round(1000 - cap_top - descent, k_dig)

        is_col_2_int = col_2.is_integer()
        is_col_3_int = col_3.is_integer()
        is_cap_height_int = cap_height.is_integer()

        if a > 0 and b > 0 and a > b and is_col_2_int and is_col_3_int and is_cap_height_int:
            print(f'Square: {a}, Space: {b}, Corner: {corner}, Usability: {usability}')
    
    print()


if __name__ == "__main__":
    print()
    derive(13)
    derive(11)
    derive(9)
