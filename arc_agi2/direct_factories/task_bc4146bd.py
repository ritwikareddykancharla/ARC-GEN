def build_program(d4, palette):
    # Canonical rule: five tiles laid side by side (horizontal axis), in the order
    # original, left-right mirror, original, mirror, original.
    # D4 conjugation: for an odd number of clockwise quarter turns, the tiling axis
    # becomes vertical and the mirror becomes an up-down flip.
    # For an even number of turns, with or without the initial row reversal, the
    # axis stays horizontal and the mirror stays a left-right flip.
    # The tile sequence O,M,O,M,O is a palindrome, so reversed directions
    # (180-degree turns, reflections) still put the plain tile at index 0.
    # The rule never uses colours, so palette needs no constants.
    vertical = (int(d4) % 4) % 2 == 1
    if vertical:
        body = (
            "    h, w = g.shape\n"
            "    mirrored = g[::-1, :]\n"
            "    out = np.zeros((5 * h, w), dtype=int)\n"
            "    for k in range(5):\n"
            "        tile = g if k % 2 == 0 else mirrored\n"
            "        out[k * h:(k + 1) * h, :] = tile\n"
        )
    else:
        body = (
            "    h, w = g.shape\n"
            "    mirrored = g[:, ::-1]\n"
            "    out = np.zeros((h, 5 * w), dtype=int)\n"
            "    for k in range(5):\n"
            "        tile = g if k % 2 == 0 else mirrored\n"
            "        out[:, k * w:(k + 1) * w] = tile\n"
        )
    program = (
        "import numpy as np\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        + body +
        "    return out.tolist()\n"
    )
    return program
