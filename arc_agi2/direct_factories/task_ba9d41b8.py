def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    s = 1 if d4 >= 4 else 0
    # Corners in clockwise order: TL, TR, BR, BL, as (is_bottom, is_right).
    # A horizontal flip sends TL to TR. Each clockwise quarter turn moves a corner one step clockwise.
    corners = [(0, 0), (0, 1), (1, 1), (1, 0)]
    bottom, right = corners[(s + k) % 4]
    bg = int(palette[0])
    header = (
        "import numpy as np\n"
        "from collections import deque\n"
        "BG = " + repr(bg) + "\n"
        "ANCHOR_BOTTOM = " + repr(bool(bottom)) + "\n"
        "ANCHOR_RIGHT = " + repr(bool(right)) + "\n"
    )
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if seen[y, x] or g[y, x] == BG:
                continue
            col = g[y, x]
            q = deque([(y, x)])
            seen[y, x] = True
            y0 = y1 = y
            x0 = x1 = x
            while q:
                cy, cx = q.popleft()
                if cy < y0: y0 = cy
                if cy > y1: y1 = cy
                if cx < x0: x0 = cx
                if cx > x1: x1 = cx
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            # The checkerboard is anchored at the box corner that is the image of the
            # original top-left corner. Cells whose parity matches that corner are cleared.
            ay = y1 if ANCHOR_BOTTOM else y0
            ax = x1 if ANCHOR_RIGHT else x0
            for yy in range(y0 + 1, y1):
                for xx in range(x0 + 1, x1):
                    if (yy - ay + xx - ax) % 2 == 0 and g[yy, xx] == col:
                        out[yy, xx] = BG
    return out.tolist()
'''
    return header + body
