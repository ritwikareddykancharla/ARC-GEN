def build_program(d4, palette):
    blob = int(palette[1])
    bg = int(palette[8])
    template = '''
BLOB = __BLOB__
BG = __BG__


def _components(g, H, W, colour):
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == colour and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == colour:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                out.append(sorted(cells))
    return out


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    for cells in _components(g, H, W, BLOB):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sides = [
            ((-1, 0), y0, sorted(x for y, x in cells if y == y0)),
            ((1, 0), y1, sorted(x for y, x in cells if y == y1)),
            ((0, -1), x0, sorted(y for y, x in cells if x == x0)),
            ((0, 1), x1, sorted(y for y, x in cells if x == x1)),
        ]
        for (dy, dx), edge, perp in sides:
            def line_at(k, dy=dy, dx=dx, edge=edge, perp=perp):
                if dy != 0:
                    yy = edge + dy * k
                    if not 0 <= yy < H:
                        return None
                    return [(yy, p) for p in perp]
                xx = edge + dx * k
                if not 0 <= xx < W:
                    return None
                return [(p, xx) for p in perp]
            stub = []
            k = 1
            while True:
                ln = line_at(k)
                if ln is None:
                    break
                vals = [g[y][x] for y, x in ln]
                if all(v != BG and v != BLOB for v in vals):
                    stub.append(vals)
                    k += 1
                else:
                    break
            if not stub:
                continue
            if line_at(len(stub) + 1) is None:
                continue  # strip already reaches the border: fired
            h = len(stub)
            k = h + 1
            while True:
                ln = line_at(k)
                if ln is None:
                    break
                vals = stub[(k - 1) % h]
                for (y, x), v in zip(ln, vals):
                    out[y][x] = v
                k += 1
    return out
'''
    return template.replace('__BLOB__', repr(blob)).replace('__BG__', repr(bg))
