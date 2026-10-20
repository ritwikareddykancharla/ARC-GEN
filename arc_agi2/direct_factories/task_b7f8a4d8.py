def build_program(d4, palette):
    bg_const = int(palette[0])
    src = '''import numpy as np
from collections import Counter, deque

BG = __BG__

def _components(g, mask):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    objs = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                col = int(g[y, x])
                q = deque([(y, x)])
                seen[y, x] = True
                ys, xs = [], []
                while q:
                    cy, cx = q.popleft()
                    ys.append(cy)
                    xs.append(cx)
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx] and int(g[ny, nx]) == col:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                objs.append((col, min(ys), min(xs), max(ys), max(xs), len(ys)))
    return objs

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    bg = BG
    if not np.any(g == bg):
        border = list(g[0, :]) + list(g[-1, :]) + list(g[:, 0]) + list(g[:, -1])
        bg = int(Counter(int(v) for v in border).most_common(1)[0][0])
    # Frame colour: the non-background colour touching the background.
    cnt = Counter()
    for y in range(h):
        for x in range(w):
            v = int(g[y, x])
            if v == bg:
                continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and g[ny, nx] == bg:
                    cnt[v] += 1
                    break
    if not cnt:
        return out.tolist()
    frame = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    mask = (g != bg) & (g != frame)
    objs = _components(g, mask)
    if not objs:
        return out.tolist()
    ccount = Counter(o[0] for o in objs)
    cells = Counter()
    for o in objs:
        cells[o[0]] += o[5]
    normal = max(ccount, key=lambda c: (ccount[c], cells[c], -c))
    special = [o for o in objs if o[0] != normal]
    for c in sorted(set(o[0] for o in special)):
        group = [o for o in special if o[0] == c]
        for a in group:
            for b in group:
                if a is b:
                    continue
                # same row band: join horizontally
                if a[1] == b[1] and a[3] == b[3] and a[4] < b[2]:
                    for y in range(a[1], a[3] + 1):
                        for x in range(a[4] + 1, b[2]):
                            if g[y, x] == bg:
                                out[y, x] = c
                # same column band: join vertically
                if a[2] == b[2] and a[4] == b[4] and a[3] < b[1]:
                    for y in range(a[3] + 1, b[1]):
                        for x in range(a[2], a[4] + 1):
                            if g[y, x] == bg:
                                out[y, x] = c
    return out.tolist()
'''
    return src.replace('__BG__', str(bg_const))
