"""Corner-bracket key matching (63613498), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_63613498``): an L-shaped
separator closes off one grid corner and encloses a key shape. Every other
object with exactly the key's shape takes the separator colour.

The archived program took the separator to be the largest object. In the
broader domain, another object can be just as large (or larger), and reading
order then decides, which depends on orientation. This program identifies the
separator by its geometry: a bracket whose bounding box contains a grid
corner, consisting of the full bounding-box row and column opposite that
corner, and enclosing exactly one non-background colour. All roles are
read from visible cells, so one program serves every D4/palette variant.
Ambiguous scenes raise errors rather than guessing.
"""

PROGRAM = r'''
from collections import Counter


def _components(grid, background):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == background or (row, col) in seen:
                continue
            seen.add((row, col))
            cells = [(row, col)]
            for y, x in cells:
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if (0 <= ny < height and 0 <= nx < width and (ny, nx) not in seen
                            and grid[ny][nx] == colour):
                        seen.add((ny, nx))
                        cells.append((ny, nx))
            found.append((colour, cells))
    return found


def _shape(cells):
    top = min(y for y, x in cells)
    left = min(x for y, x in cells)
    return frozenset((y - top, x - left) for y, x in cells)


def _bracket(grid, background, colour, cells):
    """Return the enclosed key cells if ``cells`` closes off a grid corner."""
    height, width = len(grid), len(grid[0])
    top = min(y for y, x in cells)
    bottom = max(y for y, x in cells)
    left = min(x for y, x in cells)
    right = max(x for y, x in cells)
    if bottom == top or right == left or len(cells) != (bottom - top) + (right - left) + 1:
        return None
    cell_set = set(cells)
    keys = []
    for corner_row, arm_row in ((0, bottom), (height - 1, top)):
        for corner_col, arm_col in ((0, right), (width - 1, left)):
            if corner_row not in (top, bottom) or corner_col not in (left, right):
                continue
            if arm_row == corner_row or arm_col == corner_col:
                continue
            arms = ({(arm_row, x) for x in range(left, right + 1)}
                    | {(y, arm_col) for y in range(top, bottom + 1)})
            if arms != cell_set:
                continue
            inside = [(y, x) for y in range(top, bottom + 1) for x in range(left, right + 1)
                      if (y, x) not in cell_set and grid[y][x] != background]
            colours = {grid[y][x] for y, x in inside}
            if len(colours) == 1 and colour not in colours:
                keys.append(inside)
    return keys[0] if len(keys) == 1 else None


def solve(demonstrations, grid):
    counts = Counter(cell for row in grid for cell in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Expected a unique modal background")
    background = counts[0][0]
    objects = _components(grid, background)
    frames = []
    for colour, cells in objects:
        key = _bracket(grid, background, colour, cells)
        if key is not None:
            frames.append((len(cells), colour, cells, key))
    if not frames:
        raise ValueError("Expected a corner bracket enclosing a key")
    frames.sort(key=lambda item: -item[0])
    if len(frames) > 1 and frames[0][0] == frames[1][0]:
        raise ValueError("Ambiguous corner bracket")
    _, frame_colour, frame_cells, key_cells = frames[0]
    excluded = set(frame_cells) | set(key_cells)
    key_shape = _shape(key_cells)
    out = [row[:] for row in grid]
    for colour, cells in objects:
        if colour == frame_colour or excluded & set(cells):
            continue
        if _shape(cells) == key_shape:
            for y, x in cells:
                out[y][x] = frame_colour
    return out
'''


def build_program(d4, palette):
    # Separator, key and target roles are geometric; no colour or orientation
    # constant is needed, so the same direct-coordinate program serves all variants.
    return PROGRAM
