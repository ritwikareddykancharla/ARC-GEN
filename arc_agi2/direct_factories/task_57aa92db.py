"""Scaled template completion (57aa92db), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_57aa92db``): one complete
template has a single key cell. Every other object contains the same key
colour as an s-by-s block (scale s), plus a partial view of the template in
its own colour. Each object is completed by drawing the template at scale s,
anchored at its key block.

The archived program chose as template the object with the largest ratio of
non-key cells to s squared. In RE-ARC, copies may already be complete, which
gives an exact ratio tie with the template; reading order then broke the tie
and picked a scaled copy in some orientations. Here, ties go to the smallest
scale, then the largest object. A remaining tie is accepted only when the
tied candidates imply identical template cell offsets (complete unscaled
copies in other colours). Roles are read from
visible cells, so one program serves every D4/palette variant.
"""

PROGRAM = r'''
from collections import Counter


def _objects(grid, background):
    """Eight-connected groups of non-background cells of any colour."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            seen.add((row, col))
            cells = [(row, col)]
            for y, x in cells:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < height and 0 <= nx < width and (ny, nx) not in seen
                                and grid[ny][nx] != background):
                            seen.add((ny, nx))
                            cells.append((ny, nx))
            by_colour = {}
            for y, x in sorted(cells):
                by_colour.setdefault(grid[y][x], []).append((y, x))
            found.append(by_colour)
    return found


def solve(demonstrations, grid):
    counts = Counter(cell for row in grid for cell in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Expected a unique modal background")
    background = counts[0][0]
    objects = _objects(grid, background)
    if len(objects) < 2:
        return [row[:] for row in grid]
    common = set(objects[0])
    for obj in objects[1:]:
        common &= set(obj)
    if len(common) != 1:
        raise ValueError("Expected one key colour shared by every object")
    key = next(iter(common))

    def scale(obj):
        cells = obj[key]
        side = max(1, int(round(len(cells) ** 0.5)))
        top = min(y for y, x in cells)
        left = min(x for y, x in cells)
        if side * side != len(cells) or {(y - top, x - left) for y, x in cells} != {
                (a, b) for a in range(side) for b in range(side)}:
            raise ValueError("Key cells must form a square block")
        return side, top, left

    def rank(obj):
        side, _, _ = scale(obj)
        others = sum(len(v) for colour, v in obj.items() if colour != key)
        return (others / (side * side), -side, others)

    def offsets(obj):
        _, top, left = scale(obj)
        return frozenset((y - top, x - left) for colour, cells in obj.items()
                         if colour != key for y, x in cells)

    ranks = [rank(obj) for obj in objects]
    best = max(ranks)
    tied = [i for i, r in enumerate(ranks) if r == best]
    if best[1] != -1 or len({offsets(objects[i]) for i in tied}) != 1:
        raise ValueError("Ambiguous unscaled template")
    template = tied[0]
    pattern = sorted(offsets(objects[template]))
    height, width = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for i, obj in enumerate(objects):
        if i == template:
            continue
        side, top, left = scale(obj)
        colours = [colour for colour in obj if colour != key]
        if len(colours) != 1:
            raise ValueError("Each copy needs one visible template colour")
        for dy, dx in pattern:
            for a in range(side):
                for b in range(side):
                    y, x = top + dy * side + a, left + dx * side + b
                    if 0 <= y < height and 0 <= x < width and out[y][x] == background:
                        out[y][x] = colours[0]
    return out
'''


def build_program(d4, palette):
    # Template, key and copy roles are read from the visible grid, and offsets
    # are taken in visible coordinates; no augmentation constant is needed.
    return PROGRAM
