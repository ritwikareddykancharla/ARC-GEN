def build_program(d4, palette):
    bg = int(palette[0])
    noise = int(palette[5])
    template = r'''
import numpy as np
from collections import deque

# Colour roles specialised from the palette: original background 0 and grey noise 5.
BG = __BG__
NOISE = __NOISE__
_STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(mask):
    H, W = mask.shape
    seen = np.zeros((H, W), bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in _STEPS:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Holes: background components that do not reach the visible grid border.
    hole_cells = set()
    for comp in _components(g == BG):
        if any(y == 0 or x == 0 or y == H - 1 or x == W - 1 for y, x in comp):
            continue
        hole_cells.update(comp)
    # Pieces: single-colour components (not noise) that do not touch any hole.
    pieces = []
    for col in sorted(set(g.ravel().tolist()) - {BG, NOISE}):
        for cells in _components(g == col):
            touching = False
            for y, x in cells:
                for dy, dx in _STEPS:
                    if (y + dy, x + dx) in hole_cells:
                        touching = True
                        break
                if touching:
                    break
            if touching:
                continue
            ay, ax = cells[0]
            offs = tuple((y - ay, x - ax) for y, x in cells)
            pieces.append((col, cells, offs))
    # Group identical pieces (same colour and shape) so the search does not
    # explore permutations of interchangeable pieces.
    types = {}
    for idx, (col, cells, offs) in enumerate(pieces):
        types.setdefault((col, offs), []).append(idx)
    tkeys = sorted(types.keys(), key=lambda k: (-len(k[1]), k[0], k[1]))
    counts = [len(types[k]) for k in tkeys]
    placed = []
    failed = set()

    def rec(unc):
        if not unc:
            return True
        key = (unc, tuple(counts))
        if key in failed:
            return False
        t = min(unc)  # first uncovered hole cell in visible reading order
        for i, k in enumerate(tkeys):
            if counts[i] == 0:
                continue
            place = frozenset((t[0] + dy, t[1] + dx) for dy, dx in k[1])
            if place <= unc:
                counts[i] -= 1
                placed.append((i, t))
                if rec(unc - place):
                    return True
                placed.pop()
                counts[i] += 1
        failed.add(key)
        return False

    out = g.copy()
    out[out == NOISE] = BG
    if not hole_cells:
        return out.tolist()
    total_piece = sum(len(p[1]) for p in pieces)
    if total_piece < len(hole_cells):
        return out.tolist()
    if not rec(frozenset(hole_cells)):
        return out.tolist()
    ptr = [0] * len(tkeys)
    moves = []
    for i, t in placed:
        pidx = types[tkeys[i]][ptr[i]]
        ptr[i] += 1
        moves.append((pidx, t))
    for pidx, t in moves:
        for y, x in pieces[pidx][1]:
            out[y, x] = BG
    for pidx, t in moves:
        col, cells, offs = pieces[pidx]
        for dy, dx in offs:
            out[t[0] + dy, t[1] + dx] = col
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__NOISE__', str(noise))
