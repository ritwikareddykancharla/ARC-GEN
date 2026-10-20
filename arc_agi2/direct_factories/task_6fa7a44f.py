def build_program(d4, palette):
    k = d4 % 4
    if k == 0:
        body = (
            "    out = np.zeros((2 * h, w), dtype=int)\n"
            "    out[:h, :] = g\n"
            "    out[h:, :] = g[::-1, :]\n"
        )
        note = "original on top, upside-down copy appended below"
    elif k == 2:
        body = (
            "    out = np.zeros((2 * h, w), dtype=int)\n"
            "    out[:h, :] = g[::-1, :]\n"
            "    out[h:, :] = g\n"
        )
        note = "upside-down copy on top, original below"
    elif k == 1:
        body = (
            "    out = np.zeros((h, 2 * w), dtype=int)\n"
            "    out[:, :w] = g[:, ::-1]\n"
            "    out[:, w:] = g\n"
        )
        note = "left-right mirrored copy on the left, original on the right"
    else:
        body = (
            "    out = np.zeros((h, 2 * w), dtype=int)\n"
            "    out[:, :w] = g\n"
            "    out[:, w:] = g[:, ::-1]\n"
        )
        note = "original on the left, left-right mirrored copy on the right"
    prog = (
        "import numpy as np\n"
        "\n"
        "# Mirror-extension: " + note + ".\n"
        "# Colours are copied verbatim, so no palette constants are needed.\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    h, w = g.shape\n"
        + body +
        "    return out.tolist()\n"
    )
    return prog
