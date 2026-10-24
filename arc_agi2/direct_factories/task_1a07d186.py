"""Stray pixels docking on same-coloured lines (1a07d186), reviewed for RE-ARC.

Rule (native constructor and RE-ARC ``generate_1a07d186``): full lines of
distinct colours cross the grid in one orientation. Each stray pixel whose
colour matches a line moves to the cell beside that line, on the side where
it started. Strays of any other colour disappear.

The archived program cleared and redrew strays one at a time in reading
order. RE-ARC places strays immediately beside lines, so one stray's
destination can hold another stray. Under some transforms, a later clear then
erased an earlier move. This program clears every stray first and then
draws all moves, as both generators do. Roles are read from visible cells, so
one program serves every D4/palette variant.
"""

PROGRAM = r'''
from collections import Counter


def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    counts = Counter(cell for row in grid for cell in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Expected a unique modal background")
    background = counts[0][0]
    lines = {}
    line_cells = set()
    for row in range(height):
        colour = grid[row][0]
        if colour != background and all(cell == colour for cell in grid[row]):
            if colour in lines:
                raise ValueError("Each line colour must be used once")
            lines[colour] = ("row", row)
            line_cells.update((row, col) for col in range(width))
    for col in range(width):
        colour = grid[0][col]
        if colour != background and all(grid[row][col] == colour for row in range(height)):
            if colour in lines:
                raise ValueError("Each line colour must be used once")
            lines[colour] = ("col", col)
            line_cells.update((row, col) for row in range(height))
    if len({kind for kind, _ in lines.values()}) > 1:
        raise ValueError("Lines must share one orientation")
    strays = [(row, col, grid[row][col]) for row in range(height) for col in range(width)
              if grid[row][col] != background and (row, col) not in line_cells]
    out = [row[:] for row in grid]
    for row, col, colour in strays:
        out[row][col] = background
    for row, col, colour in strays:
        if colour not in lines:
            continue
        kind, index = lines[colour]
        if kind == "row":
            out[index - 1 if row < index else index + 1][col] = colour
        else:
            out[row][index - 1 if col < index else index + 1] = colour
    return out
'''


def build_program(d4, palette):
    # Line orientation and colours are read from the grid; the docking side
    # is relative to each line, so no augmentation constant is needed.
    return PROGRAM
