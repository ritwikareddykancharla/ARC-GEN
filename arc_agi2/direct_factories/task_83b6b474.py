TEMPLATE = '''import numpy as np
from collections import Counter


def _components(g, colour):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == colour and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == colour:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out


def _pieces(g, bg):
    pieces = []
    for colour in sorted(set(g.ravel().tolist()) - {bg}):
        for cells in _components(g, colour):
            cells = sorted(cells)
            ay, ax = cells[0]
            pieces.append((colour, [(y - ay, x - ax) for (y, x) in cells]))
    return pieces


def _tilings(pieces, N, limit):
    # Exhaustive exact cover of the N x N ring by translated pieces.
    border = [(y, x) for y in range(N) for x in range(N) if y in (0, N - 1) or x in (0, N - 1)]
    bset = set(border)
    covered = set()
    used = [False] * len(pieces)
    placement = [None] * len(pieces)
    found = []

    def search():
        if len(found) >= limit:
            return
        free = None
        for c in border:
            if c not in covered:
                free = c
                break
        if free is None:
            if all(used):
                found.append(list(placement))
            return
        cy, cx = free
        for i in range(len(pieces)):
            if used[i]:
                continue
            cells = [(cy + dy, cx + dx) for (dy, dx) in pieces[i][1]]
            if all(c in bset and c not in covered for c in cells):
                covered.update(cells)
                used[i] = True
                placement[i] = cells
                search()
                covered.difference_update(cells)
                used[i] = False
                placement[i] = None

    search()
    return found


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    pieces = _pieces(g, bg)
    total = sum(len(rel) for _, rel in pieces)
    N = max(1, total // 4 + 1)
    out = np.full((N, N), bg, dtype=int)
    sols = _tilings(pieces, N, 2)
    if len(sols) != 1:
        raise ValueError("Expected one uniquely determined ring assembly")
    if sols:
        for (colour, _), cells in zip(pieces, sols[0]):
            for (y, x) in cells:
                out[y, x] = colour
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism is D4- and palette-equivariant: the output ring is invariant
    # under every D4 map, and pieces are only translated, so a translation-only
    # tiling of the visible ring, using visible colours, is already the
    # mechanism in visible coordinates. No constants need specialising.
    return TEMPLATE
