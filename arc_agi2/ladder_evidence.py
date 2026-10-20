"""Separate ladder-length ranking from counting visible horizontal rungs.

The decoder locates full level lines and the floor directly in the visible
input, independently of the target program's D4-specialized scan direction.
Only the small output layout is transformed to its episode orientation.
"""
from collections import Counter
from .augmentation import transformed
from .colour_evidence import MissingColourEvidence,_require_rule_agreement


def ladder_features(grid,palette):
    h,w=len(grid),len(grid[0]);bg,floor,marker=palette[0],palette[9],palette[5]
    lanes=[]
    for axis in (0,1):
        lines=[]
        for p in range(h if axis==0 else w):
            values=grid[p] if axis==0 else [row[p] for row in grid]
            if len(set(values))==1 and values[0]!=bg:lines.append((p,values[0]))
        if len(lines)==4:lanes.append((axis,lines))
    if len(lanes)!=1:raise MissingColourEvidence('a1aa0c1e: expected four parallel level lines')
    axis,lines=lanes[0]
    if lines[0][1]==floor:lines.reverse()
    if lines[-1][1]!=floor:raise MissingColourEvidence('a1aa0c1e: floor must end the level sequence')
    sign=1 if lines[-1][0]>lines[0][0] else -1
    if len({v for p,v in lines})!=4:raise MissingColourEvidence('a1aa0c1e: levels need distinct colours')
    if sum(v==marker for row in grid for v in row)!=1:raise MissingColourEvidence('a1aa0c1e: expected one climber')
    lengths=[];rungs=[];reaches=[]
    for i,(p,colour) in enumerate(lines[:-1]):
        counts=Counter((r if axis==0 else c) for r,row in enumerate(grid) for c,v in enumerate(row)
                       if v==colour and (r if axis==0 else c)!=p)
        positions=sorted(counts,reverse=sign<0)
        if positions!=[p+sign*j for j in range(1,len(positions)+1)]:
            raise MissingColourEvidence('a1aa0c1e: ladder lanes must be contiguous')
        if any(counts[position]!=(2 if j%2==0 else 3) for j,position in enumerate(positions)):
            raise MissingColourEvidence('a1aa0c1e: alternating rails and rungs required')
        n=len(positions)
        if n>abs(lines[i+1][0]-p)-1:raise MissingColourEvidence('a1aa0c1e: ladder exceeds its level interval')
        lengths.append(n);rungs.append(sum(v==3 for v in counts.values()))
        reaches.append(n==abs(lines[i+1][0]-p)-1)
    if not reaches[-1]:raise MissingColourEvidence('a1aa0c1e: bottom ladder must reach the floor')
    return [v for p,v in lines[:-1]],lengths,rungs,reaches


def ladder_variants(grid,palette,d4):
    colours,lengths,rungs,reaches=ladder_features(grid,palette)
    ordered=sorted(lengths)
    rank=[0 if n==0 else 2 if n==ordered[1] else 1 if n==ordered[0] else 3 for n in lengths]
    landing=2 if not reaches[1] else 1 if not reaches[0] else 0
    outputs=[]
    for widths in (rank,[min(n,3) for n in rungs]):
        out=[[palette[0]]*5 for _ in range(3)]
        for i,width in enumerate(widths):
            out[i][:width]=[colours[i]]*width;out[i][3]=palette[9]
        out[landing][4]=palette[5]
        outputs.append(transformed(out,d4,list(range(10))))
    return outputs


def require_ladder_evidence(demonstrations,queries,palette,d4):
    _require_rule_agreement('a1aa0c1e',demonstrations,queries,lambda g:ladder_variants(g,palette,d4))
