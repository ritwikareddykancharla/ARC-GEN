def build_program(d4, palette):
    d4 = int(d4) % 8
    # Original layout of quadrants: label k means the block is rot90(input, k), i.e. k counter-clockwise quarter turns.
    lab = [[0, 1], [2, 3]]
    # Move the quadrant labels the same way the D4 move acts on the whole canvas.
    if d4 >= 4:
        lab = [row[::-1] for row in lab]
    for _ in range(d4 % 4):
        lab = [list(r) for r in zip(*lab[::-1])]  # clockwise quarter turn
    # Each block's content: T R^k T^-1 = R^k for proper rotations, R^-k for reflections.
    refl = d4 >= 4
    turns = [[((-k) % 4) if refl else (k % 4) for k in row] for row in lab]
    # Palette is irrelevant: the mechanism never reads or writes specific colours.
    prog = '''import numpy as np

# TURNS[r][c] = number of counter-clockwise quarter turns of the visible input
# that fills quadrant (r, c) of the doubled output canvas.
TURNS = %r


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    blocks = [[np.rot90(g, TURNS[r][c]) for c in range(2)] for r in range(2)]
    if h == w:
        out = np.zeros((2 * h, 2 * w), dtype=int)
        for r in range(2):
            for c in range(2):
                out[r * h:(r + 1) * h, c * w:(c + 1) * w] = blocks[r][c]
        return out.tolist()
    # Non-square inputs are outside the constructor's domain. Assemble the blocks
    # only if their shapes happen to tile consistently.
    out = np.block(blocks)
    return out.tolist()
''' % (turns,)
    return prog
