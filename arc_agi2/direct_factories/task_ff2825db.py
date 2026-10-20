def build_program(d4, palette):
    # Canonical layout: palette strip on row 0, one-cell frame on rows 1..9 x cols 0..9,
    # interior rows 2..8 x cols 1..8. Horizontal flip (d4>=4) keeps the strip on top;
    # each clockwise rotation moves it top -> right -> bottom -> left.
    k = d4 % 4
    bounds = {
        0: "1, H - 1, 0, W - 1",   # strip along top row
        1: "0, H - 1, 0, W - 2",   # strip along right column
        2: "0, H - 2, 0, W - 1",   # strip along bottom row
        3: "0, H - 1, 1, W - 1",   # strip along left column
    }[k]
    bg = int(palette[0])
    lines = [
        "import numpy as np",
        "",
        "BG = %d" % bg,
        "",
        "def solve(demonstrations, grid):",
        "    g = np.array(grid, dtype=int)",
        "    H, W = g.shape",
        "    # frame bounding box (inclusive) in visible coordinates; strip line excluded",
        "    r0, r1, c0, c1 = " + bounds,
        "    out = g.copy()",
        "    inner = g[r0 + 1:r1, c0 + 1:c1]",
        "    vals, counts = np.unique(inner[inner != BG], return_counts=True)",
        "    if len(vals) == 0:",
        "        return out.tolist()",
        "    top = counts.max()",
        "    # generator guarantees a unique mode; deterministic fallback on ties",
        "    c = int(vals[counts == top].min())",
        "    # recolour frame, clear interior",
        "    out[r0:r1 + 1, c0:c1 + 1] = c",
        "    out[r0 + 1:r1, c0 + 1:c1] = BG",
        "    # hollow rectangle on the bounding box of the mode-colour cells",
        "    ys, xs = np.nonzero(inner == c)",
        "    y0, y1 = int(ys.min()) + r0 + 1, int(ys.max()) + r0 + 1",
        "    x0, x1 = int(xs.min()) + c0 + 1, int(xs.max()) + c0 + 1",
        "    out[y0, x0:x1 + 1] = c",
        "    out[y1, x0:x1 + 1] = c",
        "    out[y0:y1 + 1, x0] = c",
        "    out[y0:y1 + 1, x1] = c",
        "    return out.tolist()",
        "",
    ]
    return "\n".join(lines)
