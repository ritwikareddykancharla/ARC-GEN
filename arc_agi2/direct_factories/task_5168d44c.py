TEMPLATE = '''
BG = __BG__
FRAME = __FRAME__
DOT = __DOT__


def _scene(grid):
    h,w=len(grid),len(grid[0])
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==FRAME]
    dots=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==DOT]
    if not cells or len(dots)<2:raise ValueError('Missing frame or dotted line')
    r0,r1=min(r for r,c in cells),max(r for r,c in cells)
    c0,c1=min(c for r,c in cells),max(c for r,c in cells)
    if r1-r0!=2 or c1-c0!=2:raise ValueError('Expected 3x3 frame')
    cy,cx=r0+1,c0+1
    axis=1 if all(r==cy for r,c in dots) else 0 if all(c==cx for r,c in dots) else None
    if axis is None:raise ValueError('Expected straight dotted line')
    center=(cy,cx);positions=sorted(p[axis] for p in dots)
    if center[axis] not in positions or any(b-a!=2 for a,b in zip(positions,positions[1:])):raise ValueError('Invalid dotted line')
    expected={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-{center}
    if set(cells)!=expected:raise ValueError('Invalid frame')
    if any(v not in (BG,FRAME,DOT) for row in grid for v in row):raise ValueError('Unknown colour')
    left=sum(p<center[axis] for p in positions);right=sum(p>center[axis] for p in positions)
    return cells,center,axis,(right>left)-(right<left)


def _predict(grid,rule):
    cells,center,axis,majority=_scene(grid)
    mode,vertical,horizontal=rule
    sign=(vertical,horizontal)[axis]
    if mode and majority:sign=majority
    delta=[0,0];delta[axis]=2*sign
    h,w=len(grid),len(grid[0]);out=[row[:] for row in grid]
    for r,c in cells:out[r][c]=BG
    for r,c in cells:
        y,x=r+delta[0],c+delta[1]
        if not(0<=y<h and 0<=x<w):raise ValueError('Moved frame outside grid')
        out[y][x]=FRAME
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    rules=[(m,v,h) for m in (0,1) for v in (-1,1) for h in (-1,1)]
    observed={}
    for p in demonstrations:
        _,before,axis,_=_scene(p['input'])
        _,after,outaxis,_=_scene(p['output'])
        delta=after[axis]-before[axis]
        if axis!=outaxis or before[1-axis]!=after[1-axis] or delta not in (-2,2):raise ValueError('Invalid demonstrated motion')
        if axis in observed and observed[axis]!=delta//2:raise ValueError('Conflicting demonstrated directions')
        observed[axis]=delta//2
    rules=[r for r in rules if all(r[1+a]==s for a,s in observed.items())]
    alive=[]
    for rule in rules:
        try:
            if all(_predict(p['input'],rule)==p['output'] for p in demonstrations):alive.append(rule)
        except ValueError:pass
    if not alive:raise ValueError('No demonstrated motion rule')
    predictions=[]
    for rule in alive:
        try:predictions.append(_predict(grid,rule))
        except ValueError:raise ValueError('Unresolved motion at boundary')
    if any(p!=predictions[0] for p in predictions[1:]):raise ValueError('Unresolved motion direction')
    return predictions[0]
'''


def build_program(d4,palette):
    source=TEMPLATE
    for key,index in (("__BG__",0),("__FRAME__",2),("__DOT__",3)):
        source=source.replace(key,str(int(palette[index])))
    return source
