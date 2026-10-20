"""Distinguish erase, reserve and fill semantics using visible episodes.

48 hypotheses retain the native rule plus explicit alternatives to erasure,
reservation and legend ordering. This is a bounded ambiguity check, not proof
of identifiability against every conceivable rule. Query labels are unused.
"""
from collections import Counter
from .colour_evidence import MissingColourEvidence, _require_rule_agreement


def parse_paint_legend(g,d4):
    counts = Counter(v for row in g for v in row).most_common()
    if len(counts)>1 and counts[0][1] == counts[1][1]:
        raise MissingColourEvidence('9385bd28: background is not uniquely most frequent')
    bg = counts[0][0]
    def vector(dr,dc):
        if d4>=4: dc = -dc
        for _ in range(d4%4): dr,dc = dc,-dr
        return dr,dc
    order,kv = vector(1,0),vector(0,1)
    remaining = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != bg}
    candidates = []
    while remaining:
        first = remaining.pop();stack = [first];cells = {first}
        while stack:
            r,c = stack.pop()
            for p in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if p in remaining:
                    remaining.remove(p);cells.add(p);stack.append(p)
        top,bottom = min(r for r,c in cells),max(r for r,c in cells)
        left,right = min(c for r,c in cells),max(c for r,c in cells)
        colours = {g[r][c] for r,c in cells}
        thick = right-left == 1 if kv[0] == 0 else bottom-top == 1
        if thick and len(colours)>1: candidates.append((len(colours),(top,left,bottom,right)))
    if not candidates: raise MissingColourEvidence('9385bd28: legend not found')
    best = max(n for n,box in candidates)
    boxes = [box for n,box in candidates if n == best]
    if len(boxes)!=1: raise MissingColourEvidence('9385bd28: legend is not unique')
    top,left,bottom,right = boxes[0]
    legend = {(r,c) for r in range(top,bottom+1) for c in range(left,right+1)}
    if kv[0] == 0:
        kc,vc = (left,right) if kv[1]>0 else (right,left)
        coords = sorted(range(top,bottom+1),reverse=order[0]<0)
        rows = [(g[r][kc],g[r][vc]) for r in coords]
    else:
        kr,vr = (top,bottom) if kv[0]>0 else (bottom,top)
        coords = sorted(range(left,right+1),reverse=order[1]<0)
        rows = [(g[kr][c],g[vr][c]) for c in coords]
    entries = []
    for key,value in rows:
        if key == bg: continue
        cells = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row)
                 if v == key and (r,c) not in legend}
        region = set()
        if cells:
            region = {(r,c) for r in range(min(r for r,c in cells),max(r for r,c in cells)+1)
                      for c in range(min(c for r,c in cells),max(c for r,c in cells)+1)} - legend
        entries.append((value,cells,region))
    return bg,entries


def paint_variants(g,palette,d4):
    bg,entries = parse_paint_legend(g,d4)
    erase_colour = palette[0]
    outputs = []
    for erase_mode in ('early','inline','fill','ignore'):
        for reserve_mode in ('reserve','fill','ignore'):
            for order_mode in ('legend','reverse','small','large'):
                rows = entries
                if order_mode == 'reverse': rows = rows[::-1]
                elif order_mode in ('small','large'):
                    def area(entry):
                        cells = entry[1]
                        if not cells: return 0
                        return ((max(r for r,c in cells)-min(r for r,c in cells)+1)
                                *(max(c for r,c in cells)-min(c for r,c in cells)+1))
                    rows = sorted(rows,key=area,reverse=order_mode=='large')
                out = [row[:] for row in g];claimed = set()
                if erase_mode == 'early' and bg != erase_colour:
                    for value,cells,region in rows:
                        if value == erase_colour:
                            for r,c in cells: out[r][c] = bg
                for value,cells,region in rows:
                    if value == erase_colour and bg != erase_colour and erase_mode != 'fill':
                        if erase_mode == 'inline':
                            for r,c in cells: out[r][c] = bg
                        continue
                    free = {p for p in region-claimed if out[p[0]][p[1]] == bg}
                    if value == bg:
                        if reserve_mode == 'ignore': continue
                        if reserve_mode == 'reserve':
                            claimed |= free
                            continue
                    changed = free if free else cells
                    for r,c in changed: out[r][c] = value
                    claimed |= changed
                outputs.append(out)
    return outputs


def require_paint_evidence(demonstrations,queries,palette,d4):
    _require_rule_agreement('9385bd28',demonstrations,queries,
                            lambda g:paint_variants(g,palette,d4))
