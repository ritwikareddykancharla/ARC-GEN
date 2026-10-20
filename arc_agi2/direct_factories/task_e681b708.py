def build_program(d4, palette):
    # The mechanism is fully D4-isotropic:
    #  - rooms are 4-connected open regions;
    #  - votes come from the 8-neighbourhood ring, which includes diagonal corner markers;
    #  - majority is counted over marker cells.
    # So no axis or direction needs specialising for d4.
    # Colour roles are specialised directly as visible constants:
    #  - background = palette[0];
    #  - wall line colour = palette[1];
    #  - every other colour is a marker.
    bg = int(palette[0])
    line = int(palette[1])
    src = '''import numpy as np
from collections import deque

BG = __BG__
LINE = __LINE__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    # Dots: line-coloured cells whose 4-neighbours (inside the grid) are all background.
    dot = np.zeros((H, W), dtype=bool)
    for y in range(H):
        for x in range(W):
            if g[y, x] != LINE:
                continue
            iso = True
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and g[yy, xx] != BG:
                    iso = False
                    break
            if iso:
                dot[y, x] = True
    open_mask = (g == BG) | dot
    seen = np.zeros((H, W), dtype=bool)
    for sy in range(H):
        for sx in range(W):
            if not open_mask[sy, sx] or seen[sy, sx]:
                continue
            # Flood-fill one room (4-connected open space).
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            comp = []
            while q:
                cy, cx = q.popleft()
                comp.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and open_mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            dots = [(y, x) for (y, x) in comp if dot[y, x]]
            if not dots:
                continue
            # Marker cells in the ring around the room, corners included.
            # Each marker cell is counted once.
            marker_cells = set()
            for (y, x) in comp:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W:
                            v = int(g[yy, xx])
                            if v != BG and v != LINE:
                                marker_cells.add((yy, xx))
            if not marker_cells:
                continue
            counts = {}
            for (yy, xx) in marker_cells:
                v = int(g[yy, xx])
                counts[v] = counts.get(v, 0) + 1
            best = max(counts.values())
            winners = sorted(c for c, n in counts.items() if n == best)
            # The generator rejects tied rooms, so winners has a single entry in-domain.
            col = winners[0]
            for (y, x) in dots:
                out[y, x] = col
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__LINE__', str(line))
