"""Grid helpers preloaded into the sandbox, for `# inspect` code and for `transform` itself.

Executed inside the worker before the model's code, so every name here is simply available.
Kept small and boring on purpose: the model should spend its tokens on the rule, not on
re-typing a flood fill, and a smaller offline model gets fewer chances to write a buggy one.
Coordinates are (y, x); boxes are inclusive (y0, x0, y1, x1).
"""

from collections import Counter, deque
from itertools import pairwise

import numpy as np


def background(grid):
    """Most common colour."""
    return int(Counter(np.asarray(grid).ravel().tolist()).most_common(1)[0][0])


def components(mask, diagonal=False):
    """Connected groups of True cells -> list of [(y, x), ...], in reading order."""
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                queue, cells = deque([(y, x)]), []
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                out.append(sorted(cells))
    return out


def bbox(cells):
    """Inclusive (y0, x0, y1, x1) of a list of (y, x)."""
    ys, xs = [c[0] for c in cells], [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def crop(grid, y0, x0, y1, x1):
    """Inclusive crop (a copy)."""
    return np.asarray(grid)[y0 : y1 + 1, x0 : x1 + 1].copy()


def objects(grid, bg=None, diagonal=False, multicolour=False):
    """Objects as dicts: colour, cells, size, box (y0, x0, y1, x1), grid (crop, bg elsewhere).

    Single-colour components by default; multicolour=True groups touching non-background
    cells of any colour (then `colour` is the object's most common colour).
    """
    grid = np.asarray(grid)
    bg = background(grid) if bg is None else bg
    groups = []
    if multicolour:
        groups = components(grid != bg, diagonal)
    else:
        for colour in sorted(set(grid.ravel().tolist()) - {bg}):
            groups += components(grid == colour, diagonal)
    out = []
    for cells in groups:
        y0, x0, y1, x1 = bbox(cells)
        patch = np.full((y1 - y0 + 1, x1 - x0 + 1), bg, dtype=int)
        for y, x in cells:
            patch[y - y0, x - x0] = grid[y, x]
        colour = Counter(int(grid[y, x]) for y, x in cells).most_common(1)[0][0]
        out.append({"colour": colour, "cells": cells, "size": len(cells),
                    "box": (y0, x0, y1, x1), "grid": patch})  # fmt: skip
    return sorted(out, key=lambda o: (o["box"][0], o["box"][1]))


def dividers(grid):
    """Full-width rows and full-height columns of a single non-background colour.

    Returns {"rows": [(y, colour), ...], "cols": [(x, colour), ...]}.
    """
    grid = np.asarray(grid)
    bg = background(grid)
    rows = [(y, int(grid[y, 0])) for y in range(grid.shape[0])
            if grid[y, 0] != bg and (grid[y] == grid[y, 0]).all()]  # fmt: skip
    cols = [(x, int(grid[0, x])) for x in range(grid.shape[1])
            if grid[0, x] != bg and (grid[:, x] == grid[0, x]).all()]  # fmt: skip
    return {"rows": rows, "cols": cols}


def panels(grid):
    """Split along dividers(): list of (y0, x0, y1, x1) boxes in reading order."""
    grid = np.asarray(grid)
    d = dividers(grid)

    def spans(cuts, n):
        edges, out = [-1, *sorted(cuts), n], []
        for a, b in pairwise(edges):
            if b - a > 1:
                out.append((a + 1, b - 1))
        return out

    ys = spans([y for y, _ in d["rows"]], grid.shape[0])
    xs = spans([x for x, _ in d["cols"]], grid.shape[1])
    return [(y0, x0, y1, x1) for y0, y1 in ys for x0, x1 in xs]
