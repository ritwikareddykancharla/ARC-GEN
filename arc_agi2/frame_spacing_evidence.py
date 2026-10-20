"""Distinguish projection separation from total spread without dropping outliers."""
from .colour_evidence import MissingColourEvidence,_require_rule_agreement


def spacing_variants(grid,palette):
    bg=palette[0];by_colour={}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v!=bg:by_colour.setdefault(v,[]).append((r,c))
    frames=[]
    for colour,cells in by_colour.items():
        r0=min(r for r,c in cells);c0=min(c for r,c in cells)
        expected={(r0+r,c0+c) for r in range(4) for c in range(4)}
        border={(r,c) for r,c in expected if r in (r0,r0+3) or c in (c0,c0+3)}
        if set(cells)==expected:continue
        if set(cells)!=border or any(grid[r][c]!=bg for r in (r0+1,r0+2) for c in (c0+1,c0+2)):
            raise MissingColourEvidence('a680ac02: expected distinct-colour solid or hollow4x4squares')
        frames.append((r0,c0,colour))
    if len(frames)<2:raise MissingColourEvidence('a680ac02: need at least two hollow frames')
    rows=sorted(r for r,c,v in frames);cols=sorted(c for r,c,v in frames)
    rg=min(b-a for a,b in zip(rows,rows[1:]));cg=min(b-a for a,b in zip(cols,cols[1:]))
    if rg<4<cg:gap_axis=1
    elif cg<4<rg:gap_axis=0
    else:raise MissingColourEvidence('a680ac02: no unique separated projection axis')
    rs,cs=rows[-1]-rows[0],cols[-1]-cols[0]
    span_rows=0 if rs>=cs else 1
    span_cols=0 if rs>cs else 1
    outputs=[]
    for axis in (gap_axis,span_rows,span_cols):
        ordered=sorted(frames,key=lambda p:p[axis])
        out=[[bg]*(4 if axis==0 else 4*len(frames)) for _ in range(4*len(frames) if axis==0 else 4)]
        for i,(_,_,colour) in enumerate(ordered):
            for r in range(4):
                for c in range(4):
                    if r in (0,3) or c in (0,3):out[r+4*i if axis==0 else r][c if axis==0 else c+4*i]=colour
        outputs.append(out)
    return outputs


def require_spacing_evidence(demonstrations,queries,palette):
    _require_rule_agreement('a680ac02',demonstrations,queries,lambda g:spacing_variants(g,palette))
