"""Evidence for catalogue-line decisions and their independently learned paints.

Compare off/full/partial-line rules on each catalogue axis.  The visible bands
and fixed slot geometry define the family; no query labels or constructor
metadata are used.  This is a bounded hypothesis check, not a proof against
every possible rule consistent with finitely many demonstrations.
"""
from itertools import product

from .colour_evidence import MissingColourEvidence


def _fail(message):
    raise MissingColourEvidence('d8e07eb2: ' + message)


def _key(g, cells):
    inks = {g[r][c] for r,c in cells}
    if len(inks) != 1:
        _fail('catalogue slot is not monochrome')
    r0,c0 = min(r for r,c in cells),min(c for r,c in cells)
    return next(iter(inks)),tuple(sorted((r-r0,c-c0) for r,c in cells))


def decode_catalogue(g, palette):
    """Read slots directly from divider/band geometry, independent of the solver.

    In particular, a narrow glyph is framed around its SLOT, not its tight box.
    The five-cell query band and two-cell result band identify the axis/sign.
    """
    h,w = len(g),len(g[0])
    bg,div = palette[8],palette[6]
    frames = []
    for axis in (0,1):
        length,cross = (h,w) if axis == 0 else (w,h)
        lines = [p for p in range(length)
                 if all((g[p][s] if axis == 0 else g[s][p]) == div
                        for s in range(cross))]
        if len(lines) != 2:
            continue
        lo,hi = lines
        if sorted((lo,length-hi-1)) == [2,5] and (hi-lo-2)%5 == 0 and (cross-2)%5 == 0:
            frames.append((axis,length,cross,lo,hi,lo == 5))
    if len(frames) != 1:
        _fail('cannot uniquely read query/catalogue/result geometry')
    axis,length,cross,lo,hi,query_low = frames[0]
    xy = lambda p,s: (p,s) if axis == 0 else (s,p)
    nr,nc = (hi-lo-2)//5,(cross-2)//5
    if nr < 1 or nc < 1:
        _fail('empty catalogue')
    starts = [lo+(3 if query_low else 2)+5*i for i in range(nr)]
    catalogue,occupied = {},set()
    for i,p in enumerate(starts):
        for j,s in enumerate(range(2,cross-2,5)):
            cells = {xy(a,b) for a in range(p,p+3) for b in range(s,s+3)
                     if g[xy(a,b)[0]][xy(a,b)[1]] != bg}
            if not cells:
                _fail('empty catalogue slot')
            key = _key(g,cells)
            if key in catalogue:
                _fail('ambiguous catalogue glyph match')
            catalogue[key] = (i,j,p,s)
            occupied |= cells
    if any(g[xy(p,s)[0]][xy(p,s)[1]] != bg and xy(p,s) not in occupied
           for p in range(lo+1,hi) for s in range(cross)):
        _fail('ink outside catalogue slots')
    qp = range(lo) if query_low else range(hi+1,length)
    rp = range(hi+1,length) if query_low else range(lo)
    query_cells = {xy(p,s) for p in qp for s in range(cross)}
    remaining = {(r,c) for r,c in query_cells if g[r][c] != bg}
    matches = []
    while remaining:
        start = remaining.pop()
        ink = g[start[0]][start[1]]
        cells,stack = {start},[start]
        while stack:
            r,c = stack.pop()
            for dr,dc in product((-1,0,1),repeat=2):
                pos = r+dr,c+dc
                if pos in remaining and g[pos[0]][pos[1]] == ink:
                    remaining.remove(pos)
                    cells.add(pos)
                    stack.append(pos)
        key = _key(g,cells)
        if key not in catalogue:
            _fail('query glyph absent from catalogue')
        matches.append(catalogue[key])
    if not matches or len({(i,j) for i,j,p,s in matches}) != len(matches):
        _fail('empty or repeated query glyphs')
    paint = set()
    for i,j,p,s in matches:
        paint |= {xy(a,b) for a in range(p-1,p+4) for b in range(s-1,s+4)
                  if g[xy(a,b)[0]][xy(a,b)[1]] == bg}
    return dict(grid=g, matches=matches, nr=nr,nc=nc, frame=paint,
                query={(r,c) for r,c in query_cells if g[r][c] == bg},
                result={xy(p,s) for p in rp for s in range(cross)
                        if g[xy(p,s)[0]][xy(p,s)[1]] == bg})


def paint_roles(scene, rule):
    """0=disabled, 1=complete line, 2=any >=2 collinear selections."""
    matches = scene['matches']
    row = len(matches) >= 2 and len({m[0] for m in matches}) == 1
    col = len(matches) >= 2 and len({m[1] for m in matches}) == 1
    rmode,cmode = rule
    success = ((row and (rmode == 2 or rmode == 1 and len(matches) == scene['nc'])) or
               (col and (cmode == 2 or cmode == 1 and len(matches) == scene['nr'])))
    roles = {pos: 'frame' for pos in scene['frame']}
    if success:
        roles.update({pos: 'success_query' for pos in scene['query']})
    roles.update({pos: 'success_result' if success else 'failure_result'
                  for pos in scene['result']})
    return roles


def require_catalogue_evidence(demonstrations, queries, palette):
    demos = [(decode_catalogue(p['input'],palette),p['output']) for p in demonstrations]
    query_scenes = [decode_catalogue(p['input'],palette) for p in queries]
    candidates = []
    for rule in product(range(3),repeat=2):
        colours,valid = {},True
        for scene,out in demos:
            g = scene['grid']
            if len(out) != len(g) or any(len(row) != len(g[0]) for row in out):
                valid = False
                break
            roles = paint_roles(scene,rule)
            for r,row in enumerate(g):
                for c,ink in enumerate(row):
                    role = roles.get((r,c))
                    if role is None:
                        valid &= out[r][c] == ink
                    else:
                        colours.setdefault(role,out[r][c])
                        valid &= colours[role] == out[r][c]
            if not valid:
                break
        if valid and demos:
            candidates.append((rule,colours))
    if not candidates:
        _fail('demonstrations fit no candidate line/paint rule')
    for scene in query_scenes:
        predictions = set()
        for rule,colours in candidates:
            roles = paint_roles(scene,rule)
            if set(roles.values()) - colours.keys():
                _fail('query requires a success/failure paint role not taught by demonstrations')
            out = [row[:] for row in scene['grid']]
            for (r,c),role in roles.items():
                out[r][c] = colours[role]
            predictions.add(tuple(map(tuple,out)))
        if len(predictions) != 1:
            _fail('demonstrations leave full-line/partial-line/axis choice ambiguous')
        # Confirm the learned paints/rule agree with this family target, without
        # ever consulting a query output.  An inconsistent demo must not teach a
        # different rule while silently retaining the old emitted program.
        expected = [row[:] for row in scene['grid']]
        native_roles = paint_roles(scene,(2,2))
        for (r,c),role in native_roles.items():
            expected[r][c] = palette[2] if role == 'failure_result' else palette[3]
        if tuple(map(tuple,expected)) not in predictions:
            _fail('demonstrated rule disagrees with the program target')
