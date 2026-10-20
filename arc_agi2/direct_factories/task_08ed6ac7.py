def build_program(d4, palette):
    bg = int(palette[0])
    grey = int(palette[5])
    rank_cols = [int(palette[k]) for k in range(1, 10)]
    # Original bars are vertical (columns). Odd rotation counts make them horizontal (rows).
    vertical = (int(d4) % 4) % 2 == 0
    src = []
    src.append('import numpy as np')
    src.append('BG = %d' % bg)
    src.append('GREY = %d' % grey)
    src.append('RANK_COLOURS = %r' % (rank_cols,))
    src.append('VERTICAL = %r' % (vertical,))
    src.append('''
def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    bars = []
    for cells in _components(g == GREY):
        if VERTICAL:
            # bar length measured along rows; tie-break by column position
            pos = min(c[1] for c in cells)
            length = len(set(c[0] for c in cells))
        else:
            # bar length measured along columns; tie-break by row position
            pos = min(c[0] for c in cells)
            length = len(set(c[1] for c in cells))
        bars.append((-length, -len(cells), pos, cells))
    bars.sort(key=lambda b: (b[0], b[1], b[2]))
    for rank, b in enumerate(bars):
        if rank >= len(RANK_COLOURS):
            break
        col = RANK_COLOURS[rank]
        for (y, x) in b[3]:
            out[y, x] = col
    return out.tolist()
''')
    return '\n'.join(src)
