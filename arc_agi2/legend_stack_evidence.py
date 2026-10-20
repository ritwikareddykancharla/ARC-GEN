"""Independent scan-line legend identification and cell-wise stack verification."""
from .colour_evidence import MissingColourEvidence


def legend_stack_options(grid,palette):
    bg=palette[0];h,w=len(grid),len(grid[0]);candidates=[]
    # Look for maximal equal scan lines with distinct ink along the line.
    for axis in (0,1):
        n,m=(h,w) if axis==0 else (w,h)
        at=lambda r,c:grid[r][c] if axis==0 else grid[c][r]
        for r in range(n):
            c=0
            while c<m:
                if at(r,c)==bg:c+=1;continue
                left=c
                while c<m and at(r,c)!=bg:c+=1
                colours=[at(r,k) for k in range(left,c)]
                if len(colours)<2 or len(set(colours))!=len(colours):continue
                if r and [at(r-1,k) for k in range(left,c)]==colours:continue
                bottom=r+1
                while bottom<n and [at(bottom,k) for k in range(left,c)]==colours:bottom+=1
                if bottom-r<2:continue
                if any(at(y,x)!=bg for y in range(max(0,r-1),min(n,bottom+1)) for x in range(max(0,left-1),min(m,c+1)) if not(r<=y<bottom and left<=x<c)):continue
                coords={(y,x) if axis==0 else (x,y) for y in range(r,bottom) for x in range(left,c)}
                rest={grid[y][x] for y in range(h) for x in range(w) if (y,x) not in coords and grid[y][x]!=bg}
                if not rest or not rest<set(colours):continue
                indices=sorted(colours.index(v) for v in rest)
                if indices!=list(range(indices[0],indices[-1]+1)):continue
                candidates.append((axis,colours,coords))
    if len(candidates)!=1:raise ValueError('Legend not uniquely established')
    axis,colours,legend=candidates[0]
    coloured={v:{(r,c) for r in range(h) for c in range(w) if grid[r][c]==v and (r,c) not in legend} for v in colours}
    present=[i for i,v in enumerate(colours) if coloured[v]];first=present[0];anchor=coloured[colours[first]]
    period=max(p[axis] for p in anchor)-min(p[axis] for p in anchor)+1
    options={}
    for direction in (-1,1):
        out=[[bg]*w for _ in range(h)];valid=True
        for i,colour in enumerate(colours):
            offset=(i-first)*direction*period
            cells={(r+(offset if axis==0 else 0),c+(offset if axis==1 else 0)) for r,c in anchor}
            if any(not(0<=r<h and 0<=c<w) for r,c in cells) or (coloured[colour] and cells!=coloured[colour]):valid=False;break
            for r,c in cells:out[r][c]=colour
        if valid:options[direction]=out
    return options


def require_legend_stack_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('94be5b80: demonstrations required')
    alive={-1,1}
    try:
        for pair in demonstrations:
            options=legend_stack_options(pair['input'],palette)
            alive &= {direction for direction,out in options.items() if out==pair['output']}
        if not alive:raise ValueError('No demonstrated direction')
        for q in queries:
            options=legend_stack_options(q['input'],palette)
            answers={tuple(map(tuple,out)) for direction,out in options.items() if direction in alive}
            if len(answers)!=1:raise ValueError('Stack answer not uniquely established')
    except (ValueError,IndexError,TypeError) as exc:raise MissingColourEvidence('94be5b80: '+str(exc)) from exc
