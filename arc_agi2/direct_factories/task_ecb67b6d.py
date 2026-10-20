def build_program(d4, palette):
    fg = int(palette[5])
    rc = int(palette[8])
    head = 'FG = %d\nRC = %d\n' % (fg, rc)
    body = '''
from collections import deque


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    # Cells lying on any straight diagonal run of three FG cells.
    # Both diagonal directions are checked, and that set is closed under
    # every rotation and reflection.
    onrun = set()
    for y in range(H):
        for x in range(W):
            for dy, dx in ((1, 1), (1, -1)):
                pts = [(y + k * dy, x + k * dx) for k in range(3)]
                if all(0 <= py < H and 0 <= px < W and g[py][px] == FG for py, px in pts):
                    onrun.update(pts)
    out = [row[:] for row in g]
    seen = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if g[y][x] != FG or seen[y][x]:
                continue
            seen[y][x] = True
            q = deque([(y, x)])
            comp = []
            while q:
                cy, cx = q.popleft()
                comp.append((cy, cx))
                for ddy in (-1, 0, 1):
                    for ddx in (-1, 0, 1):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == FG:
                            seen[ny][nx] = True
                            q.append((ny, nx))
            if any(c in onrun for c in comp):
                for cy, cx in comp:
                    out[cy][cx] = RC
    return out
'''
    return head + body
