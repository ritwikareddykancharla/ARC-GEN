"""Independent clipped-bracket coordinate construction and assembly evidence."""
from .colour_evidence import MissingColourEvidence


def _brackets(radius,length):
    groups=[]
    for sy in (-1,1):
        for sx in (-1,1):
            groups.append({(sy*radius,sx*(radius-j)) for j in range(length)}|
                          {(sy*(radius-j),sx*radius) for j in range(length)})
    return groups


def unique_corner_assembly(grid):
    h=len(grid);w=len(grid[0]);points={}
    if not h or not w or any(len(row)!=w for row in grid):raise ValueError('Invalid grid')
    for y,row in enumerate(grid):
        for x,c in enumerate(row):points.setdefault(c,set()).add((y,x))
    maximum=max(map(len,points.values()));bgs=[c for c in points if len(points[c])==maximum]
    if len(bgs)!=1:raise ValueError('Ambiguous background')
    bg=bgs[0];colours=[c for c in points if c!=bg];n=len(colours)
    if not n:raise ValueError('No frames')
    options={c:set() for c in colours}
    for colour in colours:
        cells=points[colour];ys,xs=zip(*cells)
        for radius in range(n+1):
            if max(ys)-min(ys)>2*radius or max(xs)-min(xs)>2*radius:continue
            lengths=(1,) if radius==0 else (2,) if radius==1 else range(2,radius+1)
            for length in lengths:
                groups=_brackets(radius,length)
                for cy in range(max(ys)-radius,min(ys)+radius+1):
                    for cx in range(max(xs)-radius,min(xs)+radius+1):
                        visible=[{(cy+dy,cx+dx) for dy,dx in group if 0<=cy+dy<h and 0<=cx+dx<w} for group in groups]
                        if radius and sum(bool(group) for group in visible)<2:continue
                        if set().union(*visible)==cells:options[colour].add((radius,length))
    answers=set()
    for start in (0,1):
        radii=set(range(start,start+n));outer=max(radii);side=2*outer+1
        def recurse(todo,used,chosen):
            if not todo:
                result=[[bg]*side for _ in range(side)]
                for c,(radius,length) in chosen.items():
                    for dy,dx in set().union(*_brackets(radius,length)):result[outer+dy][outer+dx]=c
                answers.add(tuple(tuple(row) for row in result));return
            c=todo[0]
            for radius,length in options[c]:
                if radius in radii and radius not in used:recurse(todo[1:],used|{radius},chosen|{c:(radius,length)})
        recurse(colours,set(),{})
    if len(answers)!=1:raise ValueError('Unresolved corner-frame assembly')
    return [list(row) for row in next(iter(answers))]


def require_corner_frame_evidence(demonstrations,queries,palette=None):
    try:
        for p in demonstrations:
            if unique_corner_assembly(p['input'])!=p['output']:raise ValueError('Contradictory demo')
        for q in queries:unique_corner_assembly(q['input'])
    except (ValueError,TypeError,IndexError) as exc:raise MissingColourEvidence('4290ef0e: corner-frame assembly is not uniquely visible') from exc
