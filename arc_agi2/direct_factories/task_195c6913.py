TEMPLATE = '''
def solve(demonstrations, grid):
    RY, RX = __RY__, __RX__
    UY, UX = __UY__, __UX__
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return g
    cnt = {}
    for row in g:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    bg = max(sorted(cnt), key=lambda c: cnt[c])
    seen = [[False] * W for _ in range(H)]
    blocks = []
    singles = []
    for sy in range(H):
        for sx in range(W):
            if seen[sy][sx] or g[sy][sx] == bg:
                continue
            col = g[sy][sx]
            seen[sy][sx] = True
            stack = [(sy, sx)]
            cells = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(cells) == 4:
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                if max(ys) - min(ys) == 1 and max(xs) - min(xs) == 1:
                    blocks.append((col, min(ys), min(xs)))
            elif len(cells) == 1:
                singles.append(cells[0])
    if not blocks:
        return g
    def bkey(b):
        return b[1] if UY != 0 else b[2]
    groups = {}
    for b in blocks:
        groups.setdefault(bkey(b), []).append(b)
    lk = max(sorted(groups), key=lambda k: len(groups[k]))
    legend = sorted(groups[lk], key=lambda b: RY * b[1] + RX * b[2])
    pat = [b[0] for b in legend]
    others = [b for b in blocks if bkey(b) != lk]
    mcol = others[0][0] if others else pat[-1]
    for col, y0, x0 in blocks:
        ring = {}
        for y in range(y0 - 1, y0 + 3):
            for x in range(x0 - 1, x0 + 3):
                if 0 <= y < H and 0 <= x < W and not (y0 <= y <= y0 + 1 and x0 <= x <= x0 + 1):
                    v = g[y][x]
                    ring[v] = ring.get(v, 0) + 1
        fill = max(sorted(ring), key=lambda c: ring[c]) if ring else bg
        for y in (y0, y0 + 1):
            for x in (x0, x0 + 1):
                g[y][x] = fill
    base = [row[:] for row in g]
    dirs = ((RY, RX), (UY, UX))
    for sy, sx in singles:
        fy, fx = sy + RY, sx + RX
        if not (0 <= fy < H and 0 <= fx < W):
            continue
        reg = base[fy][fx]
        y, x = sy, sx
        g[y][x] = pat[0]
        di = 0
        idx = 0
        guard = 4 * H * W + 10
        while guard > 0:
            guard -= 1
            dy, dx = dirs[di]
            ny, nx = y + dy, x + dx
            if not (0 <= ny < H and 0 <= nx < W):
                break
            if base[ny][nx] != reg:
                g[ny][nx] = mcol
                di ^= 1
                dy, dx = dirs[di]
                ny, nx = y + dy, x + dx
                if not (0 <= ny < H and 0 <= nx < W) or base[ny][nx] != reg:
                    break
            y, x = ny, nx
            idx += 1
            g[y][x] = pat[idx % len(pat)]
    return g
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    ry, rx = 0, 1
    uy, ux = -1, 0
    if d4 >= 4:
        rx = -rx
        ux = -ux
    for _ in range(d4 % 4):
        ry, rx = rx, -ry
        uy, ux = ux, -uy
    src = TEMPLATE
    src = src.replace('__RY__', str(ry)).replace('__RX__', str(rx))
    src = src.replace('__UY__', str(uy)).replace('__UX__', str(ux))
    return src
