TEMPLATE = r'''
BG = __BG__
FRAME = __FRAME__


def _l_pieces(g, H, W):
    seen = [[False] * W for _ in range(H)]
    pieces = []
    for y in range(H):
        for x in range(W):
            if seen[y][x] or g[y][x] == BG:
                continue
            col = g[y][x]
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(cells) != 3:
                continue
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            ya, xa = min(ys), min(xs)
            if max(ys) - ya != 1 or max(xs) - xa != 1:
                continue
            box = {(ya, xa), (ya, xa + 1), (ya + 1, xa), (ya + 1, xa + 1)}
            miss = (box - set(cells)).pop()
            if miss == (ya + 1, xa + 1):
                pieces.append(('TL', col, ya, xa))
            elif miss == (ya + 1, xa):
                pieces.append(('TR', col, ya, xa + 1))
            elif miss == (ya, xa + 1):
                pieces.append(('BL', col, ya + 1, xa))
            else:
                pieces.append(('BR', col, ya + 1, xa + 1))
    return pieces


def _find_rect(g, H, W):
    pieces = _l_pieces(g, H, W)
    by = {}
    for kind, col, y, x in pieces:
        by.setdefault((kind, y, x), []).append(col)
    cands = []
    for kind, col, y0, x0 in pieces:
        if kind != 'TL':
            continue
        for kind2, col2, y1, x1 in pieces:
            if kind2 != 'BR' or y1 - y0 < 3 or x1 - x0 < 3:
                continue
            for c3 in by.get(('TR', y0, x1), []):
                for c4 in by.get(('BL', y1, x0), []):
                    cols = [col, c3, c4, col2]
                    for fr in set(cols):
                        if cols.count(fr) == 3:
                            fill = [c for c in cols if c != fr][0]
                            score = 0 if fr == FRAME else 1
                            cands.append((score, y0, x0, y1, x1, fr, fill))
    if cands:
        cands.sort()
        return cands[0][1:]
    fc = [(y, x) for y in range(H) for x in range(W) if g[y][x] == FRAME]
    if not fc:
        return None
    Y0 = min(p[0] for p in fc)
    Y1 = max(p[0] for p in fc)
    X0 = min(p[1] for p in fc)
    X1 = max(p[1] for p in fc)
    odd = [g[y][x] for (y, x) in ((Y0, X0), (Y0, X1), (Y1, X0), (Y1, X1)) if g[y][x] != FRAME and g[y][x] != BG]
    fill = odd[0] if odd else FRAME
    return (Y0, X0, Y1, X1, FRAME, fill)


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    rect = _find_rect(g, H, W)
    if rect is None:
        return out
    Y0, X0, Y1, X1, frame, fill = rect
    for y in range(H):
        for x in range(W):
            if (Y0 <= y <= Y1 or X0 <= x <= X1) and g[y][x] == BG:
                out[y][x] = fill
    for x in range(X0, X1 + 1):
        out[Y0][x] = frame
        out[Y1][x] = frame
    for y in range(Y0, Y1 + 1):
        out[y][X0] = frame
        out[y][X1] = frame
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if v == BG:
                continue
            inr = Y0 <= y <= Y1
            inc = X0 <= x <= X1
            if inr and inc:
                continue
            if inr:
                dy, dx = 0, (-1 if x < X0 else 1)
            elif inc:
                dy, dx = (-1 if y < Y0 else 1), 0
            else:
                continue
            yy, xx = y + dy, x + dx
            while 0 <= yy < H and 0 <= xx < W and g[yy][xx] == BG:
                out[yy][xx] = v
                yy += dy
                xx += dx
    return out
'''


def build_program(d4, palette):
    bg = int(palette[0])
    fr = int(palette[8])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__FRAME__', str(fr))
