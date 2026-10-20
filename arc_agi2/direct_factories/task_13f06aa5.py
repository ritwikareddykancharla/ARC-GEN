PROGRAM = '''
def solve(demonstrations, grid):
    ZERO = __ZERO__
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return [row[:] for row in g]
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(sorted(counts), key=lambda c: counts[c])
    out = [row[:] for row in g]
    seen = [[False] * W for _ in range(H)]
    rows_hit = []
    cols_hit = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == bg or seen[y][x]:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + ddy, cx + ddx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] != bg:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(cells) < 4:
                continue
            cc = {}
            for cy, cx in cells:
                cc[g[cy][cx]] = cc.get(g[cy][cx], 0) + 1
            if len(cc) < 2:
                continue
            special = min(sorted(cc), key=lambda c: cc[c])
            sp = sorted(p for p in cells if g[p[0]][p[1]] == special)
            body = [p for p in cells if g[p[0]][p[1]] != special]
            sy, sx = sp[0]
            n = len(body)
            vr = sy * n - sum(p[0] for p in body)
            vc = sx * n - sum(p[1] for p in body)
            if vr == 0 and vc == 0:
                continue
            if abs(vr) >= abs(vc):
                dy = (vr > 0) - (vr < 0)
                dx = 0
            else:
                dy = 0
                dx = (vc > 0) - (vc < 0)
            cy, cx = sy + 2 * dy, sx + 2 * dx
            while 0 <= cy < H and 0 <= cx < W:
                out[cy][cx] = special
                cy += 2 * dy
                cx += 2 * dx
            if dy != 0:
                r = 0 if dy < 0 else H - 1
                for c in range(W):
                    out[r][c] = special
                if r not in rows_hit:
                    rows_hit.append(r)
            else:
                c = 0 if dx < 0 else W - 1
                for r in range(H):
                    out[r][c] = special
                if c not in cols_hit:
                    cols_hit.append(c)
    for r in rows_hit:
        for c in cols_hit:
            out[r][c] = ZERO
    return out
'''

def build_program(d4, palette):
    zero = int(palette[0])
    return PROGRAM.replace('__ZERO__', str(zero))
