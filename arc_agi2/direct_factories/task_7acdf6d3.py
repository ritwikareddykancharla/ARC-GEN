def build_program(d4, palette):
    bg = int(palette[7])
    ca = int(palette[2])
    cb = int(palette[9])
    scan_columns = (int(d4) % 4) in (1, 3)
    src = '''import numpy as np
from collections import deque

BG = __BG__
CUP_FILL_COLOURS = (__CA__, __CB__)
# Cups open along the canonical vertical axis. The capacity metric counts
# background cells strictly between the extreme cup cells of each line that is
# perpendicular to that axis. In visible coordinates this line is a
# __LINEWORD__.
SCAN_COLUMNS = __SCANCOLS__


def _components8(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
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
                out.append(sorted(cells))
    return out


def _interior(g, comp):
    lines = {}
    for y, x in comp:
        if SCAN_COLUMNS:
            lines.setdefault(x, []).append(y)
        else:
            lines.setdefault(y, []).append(x)
    cells = []
    for key in sorted(lines):
        ps = lines[key]
        for p in range(min(ps) + 1, max(ps)):
            if SCAN_COLUMNS:
                y, x = p, key
            else:
                y, x = key, p
            if g[y, x] == BG:
                cells.append((y, x))
    return cells


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    present = [int(c) for c in np.unique(g) if int(c) != BG]
    colours = [c for c in CUP_FILL_COLOURS if c in present]
    colours += [c for c in present if c not in colours]
    candidates = []
    for cup in colours:
        for fill in colours:
            if fill == cup:
                continue
            n = int((g == fill).sum())
            if n == 0:
                continue
            for comp in _components8(g == cup):
                inter = _interior(g, comp)
                if inter and len(inter) == n:
                    candidates.append((cup, fill, inter))
    if not candidates:
        return out.tolist()
    cup, fill, inter = candidates[0]
    out[g == fill] = BG
    for y, x in inter:
        out[y, x] = fill
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__CA__', str(ca))
    src = src.replace('__CB__', str(cb))
    src = src.replace('__SCANCOLS__', 'True' if scan_columns else 'False')
    src = src.replace('__LINEWORD__', 'column' if scan_columns else 'row')
    return src
