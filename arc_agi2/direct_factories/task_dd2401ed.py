TEMPLATE = '''BG, LEFT, RIGHT, WALL = __COLOURS__


def _features(grid):
    h,w=len(grid),len(grid[0]);options=[]
    if any(v not in (BG,LEFT,RIGHT,WALL) for row in grid for v in row):raise ValueError('Unexpected colour')
    for vertical in (False,True):
        length=w if vertical else h
        def value(t,u):return grid[u][t] if vertical else grid[t][u]
        cross=h if vertical else w
        walls=[t for t in range(length) if all(value(t,u)==WALL for u in range(cross))]
        if len(walls)!=1:continue
        pos=walls[0]
        if sum(row.count(WALL) for row in grid)!=cross:continue
        for reverse in (False,True):
            old=length-1-pos if reverse else pos;new=2*old+1
            if not 0<old<new<length:continue
            ones=twos=0;valid=True
            for t in range(length):
                distance=length-1-t if reverse else t
                for u in range(cross):
                    v=value(t,u)
                    if distance==old:continue
                    if v==LEFT:ones+=1;valid &= distance<old
                    if v==RIGHT:twos+=1;valid &= distance>old
                    if distance==new and v!=BG:valid=False
            if valid and ones and twos:options.append((vertical,reverse,pos,length-1-new if reverse else new,ones))
    if len(options)!=1:raise ValueError('No unique oriented cursor')
    return options[0]


def _predict(grid,features,mode):
    vertical,reverse,old,new,ones=features;out=[row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            t=c if vertical else r
            if t==old:out[r][c]=BG
            if t==new:out[r][c]=WALL
            swept=t>new if reverse else t<new
            if swept and grid[r][c]==RIGHT and (mode=='always' or ones%2):out[r][c]=LEFT
    return out


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    modes=['always','odd']
    for pair in demonstrations:
        f=_features(pair['input'])
        modes=[m for m in modes if _predict(pair['input'],f,m)==pair['output']]
    if not modes:raise ValueError('No demonstrated recolouring mechanism')
    features=_features(grid);answers={tuple(map(tuple,_predict(grid,features,m))) for m in modes}
    if len(answers)!=1:raise ValueError('Recolouring mechanism unresolved')
    return list(map(list,next(iter(answers))))
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__COLOURS__',repr(tuple(int(palette[c]) for c in (0,1,2,5))))
