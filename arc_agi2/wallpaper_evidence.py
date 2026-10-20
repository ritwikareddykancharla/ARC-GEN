"""Independent scalar constraint check for missing periodic wallpaper patches."""
from itertools import combinations
from .colour_evidence import MissingColourEvidence


def unique_wallpaper_patch(grid):
    h=len(grid);w=len(grid[0])
    if not h or not w or any(len(row)!=w for row in grid):raise ValueError('Invalid rectangle')
    cells={}
    for y,row in enumerate(grid):
        for x,value in enumerate(row):cells.setdefault(value,[]).append((y,x))
    rectangles=[]
    for points in cells.values():
        rows,cols=zip(*points);top,bottom,left,right=min(rows),max(rows),min(cols),max(cols)
        if bottom-top>=1 and right-left>=1 and len(points)==(bottom-top+1)*(right-left+1):rectangles.append((top,left,bottom,right))
    answers=set();unknown=False
    for count in (2,3):
        for blocks in combinations(rectangles,count):
            sizes=sorted((b-t+1,r-l+1) for t,l,b,r in blocks)
            if any(x[0]>y[0] or x[1]>y[1] or x==y for x,y in zip(sizes,sizes[1:])):continue
            areas=[(b-t+1)*(r-l+1) for t,l,b,r in blocks]
            if areas.count(max(areas))!=1:continue
            top,left,bottom,right=blocks[areas.index(max(areas))]
            visible=[(y,x,v) for y,row in enumerate(grid) for x,v in enumerate(row) if not any(t<=y<=b and l<=x<=r for t,l,b,r in blocks)]
            for py in range(1,min(h,16)+1):
                for px in range(1,min(w,16)+1):
                    if py*px>16:continue
                    table={};consistent=True
                    for y,x,v in visible:
                        key=(y%py,x%px)
                        if key in table and table[key]!=v:consistent=False;break
                        table[key]=v
                    if not consistent:continue
                    needed={(y%py,x%px) for y in range(top,bottom+1) for x in range(left,right+1)}
                    if not needed<=table.keys():unknown=True;continue
                    answers.add(tuple(tuple(table[y%py,x%px] for x in range(left,right+1)) for y in range(top,bottom+1)))
    if unknown or len(answers)!=1:raise ValueError('Unresolved visible periodic reconstruction')
    return [list(row) for row in next(iter(answers))]


def require_wallpaper_evidence(demonstrations,queries,palette=None):
    try:
        for p in demonstrations:
            if unique_wallpaper_patch(p['input'])!=p['output']:raise ValueError('Contradictory demonstration')
        for q in queries:unique_wallpaper_patch(q['input'])
    except (ValueError,TypeError,IndexError) as exc:
        raise MissingColourEvidence('abbfd121: wallpaper patch is not uniquely supported by visible cells') from exc
