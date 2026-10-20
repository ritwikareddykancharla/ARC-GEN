TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
VERT = __VERT__
ANCHOR_END = __AEND__
RAREST_LAST = __RLAST__


def _divider(g):
    h, w = g.shape
    votes = {}
    for y in range(h):
        v = int(g[y, 0])
        if v != BG and (g[y] == v).all():
            votes[v] = votes.get(v, 0) + 1
    for x in range(w):
        v = int(g[0, x])
        if v != BG and (g[:, x] == v).all():
            votes[v] = votes.get(v, 0) + 1
    if votes:
        return max(sorted(votes), key=lambda c: votes[c])
    cnt = {}
    for v in g.ravel().tolist():
        if v != BG:
            cnt[v] = cnt.get(v, 0) + 1
    if not cnt:
        return None
    return max(sorted(cnt), key=lambda c: cnt[c])


def _count_blocks(g, div):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    counts = {}
    for y in range(h):
        for x in range(w):
            v = int(g[y, x])
            if seen[y, x] or v == BG or v == div:
                continue
            seen[y, x] = True
            q = deque([(y, x)])
            while q:
                cy, cx = q.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == v:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            counts[v] = counts.get(v, 0) + 1
    return counts


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    div = _divider(g)
    counts = _count_blocks(g, div)
    if not counts:
        return [[BG]]
    items = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]))
    n = len(items)
    m = max(c for _, c in items)
    if VERT:
        out = np.full((m, n), BG, dtype=int)
    else:
        out = np.full((n, m), BG, dtype=int)
    for k, (col, c) in enumerate(items):
        slot = n - 1 - k if RAREST_LAST else k
        if VERT:
            if ANCHOR_END:
                out[m - c:, slot] = col
            else:
                out[:c, slot] = col
        else:
            if ANCHOR_END:
                out[slot, m - c:] = col
            else:
                out[slot, :c] = col
    return out.tolist()
'''


def build_program(d4, palette):
    d = int(d4) % 8
    # (bars_vertical, anchored_at_far_end, rarest_bar_at_far_end)
    table = {
        0: (0, 0, 0),
        1: (1, 0, 1),
        2: (0, 1, 1),
        3: (1, 1, 0),
        4: (0, 1, 0),
        5: (1, 1, 1),
        6: (0, 0, 1),
        7: (1, 0, 0),
    }
    v, a, r = table[d]
    bg = int(palette[0])
    prog = TEMPLATE.replace('__BG__', str(bg))
    prog = prog.replace('__VERT__', str(bool(v)))
    prog = prog.replace('__AEND__', str(bool(a)))
    prog = prog.replace('__RLAST__', str(bool(r)))
    return prog
