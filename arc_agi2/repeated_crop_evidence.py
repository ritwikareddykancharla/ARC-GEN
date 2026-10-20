"""Independently fit tile padding and repeat axis using demonstration outputs."""
import itertools
from .colour_evidence import MissingColourEvidence


def crop_options(grid,palette):
    bg,fg,dot=palette[0],palette[8],palette[4]
    h,w=len(grid),len(grid[0]);cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==fg]
    copies=sum(v==dot for row in grid for v in row)
    if min(h,w)<3 or not cells or not copies:raise ValueError('Missing sprite/dots')
    if any(v not in (bg,fg,dot) for row in grid for v in row):raise ValueError('Unexpected colour')
    intervals=[]
    for axis,limit in enumerate((h,w)):
        lo=min(p[axis] for p in cells);hi=max(p[axis] for p in cells)
        if hi-lo+1>3:raise ValueError('Sprite too large')
        intervals.append([max(0,min(limit-3,s)) for s in (hi-2,lo,lo-(2-hi+lo)//2)])
    options={}
    for rm,cm,axis in itertools.product(range(3),range(3),range(2)):
        top,left=intervals[0][rm],intervals[1][cm]
        tile=[[bg if grid[y][x]==dot else grid[y][x] for x in range(left,left+3)] for y in range(top,top+3)]
        options[rm,cm,axis]=[row*copies for row in tile] if axis==0 else [row[:] for _ in range(copies) for row in tile]
    return options


def require_repeated_crop_evidence(demonstrations,queries,palette):
    try:
        if not demonstrations:raise ValueError('No demonstrations')
        alive=set(itertools.product(range(3),range(3),range(2)))
        for p in demonstrations:
            alive &= {hyp for hyp,out in crop_options(p['input'],palette).items() if out==p['output']}
        if not alive:raise ValueError('No common rule')
        for q in queries:
            options=crop_options(q['input'],palette)
            answers={tuple(map(tuple,options[h])) for h in alive}
            if len(answers)!=1:raise ValueError('Unresolved crop padding or repeat direction')
    except (ValueError,TypeError,IndexError) as exc:raise MissingColourEvidence('4852f2fa: '+str(exc)) from exc
