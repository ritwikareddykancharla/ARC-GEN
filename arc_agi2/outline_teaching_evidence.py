"""Independent gates for proposed teaching copies; no canonical relabelling."""
from collections import deque
from .colour_evidence import MissingColourEvidence


def ring_output(grid, palette):
    bg, frame, ink = (palette[c] for c in (0, 5, 2))
    points={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    if not points or any(grid[r][c]!=frame for r,c in points):raise ValueError('Frame colours')
    r0=min(r for r,c in points);r1=max(r for r,c in points)
    c0=min(c for r,c in points);c1=max(c for r,c in points)
    if r1-r0!=c1-c0:raise ValueError('Not square')
    rim={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if r in (r0,r1) or c in (c0,c1)}
    if points!=rim:raise ValueError('Not a hollow frame')
    out=[row[:] for row in grid];cycle=(frame,ink,frame,bg);level=0
    while r0<=r1:
        for r in range(r0,r1+1):out[r][c0]=out[r][c1]=cycle[level%4]
        for c in range(c0,c1+1):out[r0][c]=out[r1][c]=cycle[level%4]
        r0+=1;r1-=1;c0+=1;c1-=1;level+=1
    return out


def components(points):
    points=set(points)
    while points:
        seed=points.pop();part={seed};todo=[seed]
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in points:points.remove(p);part.add(p);todo.append(p)
        yield part


def rectangular(cells):
    if not cells:return False
    return len(cells)==(max(r for r,c in cells)-min(r for r,c in cells)+1)*(max(c for r,c in cells)-min(c for r,c in cells)+1)


def rectangle_cover(cells):
    if rectangular(cells):return [cells]
    # Enumerate corner-anchored rectangles and their complementary rectangles.
    # Different from the emitted program's horizontal/vertical cut enumeration.
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells);options={}
    for anchor_r in (r0,r1):
        for anchor_c in (c0,c1):
            for rr in range(r0,r1+1):
                for cc in range(c0,c1+1):
                    a={(r,c) for r in range(min(anchor_r,rr),max(anchor_r,rr)+1) for c in range(min(anchor_c,cc),max(anchor_c,cc)+1)}
                    if not a<=cells:continue
                    b=cells-a
                    if not rectangular(b):continue
                    key=tuple(sorted((tuple(sorted(a)),tuple(sorted(b)))))
                    options[key]=(a,b)
    if not options:raise ValueError('No rectangle cover')
    smallest=min(min(map(len,v)) for v in options.values())
    chosen=[v for v in options.values() if min(map(len,v))==smallest]
    if len(chosen)!=1:raise ValueError('Nonunique native rectangle cover')
    return chosen[0]


def outline_outputs(grid,palette):
    bg,wall,red,green=(palette[c] for c in (0,1,2,3));h=len(grid);w=len(grid[0])
    if any(v not in (bg,wall) for row in grid for v in row):raise ValueError('Unexpected colour')
    outputs={m:[row[:] for row in grid] for m in ('pieces','touch')}
    for boundary in components({(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==wall}):
        # Background components in a padded domain detect closure independently.
        universe={(r,c) for r in range(-1,h+1) for c in range(-1,w+1)}
        interiors=[]
        for region in components(universe-boundary):
            if not any(r in (-1,h) or c in (-1,w) for r,c in region):interiors.append(region)
        if not interiors:continue
        inside=set().union(*interiors)
        halo={(r+dr,c+dc) for r,c in boundary for dr in (-1,0,1) for dc in (-1,0,1)}-boundary-inside
        touch={(r,c) for r,c in inside if any((r+dr,c+dc) in boundary for dr in (-1,0,1) for dc in (-1,0,1))}
        lining=set()
        for rectangle in rectangle_cover(inside):
            lining.update((r,c) for r,c in rectangle if any(p not in rectangle for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))))
        for mode,out in outputs.items():
            for r,c in halo:
                if 0<=r<h and 0<=c<w and grid[r][c]==bg:out[r][c]=red
            for r,c in (lining if mode=='pieces' else touch):
                if grid[r][c]==bg:out[r][c]=green
    return outputs


def require_ring_teaching_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('a3f84088: missing demonstrations')
    try:
        for pair in demonstrations:
            if ring_output(pair['input'],palette)!=pair['output']:raise ValueError('Contradictory ring demonstration')
        for q in queries:ring_output(q['input'] if isinstance(q,dict) else q,palette)
    except ValueError as e:raise MissingColourEvidence('a3f84088: '+str(e)) from e


def require_outline_teaching_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('d931c21c: missing demonstrations')
    try:
        alive={'pieces','touch'}
        for pair in demonstrations:
            options=outline_outputs(pair['input'],palette)
            alive={m for m in alive if options[m]==pair['output']}
        if not alive:raise ValueError('Contradictory outline demonstration')
        for q in queries:
            grid=q['input'] if isinstance(q,dict) else q
            options=outline_outputs(grid,palette)
            if len({tuple(map(tuple,options[m])) for m in alive})!=1:raise ValueError('Unresolved seam mechanism')
            observed={v for pair in demonstrations for row in pair['output'] for v in row}|{v for row in grid for v in row}
            if any(v not in observed for row in options[next(iter(alive))] for v in row):raise ValueError('Undemonstrated output colour')
    except ValueError as e:raise MissingColourEvidence('d931c21c: '+str(e)) from e
