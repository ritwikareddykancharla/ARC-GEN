def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    flip = d4 >= 4
    lines_are_rows = (k % 2 == 0)
    reversed_pos = (k in (2, 3)) != flip
    pal = [int(palette[i]) for i in range(10)]
    table = [pal[2], pal[4], pal[3]]
    gray = pal[5]
    bg = pal[0]
    header = (
        'import numpy as np\n'
        'LINES_ARE_ROWS = ' + repr(bool(lines_are_rows)) + '\n'
        'REVERSED = ' + repr(bool(reversed_pos)) + '\n'
        'TABLE = ' + repr(table) + '\n'
        'GRAY = ' + repr(gray) + '\n'
        'BG = ' + repr(bg) + '\n'
    )
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = np.full_like(g, BG)
    if LINES_ARE_ROWS:
        nlines, n = h, w
    else:
        nlines, n = w, h
    if REVERSED:
        order = list(range(n - 1, -1, -1))
    else:
        order = list(range(n))
    for i in range(nlines):
        line = g[i, :] if LINES_ARE_ROWS else g[:, i]
        hit = None
        for p in order:
            if int(line[p]) == GRAY:
                hit = p
                break
        if hit is None:
            for p in order:
                if int(line[p]) != BG:
                    hit = p
                    break
        if hit is None:
            continue
        c = (n - 1 - hit) if REVERSED else hit
        colour = TABLE[c] if 0 <= c < len(TABLE) else BG
        if LINES_ARE_ROWS:
            out[i, :] = colour
        else:
            out[:, i] = colour
    return out.tolist()
'''
    return header + body
