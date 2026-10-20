def build_program(d4, palette):
    # Specialize the scan directions in visible coordinates, without wrappers.
    def direction(dr, dc):
        if int(d4) >= 4:
            dc = -dc
        for _ in range(int(d4) % 4):
            dr, dc = dc, -dr
        return dr, dc
    down = direction(1, 0)
    right = direction(0, 1)
    source = '''import numpy as np

BG = __BG__
SHAPE = __SHAPE__
DOWN = __DOWN__
RIGHT = __RIGHT__


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    shape = np.argwhere(g == SHAPE)
    markers = np.argwhere((g != BG) & (g != SHAPE))
    out = np.full_like(g, BG)
    if not len(shape):
        return out.tolist()
    colour = SHAPE
    if len(markers):
        distances = np.abs(markers[:, None, :] - shape[None, :, :]).max(axis=2).min(axis=1)
        # The episode gate must establish decisions depending on this scan;
        # orientation metadata is never shown to the student.
        index = min(range(len(markers)), key=lambda i: (
            int(distances[i]),
            int(markers[i, 0]) * DOWN[0] + int(markers[i, 1]) * DOWN[1],
            int(markers[i, 0]) * RIGHT[0] + int(markers[i, 1]) * RIGHT[1]))
        colour = int(g[tuple(markers[index])])
    out[g == SHAPE] = colour
    return out.tolist()
'''
    return (source.replace('__BG__', str(int(palette[0])))
            .replace('__SHAPE__', str(int(palette[5])))
            .replace('__DOWN__', repr(down)).replace('__RIGHT__', repr(right)))
