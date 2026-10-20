"""Read colour-specific line motifs from demonstrations in visible coordinates."""
from .colour_evidence import MissingColourEvidence


def _fail(message):
    raise MissingColourEvidence('98c475bf: '+message)


def _frame(g,bg):
    h,w=len(g),len(g[0])
    border=g[0][0]
    if border==bg:
        _fail('missing solid coloured borders')
    horizontal=all(row[0]==row[-1]==border for row in g)
    vertical=all(g[0][c]==g[-1][c]==border for c in range(w))
    if horizontal==vertical:
        _fail('border geometry does not establish one line axis')
    across,along=(h,w) if horizontal else (w,h)
    if along<5:
        _fail('line span is too short')
    xy=lambda p,s:(p,s) if horizontal else (s,p)
    get=lambda p,s:g[xy(p,s)[0]][xy(p,s)[1]]
    return horizontal,across,along,xy,get


def solve_visible_motifs(demonstrations,query_input,bg):
    templates={};geometry=None
    for demo in demonstrations:
        for field in ('input','output'):
            g=demo[field]
            horizontal,across,along,xy,get=_frame(g,bg)
            if geometry is not None and geometry!=(horizontal,along):
                _fail('demonstrations have incompatible axes or line spans')
            geometry=horizontal,along
            colours={get(p,s) for p in range(across) for s in range(1,along-1)}-{bg}
            for colour in colours:
                lines=[p for p in range(across) if get(p,1)==get(p,along-2)==colour
                       and any(get(p,s)==colour for s in range(2,along-2))]
                if not lines:continue
                if len(lines)!=1:_fail('multiple full lines for one colour')
                cells=frozenset((p-lines[0],s) for p in range(across) for s in range(1,along-1)
                                if get(p,s)==colour)
                if colour in templates and templates[colour]!=cells:
                    _fail('conflicting demonstrated templates')
                templates[colour]=cells
    horizontal,across,along,xy,get=_frame(query_input,bg)
    if geometry!=(horizontal,along):
        _fail('query axis or span differs from demonstrations')
    markers=[(p,get(p,1)) for p in range(across)
             if get(p,1)!=bg and get(p,1)==get(p,along-2)
             and all(get(p,s)==bg for s in range(2,along-2))]
    if not markers:_fail('no query marker pairs')
    if {colour for p,colour in markers}-templates.keys():
        _fail('query marker colour has no demonstrated motif')
    out=[row[:] for row in query_input]
    for p in range(across):
        for s in range(1,along-1):
            r,c=xy(p,s);out[r][c]=bg
    for p,colour in markers:
        for dp,s in templates[colour]:
            if not 0<=p+dp<across:_fail('demonstrated motif would be clipped')
            r,c=xy(p+dp,s)
            if out[r][c] not in (bg,colour):_fail('demonstrated motifs would overlap')
            out[r][c]=colour
    return out


def require_line_motif_evidence(demonstrations,queries,palette):
    for query in queries:
        solve_visible_motifs(demonstrations,query['input'],palette[0])
