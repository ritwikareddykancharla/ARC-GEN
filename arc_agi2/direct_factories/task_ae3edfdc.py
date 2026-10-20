def build_program(d4, palette):
    bg = int(palette[0])
    centre_a = int(palette[1])
    sat_a = int(palette[7])
    centre_b = int(palette[2])
    sat_b = int(palette[3])
    lines = []
    lines.append('BG = %d' % bg)
    lines.append('PAIRS = [(%d, %d), (%d, %d)]  # (satellite colour, centre colour)' % (sat_a, centre_a, sat_b, centre_b))
    lines.append('# D4 variant index %d: the slide-to-centre rule is symmetric under every D4 map,' % int(d4))
    lines.append('# so rows/columns and both directions along each line are handled directly.')
    body = '''
def _find(grid, colour):
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == colour:
                return (r, c)
    return None

def _sign(v):
    return 1 if v > 0 else -1

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    placements = []
    for sat, cen in PAIRS:
        pos = _find(g, cen)
        if pos is None:
            continue
        cr, cc = pos
        for r in range(h):
            for c in range(w):
                if g[r][c] != sat:
                    continue
                if r == cr and c != cc:
                    nr, nc = cr, cc + _sign(c - cc)
                elif c == cc and r != cr:
                    nr, nc = cr + _sign(r - cr), cc
                else:
                    continue
                out[r][c] = BG
                placements.append((nr, nc, sat))
    for nr, nc, sat in placements:
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = sat
    return out
'''
    return '\n'.join(lines) + '\n' + body
