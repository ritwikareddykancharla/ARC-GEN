"""Independent coordinate-canvas simulation of centre-entry tile propagation."""
from .colour_evidence import MissingColourEvidence


def restore_tile_bars(grid,palette):
    bg=palette[8];h=len(grid);w=len(grid[0]);tiles=[]
    if any(len(row)!=w for row in grid):raise ValueError('Ragged grid')
    for y in range(1,h-1):
        for x in range(1,w-1):
            around={grid[y+dy][x+dx] for dy in (-1,0,1) for dx in (-1,0,1) if(dy,dx)!=(0,0)}
            if len(around)!=1:continue
            frame=next(iter(around));c=grid[y][x]
            if c not in(bg,frame) and frame!=bg:tiles.append((y,x,c,frame))
    if not tiles or len({f for y,x,c,f in tiles})!=1:raise ValueError('Invalid motifs')
    centres={(y,x) for y,x,c,f in tiles};bars={};canvas={};explained=set()
    for c in {c for y,x,c,f in tiles}:
        points={(y,x) for y,row in enumerate(grid) for x,v in enumerate(row) if v==c and(y,x) not in centres}
        if not points:raise ValueError('Missing target bar')
        ys,xs=zip(*points);a,b,d,e=min(ys),min(xs),max(ys),max(xs)
        if points!={(y,x) for y in range(a,d+1) for x in range(b,e+1)}:raise ValueError('Target is not one solid rectangle')
        bars[c]=(a,b,d,e);canvas.update({q:c for q in points});explained|=points
    for y,x,c,f in tiles:explained|={(y+dy,x+dx) for dy in(-1,0,1) for dx in(-1,0,1)}
    if explained!={(y,x) for y,row in enumerate(grid) for x,v in enumerate(row) if v!=bg}:raise ValueError('Unexpected coloured cells')
    claimed=set()
    for y,x,c,f in tiles:
        a,b,d,e=bars[c];direction=None
        while True:
            patch={(y+dy,x+dx):c if(dy,dx)==(0,0) else f for dy in(-1,0,1) for dx in(-1,0,1)}
            if any(not(0<=r<h and 0<=s<w) for r,s in patch):raise ValueError('Off-grid copy')
            if claimed&patch.keys() or any(canvas.get(q,bg) not in(bg,c) for q in patch):raise ValueError('Colliding copies')
            claimed|=patch.keys();canvas.update(patch)
            directions=[]
            if y<a:directions.append((1,0))
            if y>d:directions.append((-1,0))
            if x<b:directions.append((0,1))
            if x>e:directions.append((0,-1))
            if not directions:break
            if len(directions)!=1 or(direction is not None and direction!=directions[0]):raise ValueError('Diagonal or overshot centre')
            direction=directions[0];y+=3*direction[0];x+=3*direction[1]
    return [[canvas.get((y,x),bg) for x in range(w)] for y in range(h)]


def require_tile_bar_evidence(demonstrations,queries,palette):
    try:
        for p in demonstrations:
            if restore_tile_bars(p['input'],palette)!=p['output']:raise ValueError('Contradictory demo')
        for q in queries:restore_tile_bars(q['input'],palette)
    except (ValueError,TypeError,IndexError) as exc:raise MissingColourEvidence('985ae207: invalid centre-entry tile construction') from exc
