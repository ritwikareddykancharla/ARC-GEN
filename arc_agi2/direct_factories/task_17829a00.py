_COMMON = '''import numpy as np
from collections import Counter, deque

BG = __BG__
LOW_FIRST = __LOWFIRST__


def _mode(vals):
    return int(Counter(int(v) for v in vals).most_common(1)[0][0])


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                comps.append(sorted(cells))
    return comps
'''

_VERTICAL = '''

def solve(demonstrations, grid):
    # Border lines are the first and last ROWS; objects slide vertically.
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    low_c = _mode(g[0, :])
    high_c = _mode(g[H - 1, :])
    interior = np.zeros((H, W), dtype=bool)
    interior[1:H - 1, :] = True
    low_mask = (g == low_c) & interior
    high_mask = (g == high_c) & interior
    out[low_mask | high_mask] = BG

    def paint(mask, colour, toward_low):
        for comp in _components(mask):
            if toward_low:
                shift = 1 - min(r for r, _ in comp)
            else:
                shift = (H - 2) - max(r for r, _ in comp)
            orig = set(comp)
            moved = {(r + shift, c) for r, c in comp}
            wall = any(c == 0 or c == W - 1 for _, c in comp)
            cells = (orig | moved) if (wall and (orig & moved)) else moved
            for r, c in cells:
                if 0 <= r < H and 0 <= c < W:
                    out[r, c] = colour

    if LOW_FIRST:
        paint(low_mask, low_c, True)
        paint(high_mask, high_c, False)
    else:
        paint(high_mask, high_c, False)
        paint(low_mask, low_c, True)
    return out.tolist()
'''

_HORIZONTAL = '''

def solve(demonstrations, grid):
    # Border lines are the first and last COLUMNS; objects slide horizontally.
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    low_c = _mode(g[:, 0])
    high_c = _mode(g[:, W - 1])
    interior = np.zeros((H, W), dtype=bool)
    interior[:, 1:W - 1] = True
    low_mask = (g == low_c) & interior
    high_mask = (g == high_c) & interior
    out[low_mask | high_mask] = BG

    def paint(mask, colour, toward_low):
        for comp in _components(mask):
            if toward_low:
                shift = 1 - min(c for _, c in comp)
            else:
                shift = (W - 2) - max(c for _, c in comp)
            orig = set(comp)
            moved = {(r, c + shift) for r, c in comp}
            wall = any(r == 0 or r == H - 1 for r, _ in comp)
            cells = (orig | moved) if (wall and (orig & moved)) else moved
            for r, c in cells:
                if 0 <= r < H and 0 <= c < W:
                    out[r, c] = colour

    if LOW_FIRST:
        paint(low_mask, low_c, True)
        paint(high_mask, high_c, False)
    else:
        paint(high_mask, high_c, False)
        paint(low_mask, low_c, True)
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    # Where the original TOP border lands: 0->top, 1->right, 2->bottom, 3->left.
    # A horizontal pre-flip (d4>=4) keeps the top row on top and only swaps the
    # two side walls, which the rule treats symmetrically.
    if k == 0:
        body, low_first = _VERTICAL, True
    elif k == 1:
        body, low_first = _HORIZONTAL, False
    elif k == 2:
        body, low_first = _VERTICAL, False
    else:
        body, low_first = _HORIZONTAL, True
    bg = int(palette[7])
    src = _COMMON.replace('__BG__', str(bg)).replace('__LOWFIRST__', 'True' if low_first else 'False')
    return src + body
