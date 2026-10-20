TEMPLATE = '''import numpy as np

BG = __BG__


def _options(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    options=[set(),set(),set()]
    for colour in np.unique(g):
        if colour==BG:continue
        ys,xs=np.where(g==colour)
        crop=g[ys.min():ys.max()+1,xs.min():xs.max()+1]
        mask=crop==colour
        answer=tuple(tuple(int(v) for v in row) for row in np.where(mask,colour,BG))
        for i,other in enumerate((mask[:,::-1],mask[::-1,:],mask[::-1,::-1])):
            if np.array_equal(mask,other):options[i].add(answer)
    return options


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive=set(range(3))
    for p in demonstrations:
        expected=tuple(tuple(row) for row in p['output'])
        options=_options(p['input'])
        alive &= {i for i,answers in enumerate(options) if answers=={expected}}
    if not alive:raise ValueError('No uniquely demonstrated symmetry rule')
    options=_options(grid)
    if any(not options[i] for i in alive):raise ValueError('Unresolved symmetry: no matching object')
    answers=set().union(*(options[i] for i in alive))
    if len(answers)!=1:raise ValueError('Unresolved symmetry or multiple matching objects')
    return [list(row) for row in next(iter(answers))]
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0])))
