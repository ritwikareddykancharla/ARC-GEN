"""Independent component decoder for demonstrated lattice packing direction."""
from .colour_evidence import MissingColourEvidence


def pack_options(grid,palette):
    bg,line,landmark=palette[0],palette[1],palette[8]
    h,w=len(grid),len(grid[0])
    edges={'top':grid[0],'bottom':grid[-1],'left':[r[0] for r in grid],'right':[r[-1] for r in grid]}
    sides=[k for k,v in edges.items() if all(c==line for c in v)]
    if len(sides)!=1:raise ValueError('Expected one marked edge')
    side=sides[0];remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (bg,line)};centres=[]
    while remaining:
        start=min(remaining);colour=grid[start[0]][start[1]];stack=[start];remaining.remove(start);cells={start}
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining and grid[p[0]][p[1]]==colour:remaining.remove(p);cells.add(p);stack.append(p)
        r0,r1=min(r for r,c in cells),max(r for r,c in cells);c0,c1=min(c for r,c in cells),max(c for r,c in cells)
        cy,cx=r0+1,c0+1
        ring={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-{(cy,cx)}
        if (r1-r0,c1-c0)!=(2,2) or cells!=ring or grid[cy][cx]!=bg:raise ValueError('Invalid hollow square component')
        centres.append((cy,cx,colour))
    if not centres:raise ValueError('No square components')
    py,px=centres[0][0]%4,centres[0][1]%4
    ys=list(range(py,h-1,4));xs=list(range(px,w-1,4))
    if len(ys)!=7 or len(xs)!=7:raise ValueError('Invalid lattice size')
    lat=[[bg]*7 for _ in range(7)]
    for r,c,v in centres:
        if r not in ys or c not in xs:raise ValueError('Inconsistent lattice phase')
        lat[ys.index(r)][xs.index(c)]=v
    horizontal=side in ('top','bottom')
    if not horizontal:lat=[list(col) for col in zip(*lat)]
    if any(row[3]!=bg for row in lat):raise ValueError('Occupied separator')
    lo=sum(v==landmark for row in lat for v in row[:3]);hi=sum(v==landmark for row in lat for v in row[4:])
    if bool(lo)==bool(hi):raise ValueError('Landmark must occupy one half only')
    compact=[[v for v in row if v!=bg] for row in lat]
    def pack(end):
        rows=[([bg]*(6-len(row))+row if end else row+[bg]*(6-len(row))) for row in compact]
        return rows if horizontal else [list(col) for col in zip(*rows)]
    cw_end=side in ('top','right')
    return {'eight':pack(hi>0),'cw':pack(cw_end),'ccw':pack(not cw_end)}


def surviving_pack_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('afe3afe9: demonstrations required')
    alive={'eight','cw','ccw'}
    try:
        for p in demonstrations:alive &= {k for k,v in pack_options(p['input'],palette).items() if v==p['output']}
    except (ValueError,IndexError,TypeError) as e:raise MissingColourEvidence('afe3afe9: invalid packing demonstration') from e
    if not alive:raise MissingColourEvidence('afe3afe9: no demonstrated packing rule')
    return alive


def require_pack_evidence(demonstrations,queries,palette):
    alive=surviving_pack_rules(demonstrations,palette)
    for q in queries:
        try:opts=pack_options(q['input'],palette)
        except (ValueError,IndexError,TypeError) as e:raise MissingColourEvidence('afe3afe9: invalid query lattice') from e
        outputs=[opts[h] for h in sorted(alive)]
        if any(p!=outputs[0] for p in outputs[1:]):raise MissingColourEvidence('afe3afe9: unresolved packing direction')
