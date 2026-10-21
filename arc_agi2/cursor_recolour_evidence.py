"""Oriented cursor motion from full wall line and source-colour side."""
from arc_agi2.colour_evidence import MissingColourEvidence


def outputs(g,palette):
    bg,blue,red,wall=(palette[c] for c in (0,1,2,5));h,w=len(g),len(g[0])
    walls={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==wall}
    blues={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==blue}
    reds={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==red}
    if not walls or not blues or not reds:raise ValueError('Missing role')
    rows={r for r,c in walls};cols={c for r,c in walls}
    if len(cols)==1 and rows==set(range(h)):axis=1;pos=next(iter(cols));length=w
    elif len(rows)==1 and cols==set(range(w)):axis=0;pos=next(iter(rows));length=h
    else:raise ValueError('Not one full wall')
    if all(p[axis]<pos for p in blues):direction=1;distance=pos
    elif all(p[axis]>pos for p in blues):direction=-1;distance=length-1-pos
    else:raise ValueError('Blue straddles wall')
    if not all((p[axis]-pos)*direction>0 for p in reds):raise ValueError('Red on source side')
    new=pos+direction*(distance+1)
    if not 0<=new<length:raise ValueError('Cursor leaves grid')
    if any(g[r][c]!=bg for r in range(h) for c in range(w) if (r,c)[axis]==new):raise ValueError('Destination blocked')
    if any(v not in (bg,blue,red,wall) for row in g for v in row):raise ValueError('Unknown colour')
    answers={m:[row[:] for row in g] for m in ('always','odd')}
    for mode,out in answers.items():
        for r,c in walls:out[r][c]=bg
        for r in range(h):
            for c in range(w):
                if (r,c)[axis]==new:out[r][c]=wall
        if mode=='always' or len(blues)%2:
            for r,c in reds:
                if ((r,c)[axis]-new)*direction<0:out[r][c]=blue
    return answers


def require_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('dd2401ed: missing demonstrations')
    try:
        alive={'always','odd'}
        for pair in demonstrations:
            possible=outputs(pair['input'],palette);alive={m for m in alive if possible[m]==pair['output']}
        if not alive:raise ValueError('No demonstrated recolouring hypothesis')
        for q in queries:
            possible=outputs(q['input'],palette)
            if len({tuple(map(tuple,possible[m])) for m in alive})!=1:raise ValueError('Recolouring unresolved')
    except ValueError as e:raise MissingColourEvidence('dd2401ed: '+str(e)) from e
