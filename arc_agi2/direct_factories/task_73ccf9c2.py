def build_program(d4, palette):
    # The black background maps to palette[0]. Shapes may use any other colour.
    bg = int(palette[0])
    # In the original coordinates the test is left-right mirror symmetry.
    # D4 = rot^k after an optional row reversal. Row reversal commutes with the
    # left-right flip. One quarter turn conjugates the left-right flip into the
    # up-down flip. So the visible axis depends only on k % 2:
    #   k even: compare columns (left-right mirror)
    #   k odd:  compare rows (up-down mirror)
    mirror_rows = ((int(d4) % 4) % 2) == 1
    template = '''BG = __BG__
MIRROR_ROWS = __MIRROR_ROWS__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    best = None
    best_score = -1
    for y in range(h):
        for x in range(w):
            if g[y][x] == BG or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny = cy + dy
                        nx = cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
            y0 = min(c[0] for c in cells)
            y1 = max(c[0] for c in cells)
            x0 = min(c[1] for c in cells)
            x1 = max(c[1] for c in cells)
            H = y1 - y0 + 1
            W = x1 - x0 + 1
            mask = [[False] * W for _ in range(H)]
            for cy, cx in cells:
                mask[cy - y0][cx - x0] = True
            s = 0
            for r in range(H):
                for c in range(W):
                    if MIRROR_ROWS:
                        if mask[r][c] != mask[H - 1 - r][c]:
                            s += 1
                    else:
                        if mask[r][c] != mask[r][W - 1 - c]:
                            s += 1
            if s > best_score:
                best_score = s
                best = [[g[r][c] for c in range(x0, x1 + 1)] for r in range(y0, y1 + 1)]
    if best is None:
        return [row[:] for row in g]
    return best
'''
    return template.replace('__BG__', str(bg)).replace('__MIRROR_ROWS__', 'True' if mirror_rows else 'False')
