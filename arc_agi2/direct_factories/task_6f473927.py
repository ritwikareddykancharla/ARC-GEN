def build_program(d4, palette):
    shape = int(palette[2])
    bg = int(palette[0])
    fill = int(palette[8])
    # Edge indices: 0=left, 1=top, 2=right, 3=bottom. A clockwise rotation moves left->top->right->bottom->left.
    # The original column 0 is the left edge. A row reversal (d4>=4) moves it to the right edge before rotating.
    start = 2 if d4 >= 4 else 0
    edge = (start + (d4 % 4)) % 4
    src = '''import numpy as np

SHAPE = %d
BG = %d
FILL = %d
KEY_EDGE = %d  # visible edge corresponding to the constructor's column 0


def _edge_cells(g, e):
    if e == 0:
        return g[:, 0]
    if e == 1:
        return g[0, :]
    if e == 2:
        return g[:, -1]
    return g[-1, :]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    # If the shape touches KEY_EDGE, the new half is attached on that side, so the edge faces the seam.
    # Otherwise the new half is attached on the opposite side, where the shape touches in-domain.
    if bool((_edge_cells(g, KEY_EDGE) == SHAPE).any()):
        side = KEY_EDGE
    else:
        side = (KEY_EDGE + 2) %% 4
    if side in (0, 2):
        mirrored = g[:, ::-1]
    else:
        mirrored = g[::-1, :]
    comp = np.where(mirrored == SHAPE, BG, FILL)
    if side == 0:
        out = np.concatenate([comp, g], axis=1)
    elif side == 2:
        out = np.concatenate([g, comp], axis=1)
    elif side == 1:
        out = np.concatenate([comp, g], axis=0)
    else:
        out = np.concatenate([g, comp], axis=0)
    return out.astype(int).tolist()
''' % (shape, bg, fill, edge)
    return src
