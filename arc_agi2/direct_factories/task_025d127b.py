def build_program(d4, palette):
    # Canonical directions: 'down' (fixed base row lies at max +y) and 'right' (shift dir, wall at max +x).
    by, bx = 1, 0
    ry, rx = 0, 1
    if d4 >= 4:
        # reverse each row: x -> W-1-x, so delta (dy,dx) -> (dy,-dx)
        bx = -bx
        rx = -rx
    for _ in range(d4 % 4):
        # clockwise rotation: point (y,x)->(x,h-1-y), delta (dy,dx)->(dx,-dy)
        by, bx = bx, -by
        ry, rx = rx, -ry
    bg = int(palette[0])
    header = (
        'BG = ' + repr(bg) + '\n'
        'BY = ' + repr(by) + '\n'
        'BX = ' + repr(bx) + '\n'
        'RY = ' + repr(ry) + '\n'
        'RX = ' + repr(rx) + '\n'
    )
    body = '''
from collections import deque

def _components(g, h, w):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == BG or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            q.append((ny, nx))
            comps.append((col, cells))
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [[BG] * w for _ in range(h)]
    for col, cells in _components(g, h, w):
        maxb = max(y * BY + x * BX for y, x in cells)
        maxr = max(y * RY + x * RX for y, x in cells)
        moving = []
        # Stamp the fixed parts: the base edge (far along B) and the wall edge (far along R).
        for y, x in cells:
            if y * BY + x * BX == maxb or y * RY + x * RX == maxr:
                out[y][x] = col
            else:
                moving.append((y, x))
        # Shift the remaining cells one step along R, clamped at the wall.
        for y, x in moving:
            ny, nx = y + RY, x + RX
            if ny * RY + nx * RX > maxr:
                ny, nx = y, x
            if 0 <= ny < h and 0 <= nx < w:
                out[ny][nx] = col
    return out
'''
    return header + body
