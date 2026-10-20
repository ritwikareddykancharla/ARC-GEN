"""Demo-oriented obstacle following with simultaneous, immutable-input paths."""
TEMPLATE='''import numpy as np

BG, PATH, EXIT, TURN, MARK, WALL, HIT = __COLOURS__
DIRECTIONS=((-1,0),(1,0),(0,-1),(0,1))
FRAMES=tuple((u,v) for u in DIRECTIONS for v in DIRECTIONS if u[0]*v[0]+u[1]*v[1]==0)


def _predict(grid,up,side):
    g=np.asarray(grid,dtype=int);h,w=g.shape
    inside=lambda p:0<=p[0]<h and 0<=p[1]<w
    plus=lambda p,d:(p[0]+d[0],p[1]+d[1])
    ink=lambda p:int(g[p])
    markers=[tuple(map(int,p)) for p in np.argwhere(g==MARK)]
    if not markers or any(inside((p[0]-up[0],p[1]-up[1])) for p in markers):raise ValueError('Markers must start at incoming edge')
    writes={}
    for marker in markers:
        local={};p=plus(marker,up)
        if not inside(p) or ink(p)!=BG:raise ValueError('Blocked start')
        while inside(plus(p,up)):
            ahead=plus(p,up)
            if ink(p)!=BG:raise ValueError('Path intersects input ink')
            if ink(ahead)==BG:local[p]=PATH
            elif ink(ahead)==WALL:
                q=plus(p,side)
                if not inside(q):raise ValueError('Side outside grid')
                if ink(q)==WALL:break
                if ink(q)!=BG:raise ValueError('Blocked turn')
                local[p]=TURN;local[ahead]=HIT
                while True:
                    p=plus(p,side)
                    if not inside(p) or ink(p)!=BG:raise ValueError('Blocked lateral path')
                    ahead=plus(p,up)
                    if ink(ahead)==BG:break
                    if ink(ahead)!=WALL:raise ValueError('Invalid obstacle')
                    local[p]=PATH
                local[p]=EXIT
            else:raise ValueError('Invalid ahead cell')
            p=plus(p,up)
        if ink(p)!=BG:raise ValueError('Blocked endpoint')
        if (p[0]-marker[0])*side[0]+(p[1]-marker[1])*side[1]==0:raise ValueError('No lateral movement')
        local[p]=MARK
        if set(local)&set(writes):raise ValueError('Intersecting paths')
        writes.update(local)
    out=g.copy()
    for p,colour in writes.items():out[p]=colour
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=list(FRAMES)
    for pair in demonstrations:
        good=[]
        for u,v in alive:
            try:
                if np.array_equal(_predict(pair['input'],u,v),np.asarray(pair['output'])):good.append((u,v))
            except (ValueError,IndexError):pass
        alive=good
    if not alive:raise ValueError('No demonstrated path orientation')
    predictions=[]
    for u,v in alive:
        try:predictions.append(_predict(grid,u,v))
        except (ValueError,IndexError):continue
    if not predictions or any(not np.array_equal(p,predictions[0]) for p in predictions[1:]):raise ValueError('Ambiguous path orientation')
    return predictions[0].tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__COLOURS__',repr(tuple(int(palette[c]) for c in (0,2,3,4,6,7,8))))
