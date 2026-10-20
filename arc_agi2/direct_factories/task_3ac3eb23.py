def build_program(d4, palette):
    # The original growth direction is 'down' (dr=+1, dc=0).
    # A horizontal flip leaves the vertical vector (1,0) unchanged.
    # Each clockwise rotation maps a vector (dr,dc) to (dc,-dr).
    dr, dc = 1, 0
    if d4 >= 4:
        dr, dc = dr, -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    ar, ac = abs(dc), abs(dr)  # perpendicular 'across' axis
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d
DR, DC = %d, %d
AR, AC = %d, %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seeds = [(r, c, int(g[r, c])) for r in range(H) for c in range(W) if g[r, c] != BG]
    seeds.sort(key=lambda s: (s[0] * AR + s[1] * AC, s[0] * DR + s[1] * DC))
    for sr, sc, col in seeds:
        t = 0
        while True:
            r = sr + DR * t
            c = sc + DC * t
            if not (0 <= r < H and 0 <= c < W):
                break
            if t %% 2 == 0:
                out[r, c] = col
            else:
                for s in (-1, 1):
                    rr = r + AR * s
                    cc = c + AC * s
                    if 0 <= rr < H and 0 <= cc < W:
                        out[rr, cc] = col
            t += 1
    return out.tolist()
''' % (bg, dr, dc, ar, ac)
    return src
