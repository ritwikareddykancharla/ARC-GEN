"""Compare full-diagonal and contiguous-run rules with visible tie criteria.

Each rule returns every tied prediction, never a scan-order winner. A rule
must uniquely reproduce each demonstration; surviving query predictions must
agree. The native constructor stays unchanged, including broken winning lines.
"""
from collections import defaultdict
from .colour_evidence import MissingColourEvidence

TIE_CRITERIA=((),('offset',),('corner',),('offset','corner'),('corner','offset'))


def diagonal_options(grid,palette):
    h,w=len(grid),len(grid[0]);groups=[]
    for sign in (-1,1):
        by_key=defaultdict(list)
        for r,row in enumerate(grid):
            for c,v in enumerate(row):
                if v==palette[0]:by_key[r+sign*c].append((r,c))
        for key,cells in by_key.items():
            runs=[];run=[]
            for cell in sorted(cells):
                if run and cell[0]!=run[-1][0]+1:runs.append(run);run=[]
                run.append(cell)
            if run:runs.append(run)
            off=abs(2*key-(h-1)-sign*(w-1))
            for mode,parts in ((0,[cells]),(1,runs)):
                for part in parts:
                    corner=min(max(abs(r-y),abs(c-x)) for r,c in (part[0],part[-1])
                               for y,x in ((0,0),(0,w-1),(h-1,0),(h-1,w-1)))
                    groups.append((mode,frozenset(part),dict(length=len(part),offset=off,corner=corner)))
    if not groups:raise MissingColourEvidence('aa300dc3: no region cells')
    options=[]
    for mode in (0,1):
        candidates=[(cells,metrics) for m,cells,metrics in groups if m==mode]
        for tie in TIE_CRITERIA:
            score=lambda p:(p[1]['length'],)+tuple(-p[1][key] for key in tie)
            best=max(map(score,candidates));options.append({cells for cells,metrics in candidates if score((cells,metrics))==best})
    return options


def _changed_cells(pair,palette):
    inp,out=pair['input'],pair['output']
    if len(inp)!=len(out) or any(len(a)!=len(b) for a,b in zip(inp,out)):
        raise MissingColourEvidence('aa300dc3: shape-changing demonstration')
    cells=frozenset((r,c) for r,row in enumerate(inp) for c,v in enumerate(row) if out[r][c]!=v)
    if any(inp[r][c]!=palette[0] or out[r][c]!=palette[8] for r,c in cells):
        raise MissingColourEvidence('aa300dc3: invalid recolouring')
    return cells


def surviving_rules(demonstrations,palette):
    alive=set(range(10))
    if not demonstrations:raise MissingColourEvidence('aa300dc3: demonstrations required')
    for pair in demonstrations:
        expected=_changed_cells(pair,palette)
        alive &= {i for i,options in enumerate(diagonal_options(pair['input'],palette)) if options=={expected}}
    if not alive:raise MissingColourEvidence('aa300dc3: no uniquely demonstrated diagonal rule')
    return alive


def require_diagonal_evidence(demonstrations,queries,palette):
    alive=surviving_rules(demonstrations,palette)
    for q in queries:
        options=diagonal_options(q['input'],palette)
        if len(set().union(*(options[i] for i in alive)))!=1:
            raise MissingColourEvidence('aa300dc3: query mechanism or tie is not demonstrated')
