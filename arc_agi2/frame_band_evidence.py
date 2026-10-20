"""Independent coordinate renderer for demonstration-conditioned frame bands."""
from .colour_evidence import MissingColourEvidence


def band_options(grid,palette):
    bg=palette[0];colours=set(v for row in grid for v in row)-{bg}
    if len(colours)!=2:raise ValueError('Expected two nested colours')
    boxes=[]
    for colour in colours:
        cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==colour]
        top,bottom=min(r for r,c in cells),max(r for r,c in cells)
        left,right=min(c for r,c in cells),max(c for r,c in cells)
        boxes.append(((bottom-top+1)*(right-left+1),(top,left,bottom,right),colour))
    boxes.sort(reverse=True);_,outer,frame=boxes[0];_,inner,ink=boxes[1]
    top,left,bottom,right=outer;a,b,c,d=inner
    gaps=(a-top,b-left,bottom-c,right-d)
    if min(gaps)<=0 or len(set(gaps))!=1:raise ValueError('Nonuniform nested frame')
    for r,row in enumerate(grid):
        for col,v in enumerate(row):
            expected=ink if a<=r<=c and b<=col<=d else frame if top<=r<=bottom and left<=col<=right else bg
            if v!=expected:raise ValueError('Invalid nested geometry')
    short,long=sorted((c-a+1,d-b+1));h,w=len(grid),len(grid[0])
    thicknesses=(min(short,top,left,h-1-bottom,w-1-right),max(0,2*short-long),short)
    outputs=[]
    for thick in thicknesses:
        outputs.append([[ink if top-thick<=r<=bottom+thick and left-thick<=col<=right+thick and not(top<=r<=bottom and left<=col<=right) else v
                         for col,v in enumerate(row)] for r,row in enumerate(grid)])
    return outputs


def require_band_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('3a301edc: demonstrations required')
    alive=set(range(3))
    try:
        for p in demonstrations:alive &= {i for i,out in enumerate(band_options(p['input'],palette)) if out==p['output']}
    except (ValueError,TypeError,IndexError) as e:raise MissingColourEvidence('3a301edc: invalid nested rectangles') from e
    if not alive:raise MissingColourEvidence('3a301edc: no demonstrated band rule')
    for q in queries:
        try:options=band_options(q['input'],palette)
        except (ValueError,TypeError,IndexError) as e:raise MissingColourEvidence('3a301edc: invalid query frame') from e
        answers={tuple(tuple(row) for row in options[i]) for i in alive}
        if len(answers)!=1:raise MissingColourEvidence('3a301edc: unresolved band thickness')
