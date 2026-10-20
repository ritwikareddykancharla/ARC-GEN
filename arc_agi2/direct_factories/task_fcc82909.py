def build_program(d4, palette):
    k = int(d4) % 4
    # Original tail direction is DOWN (+1 row). Horizontal row-reversal (d4>=4) leaves
    # vertical directions unchanged; each clockwise rotation maps down->left->up->right.
    dr, dc = [(1, 0), (0, -1), (-1, 0), (0, 1)][k]
    bg = int(palette[0])
    tail = int(palette[3])
    template = '''
BG = __BG__
TAIL = __TAIL__
DR = __DR__
DC = __DC__

def solve(demonstrations, grid):
    g = [list(int(v) for v in row) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != BG and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] != BG:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    for cells in comps:
        r0 = min(c[0] for c in cells)
        r1 = max(c[0] for c in cells)
        c0 = min(c[1] for c in cells)
        c1 = max(c[1] for c in cells)
        n = len(set(g[y][x] for y, x in cells))
        targets = []
        if DR == 1:
            for y in range(r1 + 1, r1 + 1 + n):
                for x in range(c0, c1 + 1):
                    targets.append((y, x))
        elif DR == -1:
            for y in range(r0 - n, r0):
                for x in range(c0, c1 + 1):
                    targets.append((y, x))
        elif DC == 1:
            for x in range(c1 + 1, c1 + 1 + n):
                for y in range(r0, r1 + 1):
                    targets.append((y, x))
        else:
            for x in range(c0 - n, c0):
                for y in range(r0, r1 + 1):
                    targets.append((y, x))
        for y, x in targets:
            if 0 <= y < H and 0 <= x < W and out[y][x] == BG:
                out[y][x] = TAIL
    return out
'''
    return (template.replace('__BG__', repr(bg))
                    .replace('__TAIL__', repr(tail))
                    .replace('__DR__', repr(dr))
                    .replace('__DC__', repr(dc)))
