"""Fit ray interpretation to demos while retaining all visibly ambiguous dockings.

This verifier uses coordinate-set components and relative ship coordinates, apart
from the emitted target's boolean masks and absolute affine coordinates.
"""
import collections
import itertools
from .colour_evidence import MissingColourEvidence

DIRECTIONS = ((1,0),(-1,0),(0,1),(0,-1))
RULES = tuple(itertools.permutations(range(4))) + ('any','all')


def _components(points, diagonal=False):
    remaining=set(points)
    steps=DIRECTIONS+(((1,1),(1,-1),(-1,1),(-1,-1)) if diagonal else ())
    while remaining:
        todo=[remaining.pop()];component=set(todo)
        while todo:
            r,c=todo.pop()
            for dr,dc in steps:
                p=(r+dr,c+dc)
                if p in remaining:
                    remaining.remove(p);component.add(p);todo.append(p)
        yield component


def _normalize(points):
    r0=min(r for r,c in points);c0=min(c for r,c in points)
    return frozenset((r-r0,c-c0) for r,c in points),(r0,c0)


def _turn(point,turn,reflect):
    y,x=point
    if reflect:x=-x
    for _ in range(turn):y,x=x,-y
    return y,x


def docking_predictions(grid,palette):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        raise ValueError('Invalid grid')
    H,W=len(grid),len(grid[0]);body,core=palette[8],palette[9]
    pixels={(r,c):v for r,row in enumerate(grid) for c,v in enumerate(row)}
    frequencies=collections.Counter(pixels.values())
    backgrounds=[v for v,n in frequencies.items() if n==max(frequencies.values())]
    if len(backgrounds)!=1:raise ValueError('Ambiguous background')
    bg=backgrounds[0];wall={}
    for colour in frequencies:
        if colour==bg:continue
        for component in _components(p for p,v in pixels.items() if v==colour):
            if any(r in (0,H-1) or c in (0,W-1) for r,c in component):
                wall.update({p:colour for p in component})
    free={p for p,v in pixels.items() if v!=bg and p not in wall}
    ships=[s for s in _components(free) if any(pixels[p]==body for p in s)]
    shipcells=set().union(*ships) if ships else set()
    targets=list(_components({p for p,v in pixels.items() if v==core and p not in shipcells},True))
    if not ships or len(ships)!=len(targets):raise ValueError('Unmatched ships or targets')
    base={p:(bg if p in free else v) for p,v in pixels.items()}
    target_shapes=[_normalize(t) for t in targets]
    alternatives=[]
    for ship in ships:
        sr,sc=min(r for r,c in ship),min(c for r,c in ship)
        relative={(r-sr,c-sc):pixels[r,c] for r,c in ship}
        options=[]
        for reflect in (False,True):
            for turn in range(4):
                oriented={_turn(p,turn,reflect):v for p,v in relative.items()}
                cores={p for p,v in oriented.items() if v==core}
                if not cores:continue
                shape,(rr,cc)=_normalize(cores)
                for target_id,(target_shape,(tr,tc)) in enumerate(target_shapes):
                    if shape!=target_shape:continue
                    stamped={(r+tr-rr,c+tc-cc):v for (r,c),v in oriented.items()}
                    if not set(stamped)<=set(pixels):continue
                    measurements=[]
                    for (r,c),colour in stamped.items():
                        if colour in (body,core):continue
                        hits={}
                        for index,(dr,dc) in enumerate(DIRECTIONS):
                            if stamped.get((r-dr,c-dc)) not in (body,core):continue
                            path=((r+dr*k,c+dc*k) for k in range(1,max(H,W)+1))
                            first=next((q for q in path if q not in pixels or q in wall),None)
                            hits[index]=first in wall and wall[first]==colour
                        measurements.append(hits)
                    if not measurements or any(not m for m in measurements):continue
                    scores=[]
                    for rule in RULES:
                        if rule=='any':scores.append(sum(any(m.values()) for m in measurements))
                        elif rule=='all':scores.append(sum(all(m.values()) for m in measurements))
                        else:scores.append(sum(m[next(i for i in rule if i in m)] for m in measurements))
                    options.append((target_id,frozenset(stamped.items()),not reflect,scores))
        if not options:raise ValueError('No candidate placement')
        alternatives.append(options)
    predictions=[]
    for rule_index in range(len(RULES)):
        scene=dict(base);used_targets=set();occupied=set();valid=True
        for options in alternatives:
            maximum=max((o[3][rule_index],o[2]) for o in options)
            winners={(o[0],o[1]) for o in options if (o[3][rule_index],o[2])==maximum}
            if len(winners)!=1:valid=False;break
            target,cells=next(iter(winners));placement=dict(cells)
            if target in used_targets or occupied&set(placement):valid=False;break
            used_targets.add(target);occupied.update(placement);scene.update(placement)
        predictions.append(tuple(tuple(scene[r,c] for c in range(W)) for r in range(H)) if valid else None)
    return predictions


def surviving_docking_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('6e4f6532: demonstrations required')
    alive=set(range(len(RULES)))
    for p in demonstrations:
        try:predictions=docking_predictions(p['input'],palette)
        except (ValueError,KeyError) as e:raise MissingColourEvidence('6e4f6532: invalid demonstration geometry') from e
        target=tuple(tuple(row) for row in p['output'])
        alive &= {i for i,pred in enumerate(predictions) if pred==target}
    if not alive:raise MissingColourEvidence('6e4f6532: no consistent demonstrated marker interpretation')
    return alive


def require_docking_evidence(demonstrations,queries,palette):
    alive=surviving_docking_rules(demonstrations,palette)
    for query in queries:
        try:predictions=docking_predictions(query['input'],palette)
        except (ValueError,KeyError) as e:raise MissingColourEvidence('6e4f6532: invalid query geometry') from e
        answers={predictions[i] for i in alive}
        if None in answers or len(answers)!=1:raise MissingColourEvidence('6e4f6532: unresolved marker interpretation or docking tie')
