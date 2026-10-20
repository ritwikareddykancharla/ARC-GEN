"""Assemble uniquely determined corner frames, including clipped off-grid centres."""
PROGRAM = '''
def _ring(size):
    end=size-1
    return [(y,x,min(y,end-y) if x in (0,end) else min(x,end-x))
            for y in range(size) for x in range(size) if y in (0,end) or x in (0,end)]


def _hypotheses(g,c,size,cells):
    h,w=len(g),len(g[0]);k=(size-1)//2
    y0,y1=min(y for y,x in cells),max(y for y,x in cells)
    x0,x1=min(x for y,x in cells),max(x for y,x in cells)
    if y1-y0+1>size or x1-x0+1>size:return set()
    allowed={1} if k==0 else {2} if k==1 else set(range(2,k+1))
    ring=_ring(size);out=set()
    for top in range(y1-size+1,y0+1):
        for left in range(x1-size+1,x0+1):
            counts=[0]*(k+1);bad=[False]*(k+1)
            for y,x,t in ring:
                yy,xx=top+y,left+x
                if 0<=yy<h and 0<=xx<w:
                    if g[yy][xx]==c:counts[t]+=1
                    else:bad[t]=True
            total=0
            for length in range(1,k+2):
                if bad[length-1]:break
                total+=counts[length-1]
                if total!=len(cells) or length not in allowed:continue
                quadrants=0
                for y in (0,size-1):
                    for x in (0,size-1):
                        sy=1 if y==0 else -1;sx=1 if x==0 else -1
                        if any(0<=top+yy<h and 0<=left+xx<w for j in range(length)
                               for yy,xx in ((y,x+sx*j),(y+sy*j,x))):quadrants+=1
                if k and quadrants<2:continue
                out.add((size,length))
    return out


def _recover(grid):
    g=[list(row) for row in grid]
    if not g or not g[0] or any(len(row)!=len(g[0]) for row in g):raise ValueError('Invalid grid')
    counts={}
    for row in g:
        for c in row:counts[c]=counts.get(c,0)+1
    backgrounds=[c for c in counts if counts[c]==max(counts.values())]
    if len(backgrounds)!=1:raise ValueError('Background is not uniquely identifiable')
    bg=backgrounds[0];colours=[c for c in counts if c!=bg];m=len(colours)
    if not m:raise ValueError('No visible corner frames')
    cells={c:[(y,x) for y,row in enumerate(g) for x,v in enumerate(row) if v==c] for c in colours}
    hyp={c:set().union(*(_hypotheses(g,c,s,cells[c]) for s in range(1,2*m+2,2))) for c in colours}
    answers=set()
    for base in (1,3):
        sizes=set(range(base,base+2*m,2));side=max(sizes)
        def visit(i,used,mapping):
            if i==m:
                out=[[bg]*side for _ in range(side)]
                for colour,(size,length) in mapping.items():
                    offset=(side-size)//2
                    for y,x,t in _ring(size):
                        if t<length:out[offset+y][offset+x]=colour
                answers.add(tuple(tuple(row) for row in out));return
            c=colours[i]
            for size,length in hyp[c]:
                if size not in sizes or size in used:continue
                visit(i+1,used|{size},mapping|{c:(size,length)})
        visit(0,set(),{})
    if len(answers)!=1:raise ValueError('Clipped frames do not determine a unique assembly')
    return [list(row) for row in next(iter(answers))]


def solve(demonstrations,grid):
    for p in demonstrations:
        if _recover(p['input'])!=p['output']:raise ValueError('Frame mechanism contradicts demonstration')
    return _recover(grid)
'''


def build_program(d4,palette):
    return PROGRAM
