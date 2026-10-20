TEMPLATE = '''
AXIS = @AXIS@
BG = @BG@


class MissingMotifEvidence(ValueError):
    pass


def _grid(value):
    g = [[int(v) for v in row] for row in value]
    if not g or not g[0] or any(len(r) != len(g[0]) for r in g):
        raise ValueError('Expected a non-empty rectangular grid')
    return g


def _demo_grids(demonstrations):
    out = []
    for p in demonstrations or []:
        if isinstance(p, dict):
            items = [p.get('input'), p.get('output')]
        else:
            items = list(p)
        for item in items:
            if item is not None:
                out.append(_grid(item))
    return out


def _store(templates, c, along, cells):
    if c in templates and templates[c] != (along, cells):
        raise ValueError('Conflicting demonstrated motifs for one colour')
    templates[c] = (along, cells)


def _learn(g, templates):
    # A full motif line of colour c has c at index 1 and len-2 of the line
    # and c somewhere in its interior. Its decoration is every c-cell between
    # the border lines, stored as (offset across the line, absolute index
    # along the line) in visible coordinates.
    h, w = len(g), len(g[0])
    if AXIS == 'h':
        if w < 5:
            return
        colours = set(v for row in g for v in row[1:w - 1]) - {BG}
        for c in sorted(colours):
            lines = [y for y in range(h)
                     if g[y][1] == c and g[y][w - 2] == c
                     and any(v == c for v in g[y][2:w - 2])]
            if not lines:
                continue
            if len(lines) != 1:
                raise ValueError('Multiple same-colour motif lines are ambiguous')
            ly = lines[0]
            cells = frozenset((y - ly, x) for y in range(h)
                              for x in range(1, w - 1) if g[y][x] == c)
            _store(templates, c, w, cells)
    else:
        if h < 5:
            return
        colours = set(g[y][x] for y in range(1, h - 1) for x in range(w)) - {BG}
        for c in sorted(colours):
            lines = [x for x in range(w)
                     if g[1][x] == c and g[h - 2][x] == c
                     and any(g[y][x] == c for y in range(2, h - 2))]
            if not lines:
                continue
            if len(lines) != 1:
                raise ValueError('Multiple same-colour motif lines are ambiguous')
            lx = lines[0]
            cells = frozenset((y, x - lx) for y in range(1, h - 1)
                              for x in range(w) if g[y][x] == c)
            _store(templates, c, h, cells)


def _template(templates, c, along):
    if c not in templates:
        raise MissingMotifEvidence('Marker colour %d has no demonstrated motif line' % c)
    span, cells = templates[c]
    if span != along:
        raise ValueError('Query line length differs from the demonstrations')
    return cells


def solve(demonstrations, grid):
    g = _grid(grid)
    h, w = len(g), len(g[0])
    templates = {}
    for d in _demo_grids(demonstrations):
        _learn(d, templates)
    if AXIS == 'h':
        if w < 5:
            raise ValueError('Grid too narrow for a motif line')
        out = [[row[0]] + [BG] * (w - 2) + [row[-1]] for row in g]
        markers = [(y, g[y][1]) for y in range(h)
                   if g[y][1] != BG and g[y][1] == g[y][w - 2]
                   and all(v == BG for v in g[y][2:w - 2])]
        if not markers:
            raise ValueError('Query has no marker pairs')
        for y, c in markers:
            for dy, x in sorted(_template(templates, c, w)):
                r = y + dy
                if not (0 <= r < h and 1 <= x <= w - 2):
                    raise ValueError('Demonstrated motif exceeds query bounds')
                if out[r][x] not in (BG, c):
                    raise ValueError('Query motifs overlap')
                out[r][x] = c
    else:
        if h < 5:
            raise ValueError('Grid too short for a motif line')
        out = [list(g[0])] + [[BG] * w for _ in range(h - 2)] + [list(g[-1])]
        markers = [(x, g[1][x]) for x in range(w)
                   if g[1][x] != BG and g[1][x] == g[h - 2][x]
                   and all(g[y][x] == BG for y in range(2, h - 2))]
        if not markers:
            raise ValueError('Query has no marker pairs')
        for x0, c in markers:
            for y, dx in sorted(_template(templates, c, h)):
                cx = x0 + dx
                if not (0 <= cx < w and 1 <= y <= h - 2):
                    raise ValueError('Demonstrated motif exceeds query bounds')
                if out[y][cx] not in (BG, c):
                    raise ValueError('Query motifs overlap')
                out[y][cx] = c
    return out
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(p) for p in palette]
    # Row reversal keeps the border lines vertical, and an odd number of
    # clockwise turns makes them horizontal. So the parity of d4 decides
    # whether motif lines are rows ('h') or columns ('v').
    axis = 'h' if d4 % 2 == 0 else 'v'
    return (TEMPLATE.replace('@AXIS@', repr(axis))
            .replace('@BG@', repr(pal[0])))
