"""Recover chained line painting histories, learning output layout from demos."""
TEMPLATE = '''import itertools
import numpy as np
BG = __BG__


def _orders(grid):
    g=np.asarray(grid,dtype=int)
    if g.ndim!=2 or not g.size:raise ValueError('Expected rectangular grid')
    colours=[int(c) for c in np.unique(g) if c!=BG]
    if not colours:raise ValueError('No painted lines')
    yy,xx=np.indices(g.shape);families=(yy,xx,yy-xx,yy+xx);candidates=[]
    for c in colours:
        choices=[]
        for coord in families:
            vals=np.unique(coord[g==c])
            if len(vals)!=1:continue
            mask=coord==vals[0]
            if np.any(mask&(g==BG)):continue
            if not any(np.array_equal(mask,a) for a in choices):choices.append(mask)
        if not choices:raise ValueError('A colour does not form a full straight line')
        candidates.append(choices)
    orders=set()
    for combo in itertools.product(*candidates):
        if not np.array_equal(np.logical_or.reduce(combo),g!=BG):continue
        masks=dict(zip(colours,combo));below={c:set() for c in colours}
        cross={}
        for a in colours:
            for b in colours:
                if a==b:continue
                if np.any(masks[a]&(g==b)):below[b].add(a)
                cross[a,b]=int(np.count_nonzero(masks[a]&masks[b]))==1
        def visit(order,used):
            if len(order)==len(colours):orders.add(tuple(order));return
            for c in colours:
                if c in used or not below[c]<=used:continue
                if order and not cross[order[-1],c]:continue
                visit(order+[c],used|{c})
        visit([],set())
    if not orders:raise ValueError('No valid chained painting history')
    return orders


def _render(order,mode):
    column,reverse=mode
    values=list(order[::-1] if reverse else order)
    return tuple((c,) for c in values) if column else (tuple(values),)


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required to determine output layout/order')
    alive={(column,reverse) for column in (False,True) for reverse in (False,True)}
    for p in demonstrations:
        histories=_orders(p['input']);expected=tuple(tuple(row) for row in p['output'])
        alive={mode for mode in alive if {_render(order,mode) for order in histories}=={expected}}
    if not alive:raise ValueError('No common demonstrated output convention')
    answers={_render(order,mode) for order in _orders(grid) for mode in alive}
    if len(answers)!=1:raise ValueError('Residual chained-history ambiguity')
    return [list(row) for row in next(iter(answers))]
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[7])))
