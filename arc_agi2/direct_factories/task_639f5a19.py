def build_program(d4, palette):
    q = [[6, 1], [2, 3]]
    if d4 >= 4:
        q = [[r[1], r[0]] for r in q]
    for _ in range(d4 % 4):
        q = [[q[1][0], q[0][0]], [q[1][1], q[0][1]]]
    TL = palette[q[0][0]]
    TR = palette[q[0][1]]
    BL = palette[q[1][0]]
    BR = palette[q[1][1]]
    RECT = palette[8]
    CENTER = palette[4]
    lines = []
    lines.append('RECT = %d' % RECT)
    lines.append('CENTER = %d' % CENTER)
    lines.append('TL = %d' % TL)
    lines.append('TR = %d' % TR)
    lines.append('BL = %d' % BL)
    lines.append('BR = %d' % BR)
    body = '''
from collections import deque

def _components(g, colour):
    h = len(g)
    w = len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == colour and not seen[y][x]:
                seen[y][x] = True
                dq = deque([(y, x)])
                cells = []
                while dq:
                    cy, cx = dq.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == colour:
                            seen[ny][nx] = True
                            dq.append((ny, nx))
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    out = [row[:] for row in g]
    for cells in _components(g, RECT):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        h = y1 - y0 + 1
        w = x1 - x0 + 1
        my = y0 + h // 2
        mx = x0 + w // 2
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if y < my:
                    out[y][x] = TL if x < mx else TR
                else:
                    out[y][x] = BL if x < mx else BR
        for y in range(y0 + 2, y1 - 1):
            for x in range(x0 + 2, x1 - 1):
                out[y][x] = CENTER
    return out
'''
    return '\n'.join(lines) + '\n' + body
