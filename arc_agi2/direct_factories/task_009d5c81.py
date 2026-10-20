def _d4_apply(rows, d4):
    a = [list(r) for r in rows]
    if d4 >= 4:
        a = [r[::-1] for r in a]
    for _ in range(d4 % 4):
        a = [list(r) for r in zip(*a[::-1])]
    return tuple(tuple(int(v) for v in r) for r in a)


def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    glyphs = [
        (["111", "101", "010"], 7),
        (["101", "010", "111"], 3),
        (["010", "111", "010"], 2),
    ]
    table = {}
    for shape, col in glyphs:
        rows = [[int(ch) for ch in s] for s in shape]
        table[_d4_apply(rows, d4)] = pal[col]
    bg = pal[0]
    draw = pal[8]
    sym = pal[1]
    src = []
    src.append("import numpy as np")
    src.append("BG = %d" % bg)
    src.append("DRAW = %d" % draw)
    src.append("SYM = %d" % sym)
    src.append("TABLE = %r" % (table,))
    src.append('''

def _key(g):
    m = (g == SYM)
    if not m.any():
        return None, m
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = m[y0:y1 + 1, x0:x1 + 1].astype(int)
    return tuple(tuple(int(v) for v in r) for r in sub), m


def _learn(demonstrations):
    learned = {}
    for d in demonstrations or []:
        try:
            gi = np.array(d["input"], dtype=int)
            go = np.array(d["output"], dtype=int)
            if gi.shape != go.shape:
                continue
            k, _ = _key(gi)
            dm = (gi == DRAW)
            if k is None or not dm.any():
                continue
            vals = go[dm]
            learned.setdefault(k, int(np.bincount(vals).argmax()))
        except Exception:
            continue
    return learned


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    table = dict(_learn(demonstrations))
    table.update(TABLE)
    k, m = _key(g)
    new = table.get(k) if k is not None else None
    if new is not None:
        out[g == DRAW] = new
    out[m] = BG
    return out.tolist()
''')
    return "\n".join(src)
