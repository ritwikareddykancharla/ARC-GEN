TEMPLATE = '''import numpy as np

BG = __BG__
RULES = ('gap','aspect','side')


def _parse(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    colours=[int(c) for c in np.unique(g) if c!=BG]
    if len(colours)!=2:raise ValueError('Expected two nested colours')
    boxes=[]
    for c in colours:
        ys,xs=np.where(g==c)
        b=(int(ys.min()),int(xs.min()),int(ys.max()),int(xs.max()))
        boxes.append(((b[2]-b[0]+1)*(b[3]-b[1]+1),b,c))
    boxes.sort(reverse=True)
    _,outer,frame=boxes[0];_,inner,ink=boxes[1]
    y0,x0,y1,x1=outer;a,b,c,d=inner
    gaps=(a-y0,b-x0,y1-c,x1-d)
    if min(gaps)<=0 or len(set(gaps))!=1:raise ValueError('Expected uniform nested frame')
    expected=np.full(g.shape,BG,dtype=int)
    expected[y0:y1+1,x0:x1+1]=frame;expected[a:c+1,b:d+1]=ink
    if not np.array_equal(g,expected):raise ValueError('Invalid nested rectangles')
    return g,outer,inner,ink


def _predict(grid,rule):
    g,outer,inner,ink=_parse(grid);h,w=g.shape
    y0,x0,y1,x1=outer
    short,long=sorted((inner[2]-inner[0]+1,inner[3]-inner[1]+1))
    if rule=='gap':thick=min(short,y0,x0,h-1-y1,w-1-x1)
    elif rule=='aspect':thick=max(0,2*short-long)
    else:thick=short
    out=g.copy()
    if thick:
        out[max(0,y0-thick):min(h,y1+thick+1),max(0,x0-thick):min(w,x1+thick+1)]=ink
        out[y0:y1+1,x0:x1+1]=g[y0:y1+1,x0:x1+1]
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(RULES)
    for p in demonstrations:
        expected=np.asarray(p['output'],dtype=int)
        alive &= {r for r in alive if np.array_equal(_predict(p['input'],r),expected)}
    if not alive:raise ValueError('No demonstrated band rule')
    predictions=[_predict(grid,r) for r in sorted(alive)]
    if any(not np.array_equal(p,predictions[0]) for p in predictions[1:]):raise ValueError('Unresolved band thickness')
    return predictions[0].tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0])))
