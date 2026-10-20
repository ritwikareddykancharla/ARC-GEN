"""Reconstruct the colour stack after learning its orientation from demos."""
TEMPLATE = '''import numpy as np

BG = __BG__


def _legend(g):
    h,w=g.shape;seen=set();candidates=[]
    for r in range(h):
        for c in range(w):
            if int(g[r,c])==BG or (r,c) in seen:continue
            cells={(r,c)};seen.add((r,c));todo=[(r,c)]
            while todo:
                y,x=todo.pop()
                for a,b in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0<=a<h and 0<=b<w and int(g[a,b])!=BG and (a,b) not in seen:
                        seen.add((a,b));cells.add((a,b));todo.append((a,b))
            y0,x0=min(y for y,x in cells),min(x for y,x in cells)
            y1,x1=max(y for y,x in cells),max(x for y,x in cells)
            if len(cells)!=(y1-y0+1)*(x1-x0+1):continue
            rect=g[y0:y1+1,x0:x1+1]
            for axis in (0,1):
                stripes=rect if axis==0 else rect.T
                colours=[int(v) for v in stripes[0]]
                if min(stripes.shape)<2 or len(set(colours))!=len(colours):continue
                if not np.all(stripes==stripes[0]):continue
                rest={int(g[y,x]) for y in range(h) for x in range(w) if (y,x) not in cells and int(g[y,x])!=BG}
                if not rest or not rest<set(colours):continue
                ids=sorted(colours.index(v) for v in rest)
                if ids!=list(range(ids[0],ids[-1]+1)):continue
                candidates.append((axis,colours,cells))
    if len(candidates)!=1:raise ValueError('Expected one isolated complete legend')
    return candidates[0]


def _predict(grid,direction):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    axis,colours,legend=_legend(g);shapes={}
    for y,x in np.argwhere(g!=BG):
        y,x=int(y),int(x)
        if (y,x) not in legend:shapes.setdefault(int(g[y,x]),set()).add((y,x))
    ids=sorted(colours.index(c) for c in shapes);first=ids[0];anchor=shapes[colours[first]]
    bounds=[p[axis] for p in anchor];period=max(bounds)-min(bounds)+1
    for j in ids:
        shift=(j-first)*period*direction
        moved={(y+(shift if axis==0 else 0),x+(shift if axis==1 else 0)) for y,x in anchor}
        if moved!=shapes[colours[j]]:raise ValueError('Copies disagree with stack rule')
    out=np.full(g.shape,BG,dtype=int)
    for j,colour in enumerate(colours):
        shift=(j-first)*period*direction
        for y,x in anchor:
            y+=shift if axis==0 else 0;x+=shift if axis==1 else 0
            if not(0<=y<g.shape[0] and 0<=x<g.shape[1]):raise ValueError('Stack outside grid')
            out[y,x]=colour
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive={-1,1}
    for pair in demonstrations:
        good=set()
        for direction in alive:
            try:
                if np.array_equal(_predict(pair['input'],direction),np.asarray(pair['output'])):good.add(direction)
            except ValueError:pass
        alive=good
    if not alive:raise ValueError('No demonstrated stack direction')
    predictions=[]
    for direction in alive:
        try:predictions.append(_predict(grid,direction))
        except ValueError:continue
    if not predictions or any(not np.array_equal(p,predictions[0]) for p in predictions[1:]):raise ValueError('Ambiguous stack direction')
    return predictions[0].tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0])))
