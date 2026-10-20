def build_program(d4, palette):
    bg = int(palette[7])
    line = int(palette[8])
    mark = int(palette[9])
    horiz = (int(d4) % 2 == 1)
    header = (
        "import numpy as np\n"
        "from collections import deque\n\n"
        "BG = " + str(bg) + "\n"
        "LINE = " + str(line) + "\n"
        "MARK = " + str(mark) + "\n"
        "HORIZ = " + ("True" if horiz else "False") + "\n\n"
    )
    body = '''
def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def _order(cells):
    # order cells along the line axis (lines are horizontal when HORIZ)
    if HORIZ:
        return sorted(cells, key=lambda p: (p[1], p[0]))
    return sorted(cells, key=lambda p: (p[0], p[1]))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    mask = (g == LINE) | (g == MARK)
    lines = _components(mask)
    src = None
    for c in lines:
        if any(g[y, x] == MARK for y, x in c):
            src = _order(c)
            break
    if src is None:
        return g.tolist()
    L = len(src)
    k = sum(1 for y, x in src if g[y, x] == MARK)
    at_start = (g[src[0][0], src[0][1]] == MARK)
    for y, x in src:
        g[y, x] = LINE
    tgt = None
    for c in lines:
        if len(c) == L + 2:
            tgt = _order(c)
            break
    if tgt is None:
        return g.tolist()
    n = min(k + 1, len(tgt))
    seg = tgt[:n] if at_start else tgt[len(tgt) - n:]
    for y, x in seg:
        g[y, x] = MARK
    return g.tolist()
'''
    return header + body
