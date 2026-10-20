"""Visible legend parsing and competing tile operations for a32d8b75.

The 32 hypotheses vary colour swap, a fixed tile D4 transform and whether
the arrow also rotates the tile. Shape rotation and corner placement are
shared. Invalid placement eliminates a hypothesis, never clips its stamp.
"""
from .augmentation import transformed
from .colour_evidence import MissingColourEvidence


def _crop(g, excluded):
    cells = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != excluded]
    if not cells: raise MissingColourEvidence('a32d8b75: empty legend box')
    top,bottom = min(r for r,c in cells),max(r for r,c in cells)
    left,right = min(c for r,c in cells),max(c for r,c in cells)
    return [row[left:right+1] for row in g[top:bottom+1]]


def _rotate(g, turns):
    for _ in range(turns%4): g = [list(row) for row in zip(*g[::-1])]
    return g


def _components(g,bg):
    remaining = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != bg}
    while remaining:
        stack = [remaining.pop()]; cells = set(stack)
        while stack:
            r,c = stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p = r+dr,c+dc
                    if p in remaining:
                        remaining.remove(p);cells.add(p);stack.append(p)
        yield cells


def parse_legends(g,palette,d4):
    bg,divider,corner,arrow_ink = (palette[i] for i in (0,6,4,7))
    down = (1,0)
    for _ in range(d4%4): down = down[1],-down[0]
    vertical = down[0] != 0
    positive = (down[0] if vertical else down[1]) > 0
    up = -down[0],-down[1]
    def slice_axis(a,lo,hi,rows):
        return a[lo:hi] if rows else [row[lo:hi] for row in a]
    def full(a,rows):
        lines = a if rows else zip(*a)
        return [i for i,line in enumerate(lines) if all(v == divider for v in line)]
    cross = len(g[0]) if vertical else len(g)
    boundaries = [-1]+full(g,not vertical)+[cross]
    strips = [(a+1,b) for a,b in zip(boundaries,boundaries[1:]) if b>a+1]
    if not strips: raise MissingColourEvidence('a32d8b75: no strips')
    width = max(b-a for a,b in strips)
    canvases = [s for s in strips if s[1]-s[0] == width]
    if len(canvases) != 1: raise MissingColourEvidence('a32d8b75: canvas is not unique')
    canvas = slice_axis(g,*canvases[0],not vertical)
    legends = []
    for strip in strips:
        if strip == canvases[0]: continue
        a = slice_axis(g,*strip,not vertical)
        size = len(a) if vertical else len(a[0])
        boundaries = [-1]+full(a,vertical)+[size]
        sections = [slice_axis(a,lo+1,hi,vertical)
                    for lo,hi in zip(boundaries,boundaries[1:]) if hi>lo+1]
        if not positive: sections.reverse()
        if len(sections) != 3: raise MissingColourEvidence('a32d8b75: expected three legend sections')
        upper,box1,box2 = sections[0],_crop(sections[1],divider),_crop(sections[2],divider)
        markers = [(r,c) for r,row in enumerate(box1) for c,v in enumerate(row) if v == corner]
        if len(markers) != 1: raise MissingColourEvidence('a32d8b75: corner marker not unique')
        r,c = markers[0]
        bottom,right = r >= len(box1)/2,c >= len(box1[0])/2
        cells = [(r,c) for r,row in enumerate(box2) for c,v in enumerate(row) if v == arrow_ink]
        dr = sum(r-len(box2)//2 for r,c in cells)
        dc = sum(c-len(box2[0])//2 for r,c in cells)
        if (dr == 0) == (dc == 0): raise MissingColourEvidence('a32d8b75: arrow is not cardinal')
        arrow = (0,1 if dc>0 else -1) if dc else (1 if dr>0 else -1,0)
        turns,v = 0,up
        while v != arrow: turns,v = turns+1,(v[1],-v[0])
        tiles,shapes = [],[]
        for component in _components(upper,bg):
            colours = {upper[r][c] for r,c in component}
            r0,r1 = min(r for r,c in component),max(r for r,c in component)
            c0,c1 = min(c for r,c in component),max(c for r,c in component)
            if len(colours) == 2:
                tile = [row[c0:c1+1] for row in upper[r0:r1+1]]
                if len(component) != len(tile)*len(tile[0]):
                    raise MissingColourEvidence('a32d8b75: tile is not solid')
                tiles.append(tile)
            elif len(colours) == 1:
                shapes.append([[(r,c) in component for c in range(c0,c1+1)] for r in range(r0,r1+1)])
        if len(tiles) != 1 or len(shapes) != 1:
            raise MissingColourEvidence('a32d8b75: expected one tile and one shape')
        legends.append(dict(tile=tiles[0],mask=_rotate(shapes[0],turns),turns=turns,bottom=bottom,right=right))
    if not legends: raise MissingColourEvidence('a32d8b75: no legends')
    return canvas,legends


def tile_variants(g,palette,d4):
    canvas,legends = parse_legends(g,palette,d4)
    h,w = len(canvas),len(canvas[0])
    answers = []
    for swap in (False,True):
        for transform in range(8):
            for follow_arrow in (False,True):
                out = [row[:] for row in canvas]
                rectangles = []
                for legend in legends:
                    tile = legend['tile']
                    a,b = sorted({v for row in tile for v in row})
                    if swap: tile = [[b if v == a else a for v in row] for row in tile]
                    tile = transformed(tile,transform,list(range(10)))
                    if follow_arrow: tile = _rotate(tile,legend['turns'])
                    mask = legend['mask']; th,tw = len(tile),len(tile[0])
                    height,width = len(mask)*th,len(mask[0])*tw
                    y,x = (h-height if legend['bottom'] else 0),(w-width if legend['right'] else 0)
                    rect = y,x,y+height,x+width
                    if height>h or width>w or any(y<b and a<y+height and x<d and c<x+width for a,c,b,d in rectangles):
                        out = None;break
                    rectangles.append(rect)
                    for r,row in enumerate(mask):
                        for c,paint in enumerate(row):
                            if paint:
                                for tr,trow in enumerate(tile):
                                    out[y+r*th+tr][x+c*tw:x+(c+1)*tw] = trow
                answers.append(out)
    return answers


def require_tile_evidence(demonstrations,queries,palette,d4):
    alive = set(range(32))
    for demo in demonstrations:
        alive &= {i for i,out in enumerate(tile_variants(demo['input'],palette,d4)) if out == demo['output']}
    if not alive: raise MissingColourEvidence('a32d8b75: no tile rule fits demonstrations')
    options = [tile_variants(q['input'],palette,d4) for q in queries]
    # The stated family requires complete nonoverlapping stamps. Query geometry
    # can eliminate a rule that violates those constraints, without its answer.
    alive = {i for i in alive if all(v[i] is not None for v in options)}
    if not alive: raise MissingColourEvidence('a32d8b75: no rule fits query geometry')
    for variants in options:
        if len({tuple(map(tuple,variants[i])) for i in alive}) != 1:
            raise MissingColourEvidence('a32d8b75: demonstrations leave tile operation ambiguous')
