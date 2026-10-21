"""Optional compiled version of the independent array clearance verifier.

This uses the original directional scan, not the bitboard target program.
Only the generation worker imports Numba; exported programs remain standalone.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def prune_array(grid, paint, limit, background, fill):
    height, width = grid.shape
    padded = np.full((height + 2, width + 2), background, dtype=np.int64)
    for r in range(height):
        for c in range(width):
            padded[r + 1, c + 1] = fill if paint[r, c] else grid[r, c]
    if limit:
        while True:
            removed = np.zeros(padded.shape, dtype=np.bool_)
            for rotation in range(4):
                view = np.rot90(padded, rotation)
                cut = np.zeros(view.shape, dtype=np.bool_)
                for r in range(2, view.shape[0] - 1):
                    c = 1
                    while c < view.shape[1] - 1:
                        if view[r, c] != fill:
                            c += 1
                            continue
                        start = c
                        while c < view.shape[1] - 1 and view[r, c] == fill:
                            c += 1
                        end = c
                        if end - start > limit or view[r, start - 1] != background or view[r, end] != background:
                            continue
                        exposed = True
                        for col in range(start, end):
                            if view[r - 1, col] != background:
                                exposed = False
                                break
                        if exposed:
                            for col in range(start, end):
                                cut[r, col] = True
                unrotated = np.rot90(cut, -rotation)
                for r in range(padded.shape[0]):
                    for c in range(padded.shape[1]):
                        removed[r, c] |= unrotated[r, c]
            changed = False
            for r in range(padded.shape[0]):
                for c in range(padded.shape[1]):
                    if removed[r, c]:
                        padded[r, c] = background
                        changed = True
            if not changed:
                break
    return padded[1:-1, 1:-1].copy()
