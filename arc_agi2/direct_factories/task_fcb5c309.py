"""Crop the box holding the most dots (fcb5c309), reviewed for RE-ARC.

Rule (native constructor and RE-ARC ``generate_fcb5c309``): rectangular
outlines of one colour sit among dots of a second colour. The output is the
outline that encloses the most dots, cropped, with the outline recoloured
to the dot colour.

The native constructor makes the largest box also the one with the most
dots, so the archived program cropped the largest object. RE-ARC boxes can
have equal sizes (reading order then decided) and dense dot clusters can be
the largest object. Here, the outline colour is the colour whose
components are all hollow rectangles (both sides at least 3). The box is
chosen by its enclosed dot count, and a tie is rejected. One program serves
every D4/palette variant.
"""

PROGRAM = r'''
from collections import Counter


def _components(grid, colour):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != colour or (row, col) in seen:
                continue
            seen.add((row, col))
            cells = [(row, col)]
            for y, x in cells:
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if (0 <= ny < height and 0 <= nx < width and (ny, nx) not in seen
                            and grid[ny][nx] == colour):
                        seen.add((ny, nx))
                        cells.append((ny, nx))
            found.append(cells)
    return found


def _outline(cells):
    top = min(y for y, x in cells)
    bottom = max(y for y, x in cells)
    left = min(x for y, x in cells)
    right = max(x for y, x in cells)
    if bottom - top < 2 or right - left < 2:
        return None
    border = {(y, x) for y in range(top, bottom + 1) for x in range(left, right + 1)
              if y in (top, bottom) or x in (left, right)}
    return (top, left, bottom, right) if set(cells) == border else None


def solve(demonstrations, grid):
    counts = Counter(cell for row in grid for cell in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Expected a unique modal background")
    background = counts[0][0]
    colours = [colour for colour, _ in counts[1:]]
    if len(colours) != 2:
        raise ValueError("Expected one outline colour and one dot colour")
    boxes = {}
    for colour in colours:
        found = [_outline(cells) for cells in _components(grid, colour)]
        if all(found):
            boxes[colour] = found
    if len(boxes) != 1:
        raise ValueError("Expected exactly one colour drawn only as box outlines")
    frame = next(iter(boxes))
    dot = colours[0] if colours[1] == frame else colours[1]
    scored = []
    for top, left, bottom, right in boxes[frame]:
        inside = sum(grid[y][x] == dot for y in range(top + 1, bottom)
                     for x in range(left + 1, right))
        scored.append((inside, (top, left, bottom, right)))
    scored.sort(reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        raise ValueError("Ambiguous box: equal enclosed dot counts")
    top, left, bottom, right = scored[0][1]
    return [[dot if grid[y][x] == frame else grid[y][x] for x in range(left, right + 1)]
            for y in range(top, bottom + 1)]
'''


def build_program(d4, palette):
    # Outline and dot roles are read from the grid, so no augmentation
    # constant is needed.
    return PROGRAM
