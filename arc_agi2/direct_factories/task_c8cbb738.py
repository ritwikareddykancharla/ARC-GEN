"""Assemble scattered ring pieces (c8cbb738), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_c8cbb738``): the output is a
rectangle as large as the biggest coloured piece. Every piece in the input
is a part of that rectangle's one-cell ring, and each is moved back onto
the ring.

Native pieces are symmetric about the centre, so the archived program
centred each piece. With an odd margin, centring rounds down. RE-ARC
pieces are asymmetric parts of the ring that touch two adjacent sides, and
rounding down picks a different cell under each transform. Each piece now
goes to the offset that puts the most of its cells on the ring. Ties go to
the placement whose exact centre is closest to the canvas centre, which is
how symmetric native pieces resolve. A tie that remains is rejected. Roles
are read from the grid, so one program serves every D4/palette variant.
"""

PROGRAM = r'''
from collections import Counter


def solve(demonstrations, grid):
    counts = Counter(cell for row in grid for cell in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Expected a unique modal background")
    background = counts[0][0]
    pieces = {}
    for row, line in enumerate(grid):
        for col, colour in enumerate(line):
            if colour != background:
                pieces.setdefault(colour, []).append((row, col))
    shapes = {}
    for colour, cells in pieces.items():
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        shapes[colour] = [(r - top, c - left) for r, c in cells]
    height = max(max(r for r, c in s) + 1 for s in shapes.values())
    width = max(max(c for r, c in s) + 1 for s in shapes.values())
    out = [[background] * width for _ in range(height)]

    def on_ring(r, c):
        return r in (0, height - 1) or c in (0, width - 1)

    for colour, shape in sorted(shapes.items()):
        tall = max(r for r, c in shape) + 1
        wide = max(c for r, c in shape) + 1
        options = []
        for dy in range(height - tall + 1):
            for dx in range(width - wide + 1):
                hits = sum(on_ring(r + dy, c + dx) for r, c in shape)
                # Twice the centre offset keeps the distance exact for odd margins.
                distance = abs(2 * dy + tall - height) + abs(2 * dx + wide - width)
                options.append((-hits, distance, dy, dx))
        options.sort()
        if len(options) > 1 and options[0][:2] == options[1][:2]:
            raise ValueError("Ambiguous placement on the ring")
        _, _, dy, dx = options[0]
        for r, c in shape:
            if out[r + dy][c + dx] != background:
                raise ValueError("Pieces overlap after placement")
            out[r + dy][c + dx] = colour
    return out
'''


def build_program(d4, palette):
    # Ring overlap and centre distance are D4-invariant; colours come from the grid.
    return PROGRAM
