"""Infer motif templates from supplied demonstrations, never query labels.

For native 98c475bf only. This is an episode verifier, not an alternative
constructor: no fixed colour-to-shape dictionary is used here.
"""
from .runtime import grid


class MissingMotifEvidence(ValueError):
    """The query asks for a colour whose motif was never demonstrated."""


def _canvas(g):
    g = grid(g)
    h, w = len(g), len(g[0])
    if w < 5:
        raise ValueError('Motif canvas is too narrow')
    border = g[0][0]
    if border == 0 or any(row[0] != border or row[-1] != border for row in g):
        raise ValueError('Expected two solid matching border columns')
    return g, h, w, border


def demonstrated_motifs(demonstrations):
    """Read complete coloured lines in both input and output demonstrations."""
    templates = {}
    width = None
    for pair in demonstrations:
        for field in ('input', 'output'):
            g, h, w, _ = _canvas(pair[field])
            if width is not None and width != w:
                raise ValueError('Motif demonstrations need a shared width')
            width = w
            colours = {v for row in g for v in row[1:-1]} - {0}
            for colour in colours:
                lines = [y for y, row in enumerate(g)
                         if row[1] == colour == row[-2]
                         and any(v == colour for v in row[2:-2])]
                if not lines:
                    continue  # Marker dots do not demonstrate a template.
                if len(lines) != 1:
                    raise ValueError('Multiple same-colour lines are ambiguous')
                template = frozenset((y-lines[0], x)
                                     for y in range(h) for x in range(1, w-1)
                                     if g[y][x] == colour)
                if colour in templates and templates[colour] != template:
                    raise ValueError('Conflicting demonstrated colour templates')
                templates[colour] = template
    return width, templates


def solve_demonstrated_motifs(demonstrations, query_input):
    """Infer the output from demonstrations and the query INPUT alone."""
    width, templates = demonstrated_motifs(demonstrations)
    g, h, w, border = _canvas(query_input)
    if width != w:
        raise ValueError('Query width differs from demonstrations')
    markers = [(y, row[1]) for y, row in enumerate(g)
               if row[1] != 0 and row[1] == row[-2]
               and all(v == 0 for v in row[2:-2])]
    if not markers:
        raise ValueError('Query has no marker pairs')
    missing = {colour for _, colour in markers} - templates.keys()
    if missing:
        raise MissingMotifEvidence(f'Undemonstrated marker colours: {sorted(missing)}')
    out = [[border] + [0]*(w-2) + [border] for _ in range(h)]
    for y, colour in markers:
        for dy, x in templates[colour]:
            r = y + dy
            if not 0 <= r < h or not 0 < x < w-1:
                raise ValueError('Demonstrated motif exceeds query bounds')
            if out[r][x] not in (0, colour):
                raise ValueError('Query motifs overlap')
            out[r][x] = colour
    return out
