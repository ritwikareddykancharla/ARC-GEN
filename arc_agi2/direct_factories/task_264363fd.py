"""Stamp a legend star at each marker (264363fd), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_264363fd``): a small legend
star has a centre colour, an optional ring, and two-cell arms. Large
rectangles contain single marker cells in the centre colour. Each marker
becomes a copy of the star, and every arm extends as a line to the edge of
its rectangle. The legend itself is erased.

The archived program put the legend centre at the floor of its bounding-box
midpoint. Native stars are symmetric, so that is exact there. RE-ARC stars
have arms on any subset of the four sides, so the floor moved under each
transform. The centre is now the unique legend cell whose eight neighbours
all belong to the legend (RE-ARC always draws the ring). Native plus-shaped
stars have no ring, so they fall back to the exact centre of their
odd-by-odd box; anything else is rejected. Arms are runs of at least two
cells from the centre, as before. If the rectangle colour ties the background
for the most cells, a tied colour is used only when it alone parses. RE-ARC
can also place no rectangle at all, in which case only the legend is erased.
Roles come from the grid, so one program serves every D4/palette variant.
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
            found.append(cells)
    return found


def _box(cells):
    return (min(y for y, x in cells), min(x for y, x in cells),
            max(y for y, x in cells), max(x for y, x in cells))


def solve(demonstrations, grid):
    counts = Counter(cell for row in grid for cell in row).most_common()
    tied = [colour for colour, count in counts if count == counts[0][1]]
    if len(counts) < 2:
        raise ValueError("Expected a background and a legend")
    # Large rectangles can tie the background count. Only the true background
    # leaves a single strictly smallest legend with a centre, so accept a tied
    # colour only if it is the unique one that parses.
    results = []
    for background in tied:
        try:
            results.append(_stamp(grid, background))
        except ValueError:
            continue
    if len(results) != 1:
        raise ValueError("Expected exactly one background giving a valid legend")
    return results[0]


def _stamp(grid, background):
    objects = sorted(_objects(grid, background), key=len)
    # RE-ARC may fail to place any rectangle; the legend alone is then erased.
    if not objects or (len(objects) > 1 and len(objects[0]) == len(objects[1])):
        raise ValueError("Expected one strictly smallest legend")
    legend = objects[0]
    cells = set(legend)
    full = [(y, x) for y, x in legend
            if all((y + dy, x + dx) in cells for dy in (-1, 0, 1) for dx in (-1, 0, 1))]
    top, left, bottom, right = _box(legend)
    if len(full) == 1:
        cy, cx = full[0]
    elif not full and (bottom - top) % 2 == 0 and (right - left) % 2 == 0:
        cy, cx = (top + bottom) // 2, (left + right) // 2
        if (cy, cx) not in cells:
            raise ValueError("Legend centre is empty")
    else:
        raise ValueError("Ambiguous legend centre")
    centre = grid[cy][cx]
    offsets = {(y - cy, x - cx): grid[y][x] for y, x in legend}
    arms = {}
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        k = 0
        while ((k + 1) * dy, (k + 1) * dx) in offsets:
            k += 1
        if k >= 2:
            arms[(dy, dx)] = offsets[(k * dy, k * dx)]
    out = [row[:] for row in grid]
    for y, x in legend:
        out[y][x] = background
    stamps = []
    for obj in objects[1:]:
        r0, c0, r1, c1 = _box(obj)
        fill = Counter(grid[y][x] for y, x in obj).most_common(1)[0][0]
        for my, mx in obj:
            if grid[my][mx] == centre and fill != centre:
                stamps.append((my, mx, r0, c0, r1, c1))
                for (dy, dx), colour in arms.items():
                    t = 1
                    while r0 <= my + t * dy <= r1 and c0 <= mx + t * dx <= c1:
                        if out[my + t * dy][mx + t * dx] == fill:
                            out[my + t * dy][mx + t * dx] = colour
                        t += 1
    for my, mx, r0, c0, r1, c1 in stamps:
        for (dy, dx), colour in offsets.items():
            if (dy, dx) != (0, 0) and r0 <= my + dy <= r1 and c0 <= mx + dx <= c1:
                out[my + dy][mx + dx] = colour
    return out
'''


def build_program(d4, palette):
    # Star geometry is read relative to its own centre in visible coordinates.
    return PROGRAM
