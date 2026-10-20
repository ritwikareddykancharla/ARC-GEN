TEMPLATE = '''
REGION = @REGION@
MARK = @MARK@
TIES = ((), (1,), (2,), (1,2), (2,1))


def _options(grid):
    g = [list(row) for row in grid]
    h,w = len(g),len(g[0])
    if any(len(row) != w for row in g):
        raise ValueError('Expected rectangular grid')
    candidates = [[],[]]
    corners = ((0,0),(0,w-1),(h-1,0),(h-1,w-1))
    for slope in (1,-1):
        for r0 in range(h):
            for c0 in range(w):
                if 0 <= r0-1 < h and 0 <= c0-slope < w:
                    continue
                cells=[];runs=[];run=[];r,c=r0,c0
                while 0 <= r < h and 0 <= c < w:
                    if g[r][c] == REGION:
                        cells.append((r,c));run.append((r,c))
                    elif run:
                        runs.append(run);run=[]
                    r,c=r+1,c+slope
                if run:runs.append(run)
                offset=abs((2*r0-h+1)-slope*(2*c0-w+1))
                for mode,groups in enumerate(([cells] if cells else [],runs)):
                    for selected in groups:
                        corner=min(max(abs(r-y),abs(c-x)) for r,c in (selected[0],selected[-1]) for y,x in corners)
                        candidates[mode].append((frozenset(selected),(len(selected),-offset,-corner)))
    if not candidates[0]:
        raise ValueError('No region cells on any diagonal')
    options=[]
    for group in candidates:
        for tie in TIES:
            score=lambda item: (item[1][0],)+tuple(item[1][i] for i in tie)
            best=max(map(score,group))
            options.append({cells for cells,features in group if (features[0],)+tuple(features[i] for i in tie)==best})
    return options


def _changes(grid,output):
    if len(output)!=len(grid) or any(len(a)!=len(b) for a,b in zip(grid,output)):
        raise ValueError('Demonstration output must keep the input shape')
    changed=set()
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if output[r][c]!=v:
                if v!=REGION or output[r][c]!=MARK:
                    raise ValueError('Only region cells may become the marker colour')
                changed.add((r,c))
    return frozenset(changed)


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(range(10))
    for pair in demonstrations:
        expected=_changes(pair['input'],pair['output'])
        options=_options(pair['input'])
        alive &= {i for i,choices in enumerate(options) if choices=={expected}}
    if not alive:raise ValueError('No diagonal rule uniquely reproduces all demonstrations')
    options=_options(grid)
    choices=set().union(*(options[i] for i in alive))
    if len(choices)!=1:raise ValueError('Demonstrations leave diagonal mechanism or tie unresolved')
    out=[list(row) for row in grid]
    for r,c in next(iter(choices)):out[r][c]=MARK
    return out
'''


def build_program(d4,palette):
    return TEMPLATE.replace('@REGION@',repr(int(palette[0]))).replace('@MARK@',repr(int(palette[8])))
