"""Coordinate-set symmetry check, independent of the target's array flips."""
from collections import defaultdict
from .colour_evidence import MissingColourEvidence


def symmetry_options(grid,palette):
    bg=palette[0];by_colour=defaultdict(set)
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v!=bg:by_colour[v].add((r,c))
    options=[set(),set(),set()]
    for colour,cells in by_colour.items():
        top,bottom=min(r for r,c in cells),max(r for r,c in cells)
        left,right=min(c for r,c in cells),max(c for r,c in cells)
        transforms=({(r,left+right-c) for r,c in cells},
                    {(top+bottom-r,c) for r,c in cells},
                    {(top+bottom-r,left+right-c) for r,c in cells})
        out=tuple(tuple(colour if (r,c) in cells else bg for c in range(left,right+1)) for r in range(top,bottom+1))
        for i,t in enumerate(transforms):
            if cells==t:options[i].add(out)
    return options


def surviving_symmetry_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('72ca375d: demonstrations required')
    alive=set(range(3))
    for p in demonstrations:
        expected=tuple(tuple(row) for row in p['output'])
        alive &= {i for i,v in enumerate(symmetry_options(p['input'],palette)) if v=={expected}}
    if not alive:raise MissingColourEvidence('72ca375d: no uniquely demonstrated symmetry rule')
    return alive


def require_symmetry_evidence(demonstrations,queries,palette):
    alive=surviving_symmetry_rules(demonstrations,palette)
    for q in queries:
        options=symmetry_options(q['input'],palette)
        if any(not options[i] for i in alive) or len(set().union(*(options[i] for i in alive)))!=1:
            raise MissingColourEvidence('72ca375d: unresolved symmetry or matching object')
