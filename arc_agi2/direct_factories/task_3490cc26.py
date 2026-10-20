def build_program(d4, palette):
    bg = int(palette[0])
    start = int(palette[2])
    block = int(palette[8])
    bridge = int(palette[7])
    src = '''import numpy as np

BG = __BG__
START = __START__
BLOCK = __BLOCK__
BRIDGE = __BRIDGE__


def _components(g, colour):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == colour and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == colour:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                out.append((min(ys), min(xs), max(ys), max(xs)))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    colours = sorted(set(g.ravel().tolist()) - {BG})
    # start colour first so its block is identified even if other colours appear
    if START in colours:
        colours.remove(START)
        colours = [START] + colours
    boxes = []
    start = None
    for col in colours:
        for b in _components(g, col):
            if col == START and start is None:
                start = len(boxes)
            boxes.append(b)
    if start is None:
        return out.tolist()
    visited = {start}
    cur = start
    while True:
        y0, x0, y1, x1 = boxes[cur]
        best = {}
        for j, (a0, b0, a1, b1) in enumerate(boxes):
            if j == cur:
                continue
            if a0 == y0 and a1 == y1:
                if b0 > x1:
                    d, gap = 'E', b0 - x1 - 1
                elif b1 < x0:
                    d, gap = 'W', x0 - b1 - 1
                else:
                    continue
            elif b0 == x0 and b1 == x1:
                if a0 > y1:
                    d, gap = 'S', a0 - y1 - 1
                elif a1 < y0:
                    d, gap = 'N', y0 - a1 - 1
                else:
                    continue
            else:
                continue
            if d not in best or gap < best[d][0]:
                best[d] = (gap, j)
        cands = [(gap, j, d) for d, (gap, j) in best.items() if j not in visited]
        if not cands:
            break
        cands.sort()
        gap, j, d = cands[0]
        a0, b0, a1, b1 = boxes[j]
        if d == 'E':
            out[y0:y1 + 1, x1 + 1:b0] = BRIDGE
        elif d == 'W':
            out[y0:y1 + 1, b1 + 1:x0] = BRIDGE
        elif d == 'S':
            out[y1 + 1:a0, x0:x1 + 1] = BRIDGE
        else:
            out[a1 + 1:y0, x0:x1 + 1] = BRIDGE
        visited.add(j)
        cur = j
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__START__', str(start))
    src = src.replace('__BLOCK__', str(block)).replace('__BRIDGE__', str(bridge))
    return src
