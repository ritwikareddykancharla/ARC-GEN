"""Independent coordinate-set check of demonstrated panel composition rules."""
import itertools
from .colour_evidence import MissingColourEvidence

POLICIES=('over','under','near','axis',(0,-1),(0,1),(-1,0),(1,0))
ORDERS=('panel_fwd','panel_bwd','size_desc','size_asc')
RULES=tuple(itertools.product(ORDERS,POLICIES))


def _intervals(lines,n):
    remaining=set(range(n))-set(lines);groups=[]
    while remaining:
        start=min(remaining);end=start
        while end in remaining:remaining.remove(end);end+=1
        groups.append((start,end))
    return groups


def panel_pieces(grid,palette):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):raise ValueError('Invalid grid')
    H,W=len(grid),len(grid[0]);bg,divider=palette[8],palette[0]
    rows=[r for r in range(H) if set(grid[r])=={divider}]
    cols=[c for c in range(W) if {grid[r][c] for r in range(H)}=={divider}]
    boxes=list(itertools.product(_intervals(rows,H),_intervals(cols,W)))
    if len(boxes)!=3:raise ValueError('Expected three panels')
    h,w=boxes[0][0][1]-boxes[0][0][0],boxes[0][1][1]-boxes[0][1][0]
    pieces=[]
    for (r0,r1),(c0,c1) in boxes:
        if (r1-r0,c1-c0)!=(h,w):raise ValueError('Unequal panel sizes')
        pixels={(r-r0,c-c0):grid[r][c] for r in range(r0,r1) for c in range(c0,c1) if grid[r][c] not in (bg,divider)}
        remaining=set(pixels);components=[]
        while remaining:
            seed=remaining.pop();todo=[seed];component={seed}
            while todo:
                r,c=todo.pop()
                for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if q in remaining and pixels[q]==pixels[seed]:remaining.remove(q);component.add(q);todo.append(q)
            components.append(component)
        if len(components)!=2:raise ValueError('Expected two components per panel')
        sizes=[len(c) for c in components]
        if sizes[0]==sizes[1]:raise ValueError('Tied largest component')
        winner=components[sizes.index(max(sizes))]
        pieces.append({p:pixels[p] for p in winner})
    return h,w,pieces


def _render(pieces,order,policy,h,w,bg):
    occupied={}
    domain=set(itertools.product(range(h),range(w)))
    for index in order:
        cells=pieces[index]
        if policy=='over':occupied.update(cells);continue
        if policy=='under':
            for p,v in cells.items():occupied.setdefault(p,v)
            continue
        if not set(cells)&set(occupied):offset=(0,0)
        else:
            shifts=[]
            for dr in range(-h,h+1):
                for dc in range(-w,w+1):
                    moved={(r+dr,c+dc) for r,c in cells}
                    if not moved<=domain or moved&set(occupied):continue
                    if policy=='axis' and dr and dc:continue
                    if isinstance(policy,tuple):
                        vr,vc=policy
                        if not any((dr,dc)==(n*vr,n*vc) for n in range(1,max(h,w)+1)):continue
                    shifts.append((dr,dc))
            if not shifts:return None
            distance=min(abs(r)+abs(c) for r,c in shifts)
            closest=[p for p in shifts if abs(p[0])+abs(p[1])==distance]
            if len(closest)!=1:return None
            offset=closest[0]
        dr,dc=offset
        occupied.update({(r+dr,c+dc):v for (r,c),v in cells.items()})
    return tuple(tuple(occupied.get((r,c),bg) for c in range(w)) for r in range(h))


def collision_predictions(grid,palette):
    h,w,pieces=panel_pieces(grid,palette);indices=tuple(range(len(pieces)));predictions=[]
    for ordering,policy in RULES:
        if ordering=='panel_fwd':orders=[indices]
        elif ordering=='panel_bwd':orders=[indices[::-1]]
        else:
            lengths=sorted((len(p) for p in pieces),reverse=ordering=='size_desc')
            orders=[order for order in itertools.permutations(indices) if [len(pieces[i]) for i in order]==lengths]
        answers={_render(pieces,order,policy,h,w,palette[8]) for order in orders}
        predictions.append(next(iter(answers)) if None not in answers and len(answers)==1 else None)
    return predictions


def surviving_collision_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('337b420f: demonstrations required')
    alive=set(range(len(RULES)))
    for pair in demonstrations:
        try:predictions=collision_predictions(pair['input'],palette)
        except ValueError as e:raise MissingColourEvidence('337b420f: invalid demonstration geometry') from e
        expected=tuple(tuple(row) for row in pair['output'])
        alive &= {i for i,p in enumerate(predictions) if p==expected}
    if not alive:raise MissingColourEvidence('337b420f: no consistent demonstrated collision rule')
    return alive


def require_collision_evidence(demonstrations,queries,palette):
    alive=surviving_collision_rules(demonstrations,palette)
    for query in queries:
        try:predictions=collision_predictions(query['input'],palette)
        except ValueError as e:raise MissingColourEvidence('337b420f: invalid query geometry') from e
        answers={predictions[i] for i in alive}
        if None in answers or len(answers)!=1:raise MissingColourEvidence('337b420f: unresolved collision placement')
