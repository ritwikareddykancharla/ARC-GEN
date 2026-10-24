"""Finite competing readings for e74e1818; no query answers are consumed.

Candidates: per-band identity, vertical/horizontal/180-degree reflection,
whole-grid vertical/horizontal reflection, and per-band ink-count row sorting
in either direction. This bounds a useful ambiguity check, not all ARC rules.
"""
from .augmentation import transformed
from .marker_roll_evidence import native


def variants(g):
    spans=[]
    for r, row in enumerate(g):
        inks=set(row)-{0}
        if not inks:
            continue
        if len(inks)!=1:
            raise ValueError('Expected one ink colour per occupied row')
        colour=next(iter(inks))
        if spans and spans[-1][0]==colour and spans[-1][2]==r:
            spans[-1]=(colour,spans[-1][1],r+1)
        else:
            spans.append((colour,r,r+1))
    out=[]
    for mode in ('identity','vertical','horizontal','rotate','sparse','dense'):
        a=[row[:] for row in g]
        for _,lo,hi in spans:
            rows=[row[:] for row in g[lo:hi]]
            if mode in ('vertical','rotate'):rows=rows[::-1]
            if mode in ('horizontal','rotate'):rows=[row[::-1] for row in rows]
            if mode in ('sparse','dense'):
                rows=sorted(rows,key=lambda row:sum(c!=0 for c in row),reverse=mode=='dense')
            a[lo:hi]=rows
        out.append(a)
    return out+[[row[:] for row in g[::-1]],[row[::-1] for row in g]]


def require_band_reflection_evidence(demonstrations,queries,palette=None,d4=0):
    from .colour_evidence import _require_rule_agreement
    palette=list(range(10)) if palette is None else palette
    def visible(g):
        return [transformed(a,d4,palette) for a in variants(native(g,palette,d4))]
    _require_rule_agreement('e74e1818',demonstrations,queries,visible)
