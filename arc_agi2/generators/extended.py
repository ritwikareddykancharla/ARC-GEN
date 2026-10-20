"""Independent constructors based on saved teacher explanations.

Generated outputs are constructed from latent parameters, not by calling the
reference transform. The validation harness compares the two implementations.
Defaults are deliberately variable-size. These are labelled research extensions.
"""
import random

def blank(h,w,c=0):return [[c]*w for _ in range(h)]

def inverse_tiles(rng,height=None,width=None):
    h=height or rng.randint(2,5);w=width or rng.randint(2,5)
    if not(2<=h<=5 and 2<=w<=5):raise ValueError('Squared output must fit 30')
    colour=rng.randint(1,9);cells=rng.sample(range(h*w),rng.randint(1,h*w-1))
    mask=set(cells);a=blank(h,w);b=blank(h*h,w*w)
    for i in mask:a[i//w][i%w]=colour
    for y in range(h*h):
        for x in range(w*w):
            outer=(y//h)*w+x//w;inner=(y%h)*w+x%w
            b[y][x]=colour if outer in mask and inner not in mask else 0
    return {'input':a,'output':b}

def mirrored_tiles(rng,height=None,width=None):
    h=height or rng.randint(2,10);w=width or rng.randint(2,10)
    if not(1<=h<=10 and 1<=w<=10):raise ValueError('Tripled output must fit 30')
    palette=rng.sample(range(10),rng.randint(2,6))
    a=[[rng.choice(palette) for _ in range(w)] for _ in range(h)]
    b=[[a[y%h][w-1-x%w if h<=y<2*h else x%w] for x in range(3*w)] for y in range(3*h)]
    return {'input':a,'output':b}

def sequential_legend(rng,height=None,width=None):
    h=height or rng.randint(8,30);w=width or rng.randint(8,30)
    if not(8<=h<=30 and 8<=w<=30):raise ValueError('Size outside constructor contract')
    colours=rng.sample(range(1,10),rng.randint(4,7))
    rules=list(zip(colours[:-1],colours[1:]));rng.shuffle(rules)
    a=blank(h,w);b=blank(h,w)
    for y,(src,dst) in enumerate(rules):a[y][0]=b[y][0]=src;a[y][1]=b[y][1]=dst
    # Compile the sequential mapping once; populate isolated canvas dots.
    mapping={c:c for c in colours}
    for src,dst in rules:
        mapping={c:(dst if v==src else v) for c,v in mapping.items()}
    positions=[(y,x) for y in range(0,h,2) for x in range(4,w,2)]
    rng.shuffle(positions)
    n=rng.randint(min(4,len(positions)),len(positions))
    for i,(y,x) in enumerate(positions[:n]):
        c=colours[i%len(colours)] if i<len(colours) else rng.choice(colours)
        a[y][x]=c;b[y][x]=mapping[c]
    return {'input':a,'output':b}

def erase_superset_rooms(rng,height=None,width=None):
    h=height or rng.randint(12,30);w=width or rng.randint(12,30)
    if not(12<=h<=30 and 12<=w<=30):raise ValueError('Size outside constructor contract')
    a=blank(h,w,7);b=blank(h,w,7);colours=[1,2,4,5,6,8,9]
    legend=rng.sample(colours,rng.randint(2,4))
    for y in range(4):a[y][3]=b[y][3]=3
    for x in range(4):a[3][x]=b[3][x]=3
    for i,c in enumerate(legend):a[i//3][i%3]=b[i//3][i%3]=c
    nr=2 if h<21 else rng.choice([2,3]);nc=2 if w<20 else rng.choice([2,3])
    rh=(h-5-(nr-1))//nr;rw=(w-(nc-1))//nc
    for j in range(nr*nc):
        y0=5+(j//nc)*(rh+1);x0=(j%nc)*(rw+1)
        erase=j%2==0
        selected=set(legend) if erase else set(legend[:-1])
        extras=[c for c in colours if c not in legend]
        selected.update(rng.sample(extras,rng.randint(0,len(extras))))
        room=blank(rh,rw)
        for idx,c in zip(rng.sample(range(rh*rw),len(selected)),sorted(selected)):room[idx//rw][idx%rw]=c
        for y in range(rh):
            for x in range(rw):
                a[y0+y][x0+x]=room[y][x]
                b[y0+y][x0+x]=7 if erase else room[y][x]
    return {'input':a,'output':b}

def quadrant_program(rng,height=None,width=None):
    n=(height//2) if height is not None else rng.randint(3,15)
    m=(width//2) if width is not None else n
    if not(3<=n<=15 and 3<=m<=15):raise ValueError('Quadrants must fit 30')
    H=rng.randint(2,min(30,n*m));W=rng.randint(2,min(30,n*m))
    a=blank(2*n,2*m);colours=rng.sample(range(1,10),6)
    for i in rng.sample(range(n*m),H):a[i//m][i%m]=colours[0]
    for i in rng.sample(range(n*m),W):a[i//m][m+i%m]=colours[1]
    fill=[[colours[2+(y//max(1,n//3))%2] for x in range(m)] for y in range(n)]
    motif=[[rng.choice([0,0,colours[4],colours[5]]) for _ in range(m)] for _ in range(n)]
    for y in range(n):
        for x in range(m):a[n+y][x]=fill[y][x];a[n+y][m+x]=motif[y][x]
    b=[[motif[y%n][x%m] or fill[(y*n)//H][(x*m)//W] for x in range(W)] for y in range(H)]
    return {'input':a,'output':b}

GENERATORS={'0692e18c':inverse_tiles,'00576224':mirrored_tiles,'e4888269':sequential_legend,'d59b0160':erase_superset_rooms,'f931b4a8':quadrant_program}

def generate(tid,seed=0,**kwargs):return GENERATORS[tid](random.Random(seed),**kwargs)
