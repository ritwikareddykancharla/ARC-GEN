def build_program(d4, palette):
    H, W = 4, 14

    def tf(r, c, h, w):
        if d4 >= 4:
            c = w - 1 - c
        for _ in range(d4 % 4):
            r, c = c, h - 1 - r
            h, w = w, h
        return (int(r), int(c))

    panels = []
    for i in range(3):
        pts = [tf(r, 5 * i + c, H, W) for r in range(4) for c in range(4)]
        panels.append((min(p[0] for p in pts), min(p[1] for p in pts)))
    holes = {
        2: [],
        8: [(1, 1), (1, 2), (2, 1), (2, 2)],
        4: [(2, 1), (2, 2), (3, 1), (3, 2)],
        3: [(1, 0), (2, 0), (1, 3), (2, 3)],
    }
    t0, l0 = panels[0]
    table = []
    for colour, hs in holes.items():
        rel = []
        for r, c in hs:
            vr, vc = tf(r, c, H, W)
            rel.append((vr - t0, vc - l0))
        table.append((tuple(sorted(rel)), int(palette[colour])))
    out_cells = [[tf(i, c, 3, 3) for c in range(3)] for i in range(3)]
    hole = int(palette[0])
    lines = [
        'import numpy as np',
        '',
        '# top-left corners of the three 4x4 panels in visible coordinates',
        'PANELS = ' + repr(panels),
        '# exact hole-mask (cells of hole colour, relative to panel corner) -> output colour',
        'TABLE = dict((frozenset(k), v) for k, v in ' + repr(table) + ')',
        '# visible output cells that receive the colour of panel i',
        'OUT_CELLS = ' + repr(out_cells),
        'HOLE = ' + repr(hole),
        'DEFAULT = ' + repr(hole),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid)',
        '    out = np.full((3, 3), DEFAULT, dtype=int)',
        '    for i, (t, l) in enumerate(PANELS):',
        '        block = g[t:t + 4, l:l + 4]',
        '        ys, xs = np.nonzero(block == HOLE)',
        '        key = frozenset((int(y), int(x)) for y, x in zip(ys, xs))',
        '        colour = TABLE.get(key, DEFAULT)',
        '        for r, c in OUT_CELLS[i]:',
        '            out[r, c] = colour',
        '    return out.tolist()',
    ]
    return '\n'.join(lines) + '\n'
