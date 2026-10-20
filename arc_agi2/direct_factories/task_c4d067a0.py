def build_program(d4, palette):
    # Canonical directions: U = legend-row direction (down), V = along the block row (right).
    uy, ux = 1, 0
    vy, vx = 0, 1
    if d4 >= 4:
        ux, vx = -ux, -vx
    for _ in range(d4 % 4):
        uy, ux = ux, -uy
        vy, vx = vx, -vy
    head = 'UY, UX, VY, VX = %d, %d, %d, %d\n' % (uy, ux, vy, vx)
    body = '''
from collections import Counter, deque

def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == bg or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            out.append((col, cells))
    return out

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H, W = len(g), len(g[0])
    bg = Counter(v for r in g for v in r).most_common(1)[0][0]
    comps = _components(g, bg)
    # Legend corner: the visible corner from which U and V both point inward.
    cy = 0 if (UY + VY) > 0 else H - 1
    cx = 0 if (UX + VX) > 0 else W - 1
    p0y, p0x = cy + UY + VY, cx + UX + VX
    legend = {}
    blocks = []
    for col, cells in comps:
        if len(cells) == 1:
            y, x = cells[0]
            dy, dx = y - p0y, x - p0x
            a = dy * UY + dx * UX
            b = dy * VY + dx * VX
            if a >= 0 and b >= 0 and a % 2 == 0 and b % 2 == 0:
                legend[(a // 2, b // 2)] = col
        else:
            us = [y * UY + x * UX for y, x in cells]
            vs = [y * VY + x * VX for y, x in cells]
            blocks.append((min(vs), min(us), max(max(us) - min(us), max(vs) - min(vs)) + 1, col))
    if not legend or not blocks:
        return g
    blocks.sort()
    R = max(k[0] for k in legend) + 1
    C = max(k[1] for k in legend) + 1
    pv0, pu0, size, _ = blocks[0]
    step = blocks[1][0] - pv0 if len(blocks) > 1 else size + 1
    cols = [b[3] for b in blocks]
    k = len(cols)
    found = None
    for r in range(R):
        for c in range(C - k + 1):
            if all(legend.get((r, c + i), bg) == cols[i] for i in range(k)):
                found = (r, c)
                break
        if found:
            break
    if found is None:
        return g
    r0, c0 = found
    ou = pu0 - r0 * step
    ov = pv0 - c0 * step
    out = [row[:] for row in g]
    for (r, c), col in sorted(legend.items()):
        if col == bg:
            continue
        bu = ou + r * step
        bv = ov + c * step
        for i in range(size):
            for j in range(size):
                u = bu + i
                v = bv + j
                y = u * UY + v * VY
                x = u * UX + v * VX
                if 0 <= y < H and 0 <= x < W:
                    out[y][x] = col
    return out
'''
    return head + body
