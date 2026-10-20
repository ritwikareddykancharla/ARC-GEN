def build_program(d4, palette):
    bg = int(palette[7])
    sq = int(palette[1])
    sq_out = int(palette[2])
    dot = int(palette[9])
    header = 'import numpy as np\n\nBG = %d\nSQ = %d\nSQ_OUT = %d\nDOT = %d\n' % (bg, sq, sq_out, dot)
    body = '''

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    cells = np.argwhere(g == SQ)
    if len(cells) == 0:
        return out.tolist()
    r0, c0 = (int(v) for v in cells.min(0))
    r1, c1 = (int(v) for v in cells.max(0))
    out[g == SQ] = SQ_OUT
    moves = []
    for r, c in np.argwhere(g == DOT):
        r, c = int(r), int(c)
        if c0 <= c <= c1 and r < r0:
            moves.append((r0 - r, r, c, (r0, c), (r0 - 1, c)))
        elif c0 <= c <= c1 and r > r1:
            moves.append((r - r1, r, c, (r1, c), (r1 + 1, c)))
        elif r0 <= r <= r1 and c < c0:
            moves.append((c0 - c, r, c, (r, c0), (r, c0 - 1)))
        elif r0 <= r <= r1 and c > c1:
            moves.append((c - c1, r, c, (r, c1), (r, c1 + 1)))
    if not moves:
        return out.tolist()
    best = min(m[0] for m in moves)
    for m in moves:
        out[m[1], m[2]] = BG
    for gap, r, c, inner, outer in moves:
        tr, tc = inner if gap == best else outer
        out[tr, tc] = DOT
    return out.tolist()
'''
    return header + body
