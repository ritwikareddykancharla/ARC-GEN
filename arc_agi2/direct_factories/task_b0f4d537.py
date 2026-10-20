def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[4])
    frame = int(palette[5])
    template = '''import numpy as np

BG = __BG__
MARK = __MARK__
FRAME = __FRAME__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g == MARK)
    if ys.size == 0:
        return [list(map(int, row)) for row in grid]
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    box = g[y0:y1 + 1, x0:x1 + 1]
    H, W = box.shape
    # Each visible vertical line has markers on both the top and bottom edges of the canvas box.
    # Each visible horizontal line has markers on both the left and right edges.
    # The box corners are never markers.
    vcols = [c for c in range(1, W - 1) if box[0, c] == MARK or box[H - 1, c] == MARK]
    hrows = [r for r in range(1, H - 1) if box[r, 0] == MARK or box[r, W - 1] == MARK]
    # The legend is the bounding box of line colours (anything not background, marker or frame).
    m = (g != BG) & (g != MARK) & (g != FRAME)
    out = np.full((H, W), BG, dtype=int)
    ly, lx = np.where(m)
    if ly.size == 0:
        return out.tolist()
    leg = g[ly.min():ly.max() + 1, lx.min():lx.max() + 1]
    LH, LW = leg.shape
    # Legend vertical lines span the whole legend height, so they appear in its first row.
    # Legend horizontal lines span the whole legend width, so they appear in its first column.
    lv = [c for c in range(LW) if leg[0, c] != BG]
    lh = [r for r in range(LH) if leg[r, 0] != BG]
    # The k-th canvas line in visible order pairs with the k-th legend line in visible order, per axis.
    for r, lr in zip(hrows, lh):
        out[r, :] = leg[lr, 0]
    for c, lc in zip(vcols, lv):
        out[:, c] = leg[0, lc]
    # At each crossing, copy the legend's own crossing cell; this says which line is drawn on top.
    for r, lr in zip(hrows, lh):
        for c, lc in zip(vcols, lv):
            out[r, c] = leg[lr, lc]
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__MARK__', str(mark))
                    .replace('__FRAME__', str(frame)))
