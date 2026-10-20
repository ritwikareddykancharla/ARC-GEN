def build_program(d4, palette):
    bg = int(palette[0])
    mk = int(palette[1])
    src = '''
BG = %d
MK = %d


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    # every marker is erased first; in-frame markers are repainted below
    for y in range(H):
        for x in range(W):
            if g[y][x] == MK:
                out[y][x] = BG
    # 4-connected single-colour components of non-background, non-marker colours
    seen = [[False] * W for _ in range(H)]
    corners = {}
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if seen[y][x] or c == BG or c == MK:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(cells) != 3:
                continue
            ys = [p[0] for p in cells]
            xs = [p[1] for p in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            if y1 - y0 != 1 or x1 - x0 != 1:
                continue
            cs = set(cells)
            missing = [(a, b) for a in (y0, y1) for b in (x0, x1) if (a, b) not in cs]
            if len(missing) != 1:
                continue
            my, mx = missing[0]
            ey, ex = y0 + y1 - my, x0 + x1 - mx  # elbow opposite the gap
            key = ('T' if ey == y0 else 'B') + ('L' if ex == x0 else 'R')
            d = corners.setdefault(c, {'TL': set(), 'TR': set(), 'BL': set(), 'BR': set()})
            d[key].add((ey, ex))
    for c, d in corners.items():
        for (ty, tx) in sorted(d['TL']):
            trs = [p[1] for p in d['TR'] if p[0] == ty and p[1] > tx]
            bls = [p[0] for p in d['BL'] if p[1] == tx and p[0] > ty]
            if not trs or not bls:
                continue
            rx = min(trs)
            by = min(bls)
            if (by, rx) not in d['BR']:
                continue
            h = by - ty + 1
            w = rx - tx + 1
            for y in range(ty, by + 1):
                for x in range(tx, rx + 1):
                    if g[y][x] != MK:
                        continue
                    out[y][x] = MK
                    if w > h:
                        out[y][tx + rx - x] = MK
                    elif h > w:
                        out[ty + by - y][x] = MK
    return out
''' % (bg, mk)
    return src
