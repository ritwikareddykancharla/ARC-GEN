def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    base = [
        (((1, 1, 1), (1, 1, 1)), 5),
        (((0, 1, 0), (1, 1, 1), (0, 1, 0)), 3),
        (((1, 1, 0), (0, 1, 1)), 8),
        (((1,), (1,), (1,)), 2),
        (((1, 1), (0, 1)), 4),
        (((1,), (1,)), 9),
    ]
    def tf(shape):
        g = [list(r) for r in shape]
        if d4 >= 4:
            g = [r[::-1] for r in g]
        for _ in range(d4 % 4):
            g = [list(r) for r in zip(*g[::-1])]
        return tuple(tuple(int(v) for v in r) for r in g)
    table = {}
    size_fb = {}
    for shape, col in base:
        table[tf(shape)] = pal[col]
        s = sum(sum(r) for r in shape)
        if s not in size_fb:
            size_fb[s] = pal[col]
    template = '''BG = __BG__
FG = __FG__
TABLE = __TABLE__
SIZE_FALLBACK = __SIZE__

def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if g[y][x] != FG or seen[y][x]:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == FG:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            y0 = min(c[0] for c in cells)
            y1 = max(c[0] for c in cells)
            x0 = min(c[1] for c in cells)
            x1 = max(c[1] for c in cells)
            mask = [[0] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
            for cy, cx in cells:
                mask[cy - y0][cx - x0] = 1
            key = tuple(tuple(r) for r in mask)
            col = TABLE.get(key)
            if col is None:
                col = SIZE_FALLBACK.get(len(cells))
            if col is None:
                continue
            for cy, cx in cells:
                out[cy][cx] = col
    return out
'''
    prog = template.replace('__BG__', repr(pal[7]))
    prog = prog.replace('__FG__', repr(pal[6]))
    prog = prog.replace('__TABLE__', repr(table))
    prog = prog.replace('__SIZE__', repr(size_fb))
    return prog
