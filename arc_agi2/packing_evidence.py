"""Episode evidence for minimum-rotation packing and positional swap ties.

An independent exact-cover DP enumerates all optimal placements. Compare four
keep-orientation directions with sixteen input/output relative-order mappings.
Unresolved policy ties retain ALL paintings, never an enumeration-order answer.
The scope is the family's fixed rectangle and minimum-rotated-piece objective;
this is not an exhaustive hypothesis space for all possible ARC mechanisms.
"""
from functools import lru_cache
from itertools import combinations, product

from .colour_evidence import MissingColourEvidence

DIRECTIONS = ((-1,0),(1,0),(0,-1),(0,1))


def _norm(cells):
    top,left = min(r for r,c in cells),min(c for r,c in cells)
    return tuple(sorted((r-top,c-left) for r,c in cells))


def _pieces(g,bg):
    cells = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != bg}
    groups = {}
    while cells:
        p = min(cells)
        cells.remove(p)
        colour = g[p[0]][p[1]]
        component,stack = {p},[p]
        while stack:
            r,c = stack.pop()
            for dr,dc in DIRECTIONS:
                q = r+dr,c+dc
                if q in cells and g[q[0]][q[1]] == colour:
                    cells.remove(q)
                    component.add(q)
                    stack.append(q)
        groups.setdefault((colour,_norm(component)),[]).append(tuple(sorted(component)))
    return tuple((colour,shape,tuple(members)) for (colour,shape),members in groups.items())


def optimal_packings(g,bg,oh,ow):
    """All minimum-cost tilings, with identical pieces counted by multiplicity."""
    types = _pieces(g,bg)
    area = oh*ow
    if sum(len(shape)*len(members) for colour,shape,members in types) != area:
        raise MissingColourEvidence('b7cb93ac: piece area differs from output rectangle')
    full = (1 << area)-1
    placements = [[] for _ in range(area)]
    for ti,(colour,original,members) in enumerate(types):
        shape,rotations = original,set()
        for _ in range(4):
            rotations.add(shape)
            shape = _norm([(c,-r) for r,c in shape])
        for shape in sorted(rotations):
            height,width = max(r for r,c in shape)+1,max(c for r,c in shape)+1
            for top in range(oh-height+1):
                for left in range(ow-width+1):
                    mask = sum(1 << ((top+r)*ow+left+c) for r,c in shape)
                    placement = (ti,mask,int(shape != original))
                    for p in range(area):
                        if mask & (1 << p):
                            placements[p].append(placement)
    counts = tuple(len(members) for colour,shape,members in types)
    def choices(mask,remaining):
        free = full ^ mask
        first = (free & -free).bit_length()-1
        for ti,pm,cost in placements[first]:
            if remaining[ti] and not pm & mask:
                nxt = list(remaining)
                nxt[ti] -= 1
                yield (ti,pm,cost),tuple(nxt)
    @lru_cache(None)
    def minimum(mask,remaining):
        if mask == full:
            return 0 if not any(remaining) else 999
        return min((p[2]+minimum(mask|p[1],nxt) for p,nxt in choices(mask,remaining)),default=999)
    cost = minimum(0,counts)
    if cost == 999:
        raise MissingColourEvidence('b7cb93ac: no exact rectangle packing')
    tilings = []
    def visit(mask,remaining,path):
        if mask == full:
            tilings.append(tuple(path))
            return
        best = minimum(mask,remaining)
        for p,nxt in choices(mask,remaining):
            if p[2]+minimum(mask|p[1],nxt) == best:
                visit(mask|p[1],nxt,path+[p])
    visit(0,counts,[])
    return types,tuple(tilings),cost


def _bounds(cells,direction):
    dr,dc = direction
    values = [dr*r+dc*c for r,c in cells]
    return min(values),max(values)


def _order(a,b,direction):
    amin,amax = _bounds(a,direction)
    bmin,bmax = _bounds(b,direction)
    return 1 if amin > bmax else -1 if bmin > amax else 0


@lru_cache(maxsize=256)
def packing_candidates(g,bg,oh,ow):
    types,tilings,cost = optimal_packings(g,bg,oh,ow)
    paintings,counts,placed = [],[],[]
    for tiling in tilings:
        out = [[bg]*ow for _ in range(oh)]
        unrotated = [0]*len(types)
        slots = {}
        for ti,mask,rotation in tiling:
            cells = [(p//ow,p%ow) for p in range(oh*ow) if mask & (1 << p)]
            for r,c in cells:
                out[r][c] = types[ti][0]
            unrotated[ti] += rotation == 0
            slots.setdefault(ti,[]).append(cells)
        paintings.append(tuple(map(tuple,out)))
        counts.append(unrotated)
        placed.append(slots)
    def best(scores):
        top = max(scores)
        return frozenset(p for p,s in zip(paintings,scores) if s == top)
    result = []
    for direction in DIRECTIONS:
        projections = [max(_bounds(m,direction)[0] for m in members) for colour,shape,members in types]
        levels = sorted(set(projections),reverse=True)
        # Equal-projection types are one tier, not a hidden type-ID ordering.
        result.append(best([tuple(sum(n[i] for i,p in enumerate(projections) if p == level)
                                  for level in levels) for n in counts]))
    pairs = [(i,j) for i,j in combinations(range(len(types)),2)
             if types[i][1] == types[j][1] and len(types[i][2]) == len(types[j][2]) == 1]
    for before,after in product(DIRECTIONS,repeat=2):
        relations = [(i,j,_order(types[i][2][0],types[j][2][0],before)) for i,j in pairs]
        result.append(best([sum(order*_order(slots[i][0],slots[j][0],after)
                                for i,j,order in relations) for slots in placed]))
    return tuple(result)


def require_packing_evidence(demonstrations,queries,palette):
    dimensions = {(len(d['output']),len(d['output'][0])) for d in demonstrations
                  if d['output'] and d['output'][0]}
    if len(dimensions) != 1 or not dimensions <= {(3,4),(4,3)}:
        raise MissingColourEvidence('b7cb93ac: demonstrations do not establish one rectangle shape')
    oh,ow = next(iter(dimensions))
    candidates = lambda g: packing_candidates(tuple(map(tuple,g)),palette[0],oh,ow)
    possible = set(range(20))
    for demo in demonstrations:
        expected = tuple(map(tuple,demo['output']))
        possible &= {i for i,paintings in enumerate(candidates(demo['input'])) if expected in paintings}
    if not possible:
        raise MissingColourEvidence('b7cb93ac: demonstrations fit no minimum-rotation positional rule')
    for query in queries:
        variants = candidates(query['input'])
        paintings = set().union(*(variants[i] for i in possible))
        if len(paintings) != 1:
            raise MissingColourEvidence('b7cb93ac: demonstrations leave swap-tie convention ambiguous')


@lru_cache(maxsize=4096)
def _fitting_mask(g,output,bg,oh,ow):
    return sum(1 << i for i,options in enumerate(packing_candidates(g,bg,oh,ow)) if output in options)


def select_packing_demonstrations(rows,query_input,rng,exclude_canonical_hash=None,pair_uses=None):
    """Find three distinct teaching examples without reading the query answer.

    Rows have already been filtered by split and reuse allowance by the caller.
    Group equivalent policy evidence and exhaustively search combinations of
    up to three groups. A repeat of an evidence group cannot remove further
    policies, so it is only useful as a filler after the query is resolved.
    """
    if not rows:
        return None
    oh,ow = len(rows[0]['output']),len(rows[0]['output'][0])
    if (oh,ow) not in ((3,4),(4,3)):
        return None
    options = packing_candidates(tuple(map(tuple,query_input)),0,oh,ow)
    full = (1 << 20)-1
    def identity(row):
        return row.get('canonical_input_hash',tuple(map(tuple,row['input'])))
    groups,row_masks = {},{}
    shuffled = list(rows)
    rng.shuffle(shuffled)
    pair_uses = {} if pair_uses is None else pair_uses
    usage = lambda row: pair_uses.get(row.get('input_hash'),0)
    shuffled.sort(key=usage)
    for row in shuffled:
        if identity(row) == exclude_canonical_hash:
            continue
        output = tuple(map(tuple,row['output']))
        if len(output) != oh or any(len(r) != ow for r in output):
            continue
        mask = _fitting_mask(tuple(map(tuple,row['input'])),output,0,oh,ow)
        if mask:
            groups.setdefault(mask,[]).append(row)
            row_masks[id(row)] = mask
    def resolved(mask):
        return mask and len(set().union(*(options[i] for i in range(20) if mask & (1 << i)))) == 1
    # Do not spend scarce tie witnesses as fillers for already-unambiguous
    # queries. Respect the caller's reuse cap and prefer less-used witnesses.
    fillers = sorted(shuffled,key=lambda row: (row_masks.get(id(row),0) != full,usage(row)))
    def choose(masks):
        # Distinct canonical inputs, including when different evidence groups
        # happen to contain rotated/recoloured copies of the same input.
        def select(index,selected,used):
            if index == len(masks):
                if len(selected) == 3:
                    return selected
                alive = full
                for mask in masks:
                    alive &= mask
                for row in fillers:
                    key = identity(row)
                    mask = row_masks.get(id(row),0)
                    if key not in used and key != exclude_canonical_hash and alive & mask:
                        selected = selected+[row]
                        used = used|{key}
                        alive &= mask
                        if len(selected) == 3:
                            return selected
                return selected if len(selected) == 3 else None
            for row in groups[masks[index]]:
                key = identity(row)
                if key not in used:
                    answer = select(index+1,selected+[row],used|{key})
                    if answer is not None:
                        return answer
            return None
        return select(0,[],set())
    if resolved(full):
        return choose(())
    masks = sorted((mask for mask in groups if mask != full),key=int.bit_count)
    viable = []
    for count in (1,2,3):
        for selected in combinations(masks,count):
            alive = full
            for mask in selected:
                alive &= mask
            if resolved(alive):
                uses = [usage(groups[mask][0]) for mask in selected]
                viable.append(((max(uses),sum(uses),count),selected))
    # All group combinations are considered before preferring a short context:
    # otherwise the strongest rare witness is repeatedly exhausted while
    # available, slightly longer teaching combinations remain unused.
    for score,selected in sorted(viable,key=lambda item:item[0]):
        demos = choose(selected)
        if demos is not None:
            return demos
    return None
