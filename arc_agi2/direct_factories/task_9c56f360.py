def build_program(d4, palette):
    bg = int(palette[0])
    mv = int(palette[3])
    wall = int(palette[8])
    # Original motion: 3-runs anchored at the RIGHT edge slide LEFT, vector (dr,dc)=(0,-1).
    dr, dc = 0, -1
    if d4 >= 4:
        dc = -dc  # reversing each row flips horizontal component
    for _ in range(d4 % 4):
        # clockwise rotation maps (r,c)->(c,H-1-r), so a vector (dr,dc)->(dc,-dr)
        dr, dc = dc, -dr
    src = []
    src.append('import numpy as np\n')
    src.append('BG = %d\n' % bg)
    src.append('MV = %d\n' % mv)
    src.append('WALL = %d\n' % wall)
    src.append('DR = %d\n' % dr)
    src.append('DC = %d\n' % dc)
    src.append('''

def _lines(H, W):
    # Each line is ordered starting at the edge where the movers are anchored,
    # proceeding in the direction of motion.
    if DR == 0:
        cols = list(range(W - 1, -1, -1)) if DC == -1 else list(range(W))
        return [[(r, c) for c in cols] for r in range(H)]
    rows = list(range(H - 1, -1, -1)) if DR == -1 else list(range(H))
    return [[(r, c) for r in rows] for c in range(W)]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for line in _lines(H, W):
        vals = [int(g[p]) for p in line]
        n = len(vals)
        if n == 0 or vals[0] != MV:
            continue
        L = 0
        while L < n and vals[L] == MV:
            L += 1
        k = 0
        while L + k < n and vals[L + k] == BG:
            k += 1
        if k == 0:
            continue
        for i in range(k):
            out[line[i]] = BG
        for i in range(k, k + L):
            out[line[i]] = MV
    return out.tolist()
''')
    return ''.join(src)
