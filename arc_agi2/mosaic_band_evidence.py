"""Independent length-combination enumeration under the visible-band contract."""
import itertools
from .colour_evidence import MissingColourEvidence


def _cuts(grid,bg,axis):
    n=len(grid) if axis==0 else len(grid[0]);other=len(grid[0]) if axis==0 else len(grid)
    read=lambda i,j:grid[i][j] if axis==0 else grid[j][i]
    visible=[any(read(i,j)!=bg for j in range(other)) for i in range(n)]
    indices=[i for i,v in enumerate(visible) if v]
    if not indices:return []
    first,last=min(indices),max(indices);prefix=[0]
    for v in visible:prefix.append(prefix[-1]+v)
    allowed=set()
    for a in range(1,n-3):
        for b in range(a+3,min(a+8,n-1)+1):
            if prefix[a]==prefix[b]:continue
            if all(len({read(i,j) for i in range(a,b) if read(i,j)!=bg})<=1 for j in range(other)):allowed.add((a,b))
    answers={}
    for count in range(2,5):
        for lengths in itertools.product(range(3,9),repeat=count):
            total=sum(lengths)
            if total>16:continue
            for start in range(1,min(first,6)+1):
                end=start+total
                if not(last<end<n and 1<=n-end<=6 and min(start,n-end)<=2):continue
                cuts=[start]
                for length in lengths:cuts.append(cuts[-1]+length)
                if not all((a,b) in allowed for a,b in zip(cuts,cuts[1:])):continue
                answers.setdefault(tuple(prefix[c] for c in cuts),cuts)
    return list(answers.values())


def visible_mosaic(grid,palette):
    bg=palette[0];rowcuts=_cuts(grid,bg,0);colcuts=_cuts(grid,bg,1);answers=set()
    for rr in rowcuts:
        for cc in colcuts:
            blocks=[];valid=True
            for a,b in zip(rr,rr[1:]):
                row=[]
                for c,d in zip(cc,cc[1:]):
                    values=set(grid[r][col] for r in range(a,b) for col in range(c,d))-{bg}
                    if len(values)>1:valid=False;break
                    row.append(next(iter(values)) if values else None)
                if not valid:break
                blocks.append(row)
            if not valid:continue
            # Across each pair of adjacent bands there must be a witnessed
            # difference or a still-unknown cell capable of being different.
            if any(all(a==b and a is not None for a,b in zip(blocks[i],blocks[i+1])) for i in range(len(blocks)-1)):continue
            if any(all(row[i]==row[i+1] and row[i] is not None for row in blocks) for i in range(len(blocks[0])-1)):continue
            if any(None in row for row in blocks):raise ValueError('Unobservable individual block')
            answers.add(tuple(map(tuple,blocks)))
            if len(answers)>1:raise ValueError('Competing block grids')
    if len(answers)!=1:raise ValueError('No visible-band layout')
    return [list(row) for row in next(iter(answers))]


def _mirror(grid,axis):return grid[::-1] if axis==0 else [row[::-1] for row in grid]


def require_mosaic_band_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('80214e03: demonstrations required')
    alive={0,1}
    try:
        for p in demonstrations:
            blocks=visible_mosaic(p['input'],palette)
            alive &= {axis for axis in alive if _mirror(blocks,axis)==p['output']}
        if not alive:raise ValueError('No demonstrated mirror')
        for q in queries:
            blocks=visible_mosaic(q['input'],palette)
            if len({tuple(map(tuple,_mirror(blocks,axis))) for axis in alive})!=1:raise ValueError('Unresolved mirror')
    except (ValueError,IndexError,TypeError) as exc:raise MissingColourEvidence('80214e03: '+str(exc)) from exc
