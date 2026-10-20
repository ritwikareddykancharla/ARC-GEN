TEMPLATE = '''import numpy as np

BG = __BG__
FG = __FG__
SQ_COL = __SQ__
BAR_COL = __BAR__

# Bricks anchored at their first cell in VISIBLE reading order
# (top-to-bottom, then left-to-right): 2x2 square, horizontal 1x3 bar,
# vertical 3x1 bar. This brick set is closed under every D4 transform.
SHAPES = (
    (((0, 0), (0, 1), (1, 0), (1, 1)), True),
    (((0, 0), (0, 1), (0, 2)), False),
    (((0, 0), (1, 0), (2, 0)), False),
)


def _tile(cells):
    shape = set(cells)
    n = len(cells)
    used = set()
    placed = []

    def rec(i):
        while i < n and cells[i] in used:
            i += 1
        if i == n:
            return True
        y, x = cells[i]
        for offs, is_sq in SHAPES:
            cs = [(y + dy, x + dx) for dy, dx in offs]
            if all(c in shape and c not in used for c in cs):
                used.update(cs)
                placed.append((cs, is_sq))
                if rec(i + 1):
                    return True
                used.difference_update(cs)
                placed.pop()
        return False

    if rec(0):
        return placed
    return None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    cells = [(y, x) for y in range(H) for x in range(W) if g[y, x] == FG]
    if not cells:
        cells = [(y, x) for y in range(H) for x in range(W) if g[y, x] != BG]
    out = g.copy()
    placed = _tile(cells)
    if placed is not None:
        for cs, is_sq in placed:
            for (y, x) in cs:
                out[y, x] = SQ_COL if is_sq else BAR_COL
    return out.tolist()
'''


def build_program(d4, palette):
    # The brick vocabulary {2x2 square, 1x3 bar, 3x1 bar} maps onto itself
    # under every D4 transform (horizontal and vertical bars swap roles), and
    # the exact cover is searched directly in visible coordinates. So d4
    # does not alter the emitted mechanism; only colour roles are specialised.
    src = TEMPLATE
    src = src.replace("__BG__", repr(int(palette[0])))
    src = src.replace("__FG__", repr(int(palette[5])))
    src = src.replace("__SQ__", repr(int(palette[8])))
    src = src.replace("__BAR__", repr(int(palette[2])))
    return src
