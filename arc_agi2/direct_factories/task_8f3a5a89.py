def build_program(d4, palette):
    BG = int(palette[8])
    ONE = int(palette[1])
    MARK = int(palette[6])
    FRAME = int(palette[7])
    d4 = int(d4) % 8
    # The 6 starts at the bottom-left corner. Track where that corner ends up
    # in visible coordinates. This is only a fallback; the 6 is found by colour.
    bottom, left = True, True
    if d4 >= 4:
        left = not left  # reversing each row swaps left and right
    for _ in range(d4 % 4):
        # A clockwise turn maps (r, c) to (c, H-1-r):
        # the left column becomes the top row, and the bottom row becomes the left column.
        bottom, left = (not left), bottom
    header = (
        'BG = %d\n'
        'ONE = %d\n'
        'MARK = %d\n'
        'FRAME = %d\n'
        'MARK_BOTTOM = %r\n'
        'MARK_LEFT = %r\n'
    ) % (BG, ONE, MARK, FRAME, bottom, left)
    body = '''
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return g
    corner = (H - 1 if MARK_BOTTOM else 0, 0 if MARK_LEFT else W - 1)
    marks = [(y, x) for y in range(H) for x in range(W) if g[y][x] == MARK]
    if marks:
        start = corner if corner in marks else marks[0]
    else:
        start = corner
    sy, sx = start
    # Region: background cells reachable from the 6 by 4-connected moves.
    # The 6 itself is not part of the region.
    region = [[False] * W for _ in range(H)]
    seen = {(sy, sx)}
    stack = [(sy, sx)]
    while stack:
        y, x = stack.pop()
        for dy, dx in N4:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in seen and g[ny][nx] == BG:
                seen.add((ny, nx))
                region[ny][nx] = True
                stack.append((ny, nx))

    def near(y, x, m):
        for dy, dx in N8:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and m[ny][nx]:
                return True
        return False

    # Objects: 8-connected components of non-background, non-marker cells.
    is_obj = [[g[y][x] != BG and g[y][x] != MARK for x in range(W)] for y in range(H)]
    done = [[False] * W for _ in range(H)]
    out = [row[:] for row in g]
    wall = [[False] * W for _ in range(H)]
    for y0 in range(H):
        for x0 in range(W):
            if not is_obj[y0][x0] or done[y0][x0]:
                continue
            comp = []
            done[y0][x0] = True
            st = [(y0, x0)]
            while st:
                y, x = st.pop()
                comp.append((y, x))
                for dy, dx in N8:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and is_obj[ny][nx] and not done[ny][nx]:
                        done[ny][nx] = True
                        st.append((ny, nx))
            if not any(near(y, x, region) for y, x in comp):
                # Not touching the region: erase the whole object.
                for y, x in comp:
                    out[y][x] = BG
            elif any(y == 0 or y == H - 1 or x == 0 or x == W - 1 for y, x in comp):
                # Surviving object on the grid border: it is a wall.
                for y, x in comp:
                    wall[y][x] = True
    # Frame: region cells on the border or 8-touching a wall cell.
    for y in range(H):
        for x in range(W):
            if region[y][x] and (y == 0 or y == H - 1 or x == 0 or x == W - 1 or near(y, x, wall)):
                out[y][x] = FRAME
    return out
'''
    return header + body
