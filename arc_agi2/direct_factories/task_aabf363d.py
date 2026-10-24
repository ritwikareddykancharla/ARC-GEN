"""Marker recolouring (aabf363d), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_aabf363d``): a drawing in one
colour and a single marker pixel in a second colour. The drawing takes the
marker colour, and the marker is erased.

The archived program chose the marker as the smallest 4-connected
component. RE-ARC drawings grow through diagonal neighbours, so some of their
components are single pixels, and reading order then broke the tie
differently under each transform. Here, the roles are colours: the marker is
the strictly rarer of exactly two non-background colours. The background is
the border's modal colour, because RE-ARC drawings may cover more cells.
One program serves every D4/palette variant.
"""

PROGRAM = r'''
from collections import Counter


def solve(demonstrations, grid):
    # The drawing never reaches the outer border (only the marker may), so
    # the background is the border's modal colour even when the drawing is
    # the most frequent colour overall.
    border = [cell for row in (grid[0], grid[-1]) for cell in row]
    border += [row[0] for row in grid[1:-1]] + [row[-1] for row in grid[1:-1]]
    ranked = Counter(border).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError("Expected a unique modal border background")
    background = ranked[0][0]
    counts = Counter(cell for row in grid for cell in row if cell != background)
    foreground = [(count, colour) for colour, count in counts.items()]
    if len(foreground) != 2 or foreground[0][0] == foreground[1][0]:
        raise ValueError("Expected a drawing colour and a strictly rarer marker colour")
    drawing = max(foreground)[1]
    marker = min(foreground)[1]
    out = []
    for row in grid:
        out.append([marker if cell == drawing else background if cell == marker else cell
                    for cell in row])
    return out
'''


def build_program(d4, palette):
    # Colour roles are read from cell counts; geometry is untouched.
    return PROGRAM
