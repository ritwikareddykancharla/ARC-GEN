"""Coordinate-set verification of framed holes and their aligned gallery shapes."""
from .colour_evidence import MissingColourEvidence


def gallery_answers(grid, palette):
    bg=palette[0];h,w=len(grid),len(grid[0]);answers=set()
    colours={v for row in grid for v in row}-{bg}
    for frame in colours:
        fc={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==frame}
        y0,y1=min(r for r,c in fc),max(r for r,c in fc)
        x0,x1=min(c for r,c in fc),max(c for r,c in fc)
        bh,bw=y1-y0+1,x1-x0+1
        perimeter={(r,c) for r in range(y0,y1+1) for c in range(x0,x1+1) if r in (y0,y1) or c in (x0,x1)}
        if min(bh,bw)<3 or not perimeter<=fc:continue
        if any(grid[r][c] not in (bg,frame) for r in range(y0,y1+1) for c in range(x0,x1+1)):continue
        gallery={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (bg,frame)}
        if not gallery:continue
        sides=[]
        if all(c>x1 for r,c in gallery):sides.append((0,bw,0))
        if all(c<x0 for r,c in gallery):sides.append((0,-bw,0))
        if all(r>y1 for r,c in gallery):sides.append((bh,0,1))
        if all(r<y0 for r,c in gallery):sides.append((-bh,0,1))
        if len(sides)!=1:continue
        dy,dx,axis=sides[0]
        symbols={colour:{(r-y0-dy,c-x0-dx) for r,c in gallery if grid[r][c]==colour} for colour in colours-{frame}}
        holes={(r-y0,c-x0) for r in range(y0,y1+1) for c in range(x0,x1+1) if grid[r][c]==bg}
        if not holes:continue
        out=[row[x0:x1+1] for row in grid[y0:y1+1]];valid=True
        while holes:
            seed=holes.pop();region={seed};stack=[seed]
            while stack:
                r,c=stack.pop()
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        p=r+dr,c+dc
                        if p in holes:holes.remove(p);region.add(p);stack.append(p)
            choices=set()
            for colour,cells in symbols.items():
                shift=min(p[axis] for p in region)-min(p[axis] for p in cells)
                translated={(r+shift,c) if axis==0 else (r,c+shift) for r,c in cells}
                if translated==region:choices.add(colour)
            if len(choices)!=1:valid=False;break
            for r,c in region:out[r][c]=next(iter(choices))
        if valid:answers.add(tuple(map(tuple,out)))
    return answers


def require_gallery_evidence(demonstrations, queries, palette):
    if not demonstrations:raise MissingColourEvidence('93b4f4b3: demonstrations required')
    for pair in demonstrations:
        expected=tuple(map(tuple,pair['output']))
        if gallery_answers(pair['input'],palette)!={expected}:
            raise MissingColourEvidence('93b4f4b3: demonstrations violate unique aligned gallery matching')
    for query in queries:
        if len(gallery_answers(query['input'],palette))!=1:
            raise MissingColourEvidence('93b4f4b3: query has no unique aligned gallery solution')
