"""Fresh latent-scene constructors; outputs do not call the saved solver.

These cover bounded subfamilies, not every possible input to their task.
The separate audit compares original fixtures and randomized generated pairs.
"""
import random
from .extended import blank

def legend_glyph(rng):
    h,w=rng.randint(12,30),rng.randint(10,30)
    glyphs=[([[1,1,1],[1,0,1],[0,1,0]],7),
            ([[1,0,1],[0,1,0],[1,1,1]],3),
            ([[0,1,0],[1,1,1],[0,1,0]],2)]
    glyph,c=rng.choice(glyphs);a=blank(h,w);b=blank(h,w)
    # Connected drawing with a bbox strictly larger than the 3x3 glyph.
    dh,dw=rng.randint(4,h-7),rng.randint(4,w-2)
    y0,x0=1,rng.randint(0,w-dw)
    cells={(y,x) for y in range(dh) for x in range(dw) if y==0 or x==0 or rng.random()<.35}
    for y,x in cells:a[y0+y][x0+x]=8;b[y0+y][x0+x]=c
    sy,sx=rng.randint(dh+3,h-3),rng.randint(0,w-3)
    for y in range(3):
        for x in range(3):
            if glyph[y][x]:a[sy+y][sx+x]=1
    return {'input':a,'output':b}

def hole_count_colour(rng):
    h,w=rng.randint(16,30),rng.randint(20,30)
    a=blank(h,w);b=blank(h,w);table={1:1,2:3,3:2,4:4}
    for sy in range(1,h-4,6):
        for sx in range(1,w-9,10):
            n=rng.randint(1,4);hh=rng.randint(3,5);ww=2*n+1
            cells={(y,x) for y in range(hh) for x in range(ww) if y in (0,hh-1) or x%2==0}
            for y,x in cells:a[sy+y][sx+x]=8;b[sy+y][sx+x]=table[n]
    return {'input':a,'output':b}

def embedded_pluses(rng):
    h,w=rng.randint(9,30),rng.randint(9,30);a=blank(h,w,2);b=blank(h,w,2)
    offsets=[(0,0),(-1,0),(1,0),(0,-1),(0,1)]
    # Each separated patch is either a complete plus or a proper fragment.
    sites=[(y,x) for y in range(2,h-2,4) for x in range(2,w-2,4)]
    rng.shuffle(sites)
    for i,(y,x) in enumerate(sites):
        full=i==0 or rng.random()<.55
        cells=offsets if full else rng.sample(offsets,rng.randint(1,4))
        for dy,dx in cells:a[y+dy][x+dx]=4;b[y+dy][x+dx]=8 if full else 4
        # One extra diagonal attachment demonstrates matching within a blob.
        if full and rng.random()<.5:a[y-1][x-1]=b[y-1][x-1]=4
    return {'input':a,'output':b}

def count_snake_walls(rng):
    h,w=rng.randint(10,30),rng.randint(8,30);a=blank(h,w)
    lanes=list(range(1,h-2,4));rng.shuffle(lanes);n=rng.randint(1,len(lanes))
    for y in lanes[:n]:
        bend=rng.randint(1,w-2);down=rng.choice([0,1])
        for x in range(w):a[y+(down if x>bend else 0)][x]=5
        if down:a[y+1][bend]=5
    return {'input':a,'output':blank(n+1,1)}

def orient_dominoes(rng):
    h,w=rng.randint(10,30),rng.randint(10,30);a=blank(h,w,8);b=blank(h,w,8)
    vertical=rng.choice([False,True])
    length,count=(h,w) if vertical else (w,h)
    for line in range(1,count-1,3):
        start=rng.randint(2,length-4);left=rng.choice([True,False]);target=0 if left else length-1
        def put(g,offset,c):
            if vertical:g[offset][line]=c
            else:g[line][offset]=c
        put(a,target,7);put(b,target,7)
        original=rng.choice([(1,6),(6,1)]);correct=(6,1) if left else (1,6)
        for j in range(2):put(a,start+j,original[j]);put(b,start+j,correct[j])
    return {'input':a,'output':b}

def duplicate_object(rng):
    h,w=rng.randint(12,30),rng.randint(12,30);a=blank(h,w)
    th,tw=rng.randint(2,4),rng.randint(2,4)
    # Dense multicolour objects avoid disconnected fragments; use random holes
    # only off the first row/column, keeping the whole object connected.
    tile=[[rng.randint(1,9) for x in range(tw)] for y in range(th)]
    positions=[(1,1),(1,w-tw-1),(h-th-1,1),(h-th-1,w-tw-1)]
    rng.shuffle(positions)
    for i,(y0,x0) in enumerate(positions):
        piece=[r[:] for r in tile]
        if i>=2:piece[0][0]=1+(tile[0][0]+i-1)%9
        for y in range(th):
            for x in range(tw):a[y0+y][x0+x]=piece[y][x]
    return {'input':a,'output':tile}

def anchor_stamping(rng):
    h,w=rng.randint(12,30),rng.randint(12,30);a=blank(h,w);b=blank(h,w)
    th,tw=rng.randint(2,4),rng.randint(2,4)
    shape={(y,x) for y in range(th) for x in range(tw) if (y,x)!=(0,0) and (y==0 or x==0 or rng.random()<.6)}
    positions=[(1,1),(1,w-tw-1),(h-th-1,1),(h-th-1,w-tw-1)]
    rng.shuffle(positions);ay,ax=positions.pop();a[ay][ax]=3
    for y,x in shape:a[ay+y][ax+x]=8
    for ty,tx in positions[:rng.randint(1,3)]:
        a[ty][tx]=2
        for y,x in shape:b[ty+y][tx+x]=8
    return {'input':a,'output':b}

def size_relational_motion(rng):
    h,w=rng.randint(14,30),rng.randint(18,30);a=blank(h,w);b=blank(h,w)
    n=min(5,(w-1)//5);shared=rng.randint(3,7)
    unique=rng.sample([i for i in range(2,10) if i!=shared],n-2)
    sizes=[shared,shared,*unique];rng.shuffle(sizes)
    colours=rng.sample(range(1,10),n)
    for i,(size,c) in enumerate(zip(sizes,colours)):
        cells={(0,0)}
        while len(cells)<size:
            y,x=rng.choice(sorted(cells));dy,dx=rng.choice([(0,1),(1,0),(1,1)])
            if y+dy<4 and x+dx<4:cells.add((y+dy,x+dx))
        height=1+max(y for y,x in cells);sy=rng.randint(2,h-height-2);sx=1+i*5
        dest=0 if size==shared else h-height
        for y,x in cells:a[sy+y][sx+x]=c;b[dest+y][sx+x]=c
    return {'input':a,'output':b}

def repair_periodic_panel(rng):
    p=rng.randint(2,4);length=p*rng.randint(4,min(6,24//p));width=rng.randint(1,3)
    h,w=width+8,length+6;a=blank(h,w);b=blank(h,w)
    y0,x0=3,2
    palette=rng.sample([1,2,3,4,8,9],p)
    tile=[[palette[(x+y)%p] for x in range(p)] for y in range(width)]
    for y in range(width+2):
        for x in range(length+2):
            c=6 if y in (0,width+1) or x in (0,length+1) else tile[y-1][(x-1)%p]
            a[y0+y][x0+x]=b[y0+y][x0+x]=c
    cy,cx=rng.randint(1,width),rng.randint(1,length)
    a[y0+cy][x0+cx]=rng.choice([c for c in palette if c!=a[y0+cy][x0+cx]])
    if rng.random()<.5:a=[list(r) for r in zip(*a)];b=[list(r) for r in zip(*b)]
    return {'input':a,'output':b}

def union_subset_tiles(rng):
    h,w=16,11;a=blank(h,w);b=blank(h,w)
    full=set(rng.sample(range(16),rng.randint(9,13)))
    order=list(full);rng.shuffle(order);cut=rng.randint(3,len(order)-3)
    left,right=set(order[:cut]),set(order[cut:]);outside=list(set(range(16))-full)
    pieces=[(full,3),(left,8),(right,8)]
    for _ in range(3):
        other=set(rng.sample(range(16),rng.randint(2,len(full)-1)))
        other.add(rng.choice(outside))
        if len(other)>=len(full):other.remove(next(c for c in other if c in full))
        pieces.append((other,2))
    rng.shuffle(pieces)
    for (sy,sx),(cells,c) in zip([(y,x) for y in [1,6,11] for x in [1,6]],pieces):
        for i in cells:a[sy+i//4][sx+i%4]=2;b[sy+i//4][sx+i%4]=c
    return {'input':a,'output':b}

GENERATORS={
 '009d5c81':legend_glyph,'0a2355a6':hole_count_colour,'1818057f':embedded_pluses,
 'e872b94a':count_snake_walls,'f341894c':orient_dominoes,'f5aa3634':duplicate_object,
 'f5c89df1':anchor_stamping,'62593bfd':size_relational_motion,
 '135a2760':repair_periodic_panel,'fea12743':union_subset_tiles,
}
