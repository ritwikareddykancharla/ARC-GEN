"""Constructive counting, selection, geometry and symmetry subfamilies.

Each output is rendered from the sampled latent scene, independently of the
archived transform. See function docstrings for deliberately bounded scope.
"""
from .extended import blank

def paint(g,cells,c,origin=(0,0)):
    for y,x in cells:g[y+origin[0]][x+origin[1]]=c

def polyomino(rng,n,side=5):
    cells={(0,0)}
    while len(cells)<n:
        frontier={(y+dy,x+dx) for y,x in cells for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]
                  if 0<=y+dy<side and 0<=x+dx<side}-cells
        cells.add(rng.choice(sorted(frontier)))
    return cells

def objects_scene(rng,bg=0):
    """2–6 separated monochrome polyominoes, distinct areas and colours."""
    h,w=rng.randint(18,30),rng.randint(18,30);a=blank(h,w,bg)
    sites=[(y,x) for y in range(1,h-5,7) for x in range(1,w-5,7)]
    rng.shuffle(sites);n=rng.randint(2,min(6,len(sites)))
    sizes=rng.sample(range(2,20),n);colours=rng.sample([i for i in range(10) if i!=bg],n)
    objs=[]
    for origin,size,c in zip(sites,sizes,colours):
        cells=polyomino(rng,size);paint(a,cells,c,origin);objs.append((cells,c,origin))
    return a,objs

def parity_corner(rng):
    """Square random mosaics; parity interpretation is a reference hypothesis."""
    n=rng.randint(3,30);a=[[rng.randrange(10) for x in range(n)] for y in range(n)]
    x=n-2 if n%2==0 else 0
    return {'input':a,'output':[row[x:x+2] for row in a[:2]]}

def largest_blob(rng):
    """Blobs plus disconnected noise; object size, not colour frequency."""
    a,objs=objects_scene(rng);win=max(objs,key=lambda o:len(o[0]))[1]
    used={c for _,c,_ in objs};noise=next(c for c in range(1,10) if c not in used)
    h,w=len(a),len(a[0])
    for y in range(0,h,2):
        for x in range(0,w,2):
            if a[y][x]==0 and rng.random()<.65:a[y][x]=noise
    return {'input':a,'output':blank(3,3,win)}

def trim_objects(rng):
    a,objs=objects_scene(rng,bg=8);b=[r[:] for r in a]
    for cells,c,(sy,sx) in objs:
        for y,x in cells:
            if x<2:b[sy+y][sx+x]=8
    return {'input':a,'output':b}

def row_complement(rng):
    h,w=rng.randint(3,30),rng.randint(5,30);a=blank(h,w);b=blank(h,w)
    for y in range(h):
        c=rng.randint(1,9);positions=set(rng.sample(range(w),rng.randint(max(2,w//2),w-1)))
        others=[v for v in range(1,10) if v!=c]
        for x in range(w):
            a[y][x]=c if x in positions else (rng.choice(others) if rng.random()<.2 else 0)
            b[y][x]=0 if x in positions else c
    return {'input':a,'output':b}

def size_to_rings(rng):
    a,objs=objects_scene(rng,bg=7);cols=[c for cells,c,pos in sorted(objs,key=lambda o:-len(o[0]))]
    s=2*len(cols)-1;b=[[cols[min(y,x,s-1-y,s-1-x)] for x in range(s)] for y in range(s)]
    return {'input':a,'output':b}

def unique_object(rng):
    h,w=rng.randint(18,30),rng.randint(18,30);a=blank(h,w)
    tiles=[[[rng.randint(1,9) for x in range(3)] for y in range(3)] for _ in range(3)]
    # Guarantee distinct appearances without requiring random rejection.
    for i,t in enumerate(tiles):t[0][0]=i+1
    items=[tiles[0],tiles[0],tiles[1],tiles[1],tiles[2]];rng.shuffle(items)
    sites=[(y,x) for y in range(1,h-3,6) for x in range(1,w-3,6)];rng.shuffle(sites)
    for (sy,sx),t in zip(sites,items):
        for y in range(3):
            for x in range(3):a[sy+y][sx+x]=t[y][x]
    return {'input':a,'output':tiles[2]}

def counts_to_rectangle(rng):
    h,w=rng.randint(12,30),rng.randint(12,30);a=blank(h,w,7);b=blank(16,16,7)
    small,big=sorted(rng.sample(range(2,17),2));c,d=rng.sample([i for i in range(10) if i!=7],2)
    sites=[(y,x) for y in range(0,h,2) for x in range(0,w,2)];rng.shuffle(sites)
    for (y,x),v in zip(sites,[c]*small+[d]*big):a[y][x]=v
    for y in range(16-small,16):
        for x in range(big):b[y][x]=4 if x in [15-y,big-1-(15-y)] else 2
    return {'input':a,'output':b}

def count_frame_dots(rng):
    h,w=rng.randint(18,30),rng.randint(18,30);a=blank(h,w)
    sites=[(y,x) for y in range(1,h-6,8) for x in range(1,w-6,8)];rng.shuffle(sites)
    n=rng.randint(2,min(5,len(sites)));nums=rng.sample(range(1,17),n)
    cols=rng.sample([1,2,3,4,6,7,8,9],n)
    for (sy,sx),count,c in zip(sites,nums,cols):
        for y in range(6):
            for x in range(6):
                if y in [0,5] or x in [0,5]:a[sy+y][sx+x]=c
        for i in rng.sample(range(16),count):a[sy+1+i//4][sx+1+i%4]=5
    b=blank(n,max(nums))
    for y,(count,c) in enumerate(sorted(zip(nums,cols))):b[y][:count]=[c]*count
    return {'input':a,'output':b}

def symmetry_selection(rng,want_symmetric=False):
    h,w=rng.randint(18,30),rng.randint(18,30);a=blank(h,w)
    sites=[(1,1),(1,w-6),(h-6,1),(h-6,w-6)];rng.shuffle(sites)
    cols=rng.sample(range(1,10),4);answer=None
    for i,((sy,sx),c) in enumerate(zip(sites,cols)):
        t=blank(5,5)
        for y in range(5):
            t[y][2]=c
            for x in range(2):
                if y in [0,4] or rng.random()<.5:t[y][x]=t[y][4-x]=c
        symmetric=(i==0) if want_symmetric else (i!=0)
        if not symmetric:t[0][0]=0
        for y in range(5):
            for x in range(5):a[sy+y][sx+x]=t[y][x]
        if i==0:answer=t
    return {'input':a,'output':answer}

def asymmetric_crop(rng):return symmetry_selection(rng,False)
def symmetric_crop(rng):return symmetry_selection(rng,True)

def bottom_sort(rng):
    a,objs=objects_scene(rng,bg=7);h,w=len(a),len(a[0]);b=blank(h,w,7)
    # Sample at most four, so accumulated bbox widths never exceed canvas width.
    if sum(1+max(x for y,x in o[0]) for o in objs)>w:return bottom_sort(rng)
    x=0
    for cells,c,pos in sorted(objs,key=lambda o:len(o[0])):
        oh=1+max(y for y,x in cells);ow=1+max(x for y,x in cells)
        paint(b,cells,c,(h-oh,x));x+=ow
    return {'input':a,'output':b}

def outer_outline(rng):
    h,w=rng.randint(12,30),rng.randint(12,30);a=blank(h,w,8);b=blank(h,w,8)
    hh,ww=rng.randint(3,min(9,h-4)),rng.randint(3,min(9,w-4));sy,sx=rng.randint(1,h-hh-1),rng.randint(1,w-ww-1)
    c,core=rng.sample([i for i in range(10) if i!=8],2)
    for y in range(hh):
        for x in range(ww):a[sy+y][sx+x]=c
    a[sy+hh//2][sx+ww//2]=core
    for x in range(sx,sx+ww):b[sy-1][x]=b[sy+hh][x]=core
    for y in range(sy,sy+hh):b[y][sx-1]=b[y][sx+ww]=core
    return {'input':a,'output':b}

def extract_segments(rng):
    h,w=rng.randint(8,30),rng.randint(8,30)
    a=[[rng.choice([0,0,0,2]) for _ in range(w)] for _ in range(h)]
    gap=rng.randint(1,w-3);ys=sorted(rng.sample(range(h),rng.randint(1,min(10,h))))
    output=[]
    for y in ys:
        x=rng.randint(0,w-gap-2);a[y][x]=1;a[y][x+gap+1]=8;output.append(a[y][x+1:x+gap+1])
    return {'input':a,'output':output}

def row_rings(rng):
    h,w=rng.randint(3,16),rng.randint(1,30);cols=[rng.randrange(10) for _ in range(h-1)];cols.append(cols[-1])
    a=[[c]*w for c in cols];n=2*(h-1)
    b=[[cols[min(y,x,n-1-y,n-1-x)] for x in range(n)] for y in range(n)]
    return {'input':a,'output':b}

def object_barchart(rng):
    h,w=rng.randint(18,30),rng.randint(18,30);a=blank(h,w,7);cols=[5,2,8,9,6]
    sites=[(y,x) for y in range(1,h-2,4) for x in range(1,w-2,4)];rng.shuffle(sites)
    counts=[rng.randint(1,min(4,len(sites)//5)) for _ in cols]
    for c,n in zip(cols,counts):
        for _ in range(n):
            sy,sx=sites.pop();cells=rng.choice([[(0,0)],[(0,0),(1,1)],[(0,0),(0,1),(1,0)],[(0,1),(1,0),(1,2),(2,1)]])
            paint(a,cells,c,(sy,sx))
    b=blank(max(counts),5,7)
    for x,(n,c) in enumerate(zip(counts,cols)):
        for y in range(len(b)-n,len(b)):b[y][x]=c
    return {'input':a,'output':b}

def diagonal_components(rng):
    h,w=rng.randint(14,30),rng.randint(14,30);a=blank(h,w);b=blank(h,w)
    sites=[(y,x) for y in range(1,h-5,6) for x in range(1,w-5,6)];rng.shuffle(sites)
    for i,(sy,sx) in enumerate(sites):
        selected=i==0 or rng.random()<.5
        if selected:
            n=rng.randint(3,5);cells={(j,j) for j in range(n)}
            if rng.random()<.5:cells.add((0,1))
            if rng.random()<.5:cells={(y,n-1-x) for y,x in cells}
        else:cells={(0,x) for x in range(rng.randint(2,5))}|{(1,0)}
        paint(a,cells,5,(sy,sx));paint(b,cells,8 if selected else 5,(sy,sx))
    return {'input':a,'output':b}

def shear_outline(rng):
    h,w=rng.randint(10,30),rng.randint(10,30);a=blank(h,w);b=blank(h,w)
    hh,ww=rng.randint(3,min(10,h-2)),rng.randint(3,min(10,w-2));sy,sx=rng.randint(0,h-hh),rng.randint(0,w-ww);c=rng.randint(1,9)
    for y in range(hh):
        for x in range(ww):
            if y in [0,hh-1] or x in [0,ww-1]:
                a[sy+y][sx+x]=c
                dest=sx+x-(hh-1-y)
                if dest>=0:b[sy+y][dest]=c
    return {'input':a,'output':b}

def offcentre_symmetry(rng):
    """30x30 crop of a 32x32 D4-symmetric mosaic, one erased rectangle."""
    # Latent colours indexed by unordered distances to the two central axes.
    orbit={(i,j):rng.randint(1,9) for i in range(16) for j in range(i,16)}
    b=[[orbit[tuple(sorted([min(y,31-y),min(x,31-x)]))] for x in range(30)] for y in range(30)]
    a=[r[:] for r in b];sy,sx=rng.randint(2,10),rng.randint(2,10)
    hh,ww=rng.randint(2,5),rng.randint(2,5)
    for y in range(sy,sy+hh):
        for x in range(sx,sx+ww):a[y][x]=0
    return {'input':a,'output':b}

def ranked_capped_bars(rng):
    h,w=rng.randint(16,30),rng.randint(18,30);a=blank(h,w);b=blank(h,w)
    cols=rng.sample(range(1,10),rng.randint(1,3));body=rng.choice([i for i in range(1,10) if i not in cols])
    sites=list(range(7,w,2));rng.shuffle(sites)
    for i,c in enumerate(cols):
        n=min(rng.randint(2,3),len(sites)//(len(cols)-i));rank=rng.randint(1,n)
        for y in range(rank):a[y][i*2]=b[y][i*2]=c
        heights=rng.sample(range(3,h-3),n);chosen=sorted(heights,reverse=True)[rank-1]
        for hh in heights:
            x=sites.pop()
            for y in range(h-hh,h):
                v=c if y in [h-hh,h-1] else body;a[y][x]=v;b[y][x]=c if hh==chosen else v
    return {'input':a,'output':b}

GENERATORS={
 'a6953f00':parity_corner,'3194b014':largest_blob,'52364a65':trim_objects,
 '2de01db2':row_complement,'5587a8d0':size_to_rings,'cd3c21df':unique_object,
 '878187ab':counts_to_rectangle,'d4c90558':count_frame_dots,'73ccf9c2':asymmetric_crop,
 'd56f2372':symmetric_crop,'4df5b0ae':bottom_sort,'aa62e3f4':outer_outline,
 '505fff84':extract_segments,'45a5af55':row_rings,'aaecdb9a':object_barchart,
 'ecb67b6d':diagonal_components,'423a55dc':shear_outline,'981571dc':offcentre_symmetry,
 '97d7923e':ranked_capped_bars,
}
