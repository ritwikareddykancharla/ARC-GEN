"""Independent literal repainting check for consecutive-crossing histories."""
from itertools import product,permutations
from .colour_evidence import MissingColourEvidence


def simulate_histories(grid,palette,require_chain=True):
    bg=palette[7];h=len(grid);w=len(grid[0]);by_colour={}
    if any(len(row)!=w for row in grid):raise ValueError('Ragged input')
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value!=bg:by_colour.setdefault(value,set()).add((r,c))
    if not by_colour:raise ValueError('No lines')
    colours=list(by_colour);choices=[]
    coordinates=(lambda r,c:r,lambda r,c:c,lambda r,c:r-c,lambda r,c:r+c)
    for colour in colours:
        candidates=[]
        for coordinate in coordinates:
            values={coordinate(r,c) for r,c in by_colour[colour]}
            if len(values)!=1:continue
            value=next(iter(values));cells=frozenset((r,c) for r in range(h) for c in range(w) if coordinate(r,c)==value)
            if any(grid[r][c]==bg for r,c in cells):continue
            if cells not in candidates:candidates.append(cells)
        if not candidates:raise ValueError('Nonlinear object')
        choices.append(candidates)
    answers=set();expected=tuple(tuple(row) for row in grid)
    for shapes in product(*choices):
        masks=dict(zip(colours,shapes))
        for order in permutations(colours):
            if require_chain and any(len(masks[a]&masks[b])!=1 for a,b in zip(order,order[1:])):continue
            painted=[[bg]*w for _ in range(h)];last=None;good=True
            for colour in order:
                if require_chain and last is not None and sum(painted[r][c]==last for r,c in masks[colour])!=1:good=False;break
                for r,c in masks[colour]:painted[r][c]=colour
                last=colour
            if good and tuple(tuple(row) for row in painted)==expected:answers.add(order)
    if not answers:raise ValueError('No consistent painting histories')
    return answers


def _layout(order,column,reverse):
    order=order[::-1] if reverse else order
    return tuple((c,) for c in order) if column else (tuple(order),)


def require_chained_lines_evidence(demonstrations,queries,palette):
    try:
        if not demonstrations:raise ValueError('Demonstrations required')
        alive={(a,b) for a in (False,True) for b in (False,True)}
        for p in demonstrations:
            histories=simulate_histories(p['input'],palette);expected=tuple(tuple(row) for row in p['output'])
            alive={mode for mode in alive if {_layout(order,*mode) for order in histories}=={expected}}
        if not alive:raise ValueError('Inconsistent demonstration convention')
        for q in queries:
            answers={_layout(order,*mode) for order in simulate_histories(q['input'],palette) for mode in alive}
            if len(answers)!=1:raise ValueError('Ambiguous chain history')
    except (ValueError,TypeError,IndexError) as exc:raise MissingColourEvidence('22425bda: chained painting order or output convention unresolved') from exc
