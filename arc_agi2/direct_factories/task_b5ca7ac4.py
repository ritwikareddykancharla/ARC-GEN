TEMPLATE = '''import numpy as np
from collections import Counter

FRAME_A = __FA__
DIR_A = "__DA__"
FRAME_B = __FB__
DIR_B = "__DB__"


def _background(g):
    return int(Counter(g.ravel().tolist()).most_common(1)[0][0])


def _find_squares(g, bg):
    H, W = g.shape
    used = np.zeros(g.shape, dtype=bool)
    squares = []
    for y in range(H - 4):
        for x in range(W - 4):
            if used[y:y + 5, x:x + 5].any():
                continue
            blk = g[y:y + 5, x:x + 5]
            border = np.concatenate([blk[0], blk[4], blk[1:4, 0], blk[1:4, 4]])
            inner = blk[1:4, 1:4]
            c = int(border[0])
            ic = int(inner[0, 0])
            if c == bg or not (border == c).all() or not (inner == ic).all():
                continue
            if ic == c or ic == bg:
                continue
            used[y:y + 5, x:x + 5] = True
            squares.append({"pos": (y, x), "frame": c, "blk": blk.copy()})
    return squares


def _slide(group, direction, H, W):
    along = 1 if direction in ("left", "right") else 0
    perp = 1 - along
    toward_zero = direction in ("left", "up")
    limit = (W if along == 1 else H) - 5
    order = sorted(group, key=lambda s: s["pos"][along], reverse=not toward_zero)
    placed = []
    for s in order:
        p = s["pos"][perp]
        blockers = [q for q in placed if abs(q[perp] - p) < 5]
        if toward_zero:
            n = max([q[along] + 5 for q in blockers], default=0)
        else:
            n = min([q[along] - 5 for q in blockers], default=limit)
        new = [0, 0]
        new[perp] = p
        new[along] = n
        new = (new[0], new[1])
        placed.append(new)
        s["new"] = new


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _background(g)
    squares = _find_squares(g, bg)
    for s in squares:
        s["new"] = s["pos"]
    _slide([s for s in squares if s["frame"] == FRAME_A], DIR_A, H, W)
    _slide([s for s in squares if s["frame"] == FRAME_B], DIR_B, H, W)
    out = np.full_like(g, bg)
    for s in squares:
        y, x = s["new"]
        if 0 <= y <= H - 5 and 0 <= x <= W - 5:
            out[y:y + 5, x:x + 5] = s["blk"]
    return out.tolist()
'''


def build_program(d4, palette):
    k = d4 % 4
    v = (0, 1) if d4 >= 4 else (0, -1)
    for _ in range(k):
        v = (v[1], -v[0])
    names = {(0, -1): 'left', (0, 1): 'right', (-1, 0): 'up', (1, 0): 'down'}
    da = names[v]
    db = names[(-v[0], -v[1])]
    fa = int(palette[8])
    fb = int(palette[2])
    return (TEMPLATE.replace('__FA__', str(fa)).replace('__FB__', str(fb))
            .replace('__DA__', da).replace('__DB__', db))
