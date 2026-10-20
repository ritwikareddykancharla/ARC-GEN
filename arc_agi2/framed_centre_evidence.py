"""Visible uniqueness for framed-cell extraction; never chooses a planted latent."""
from .colour_evidence import MissingColourEvidence


def framed_colours(grid, palette):
    """Set-based perimeter enumeration, independent of the array target."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise MissingColourEvidence('d9fac9be: rectangular nonempty grid required')
    bg = palette[0]
    centres = set()
    height, width = len(grid), len(grid[0])
    for top in range(height - 2):
        for left in range(width - 2):
            border = {(top, c) for c in range(left, left + 3)}
            border |= {(top + 2, c) for c in range(left, left + 3)}
            border |= {(top + 1, left), (top + 1, left + 2)}
            colours = {grid[r][c] for r, c in border}
            centre = grid[top + 1][left + 1]
            if len(colours) == 1 and bg not in colours and centre != bg and centre not in colours:
                centres.add(centre)
    return centres


def require_framed_centre_evidence(demonstrations, queries, palette):
    if not demonstrations:
        raise MissingColourEvidence('d9fac9be: demonstrations required')
    for demo in demonstrations:
        candidates = framed_colours(demo['input'], palette)
        if len(candidates) != 1 or demo['output'] != [[next(iter(candidates))]]:
            raise MissingColourEvidence('d9fac9be: demonstrated framed centre is not unique and consistent')
    for query in queries:
        if len(framed_colours(query['input'], palette)) != 1:
            raise MissingColourEvidence('d9fac9be: query has no unique framed-centre colour')
