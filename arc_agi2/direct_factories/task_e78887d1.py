def build_program(d4, palette):
    # Canonical frame: bands are stacked downwards (+row), so the last band is the lowest one.
    # Slots run left to right (+col), and output slot i takes its shape from slot i+1.
    br, bc = 1, 0
    sr, sc = 0, 1
    if d4 >= 4:
        # Reversing each row negates the column component of every direction.
        bc, sc = -bc, -sc
    for _ in range(d4 % 4):
        # A clockwise rotation maps (r, c) to (c, H-1-r), so a direction (dr, dc) becomes (dc, -dr).
        br, bc = bc, -br
        sr, sc = sc, -sr
    rows = (bc == 0)
    if rows:
        last_high = br > 0
        succ = sc
    else:
        last_high = bc > 0
        succ = sr
    bg = int(palette[0])
    header = 'BG = %d\nBANDS_ARE_ROWS = %s\nLAST_HIGH = %s\nSUCC = %d\n' % (bg, rows, last_high, succ)
    body = '''
def _runs(idx):
    runs = []
    for i in idx:
        if runs and i == runs[-1][-1] + 1:
            runs[-1].append(i)
        else:
            runs.append([i])
    return runs


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if BANDS_ARE_ROWS:
        used = [i for i in range(H) if np.any(g[i, :] != BG)]
        L = W
    else:
        used = [j for j in range(W) if np.any(g[:, j] != BG)]
        L = H
    if not used:
        return g.tolist()
    runs = _runs(used)
    band = runs[-1] if LAST_HIGH else runs[0]
    a0 = band[0]
    a1 = band[-1] + 1
    h = a1 - a0
    step = h + 1
    n = max(1, (L + 1) // step)
    if BANDS_ARE_ROWS:
        sub = g[a0:a1, :]
    else:
        sub = g[:, a0:a1]
    out = np.full(sub.shape, BG, dtype=int)

    def piece(arr, k):
        s = k * step
        if BANDS_ARE_ROWS:
            return arr[:, s:s + h]
        return arr[s:s + h, :]

    colours = []
    for k in range(n):
        vals = piece(g, k)
        vals = vals[vals != BG].tolist()
        if vals:
            cnt = Counter(vals)
            best = max(cnt.values())
            colours.append(min(c for c in cnt if cnt[c] == best))
        else:
            colours.append(None)
    for k in range(n):
        if colours[k] is None:
            continue
        m = piece(sub, (k + SUCC) % n) != BG
        tgt = piece(out, k)
        if tgt.shape != m.shape:
            continue
        tgt[m] = colours[k]
    return out.tolist()
'''
    return 'import numpy as np\nfrom collections import Counter\n' + header + body
