"""Recover mosaics under the documented observable-band contract."""
TEMPLATE='''import numpy as np

BG = __BG__


def _partitions(m):
    h,w=len(m),len(m[0]);visible=[any(m[y][x]!=BG for y in range(h)) for x in range(w)]
    positions=[x for x,v in enumerate(visible) if v]
    if not positions:return []
    lo,hi=positions[0],positions[-1];prefix=[0]
    for v in visible:prefix.append(prefix[-1]+int(v))
    extent=[]
    for a in range(w):
        colours=[None]*h;b=a
        while b<w:
            if any(m[y][b]!=BG and colours[y] is not None and m[y][b]!=colours[y] for y in range(h)):break
            for y in range(h):
                if m[y][b]!=BG:colours[y]=m[y][b]
            b+=1
        extent.append(b)
    found={}
    for start in range(1,min(lo,6)+1):
        def visit(cuts):
            pos=cuts[-1];count=len(cuts)-1
            if pos>hi and 2<=count<=4 and 1<=w-pos<=6 and min(start,w-pos)<=2:
                found.setdefault(tuple(prefix[c] for c in cuts),tuple(cuts))
            if count==4 or pos>=w-1:return
            for end in range(pos+3,min(pos+8,start+16,w-1,extent[pos])+1):
                if prefix[end]>prefix[pos]:visit(cuts+[end])
        visit([start])
    return list(found.values())


def _recover(grid):
    g=[[int(v) for v in row] for row in grid]
    if not g or not g[0] or any(len(row)!=len(g[0]) for row in g):raise ValueError('Expected rectangular mosaic')
    columns=_partitions(g);rows=_partitions([list(x) for x in zip(*g)])
    answers=set()
    for cc in columns:
        for rr in rows:
            blocks=[];valid=True
            for a,b in zip(rr,rr[1:]):
                line=[]
                for c,d in zip(cc,cc[1:]):
                    colours={g[y][x] for y in range(a,b) for x in range(c,d) if g[y][x]!=BG}
                    if len(colours)>1:valid=False;break
                    line.append(next(iter(colours)) if colours else -1)
                if not valid:break
                blocks.append(tuple(line))
            if not valid:continue
            if any(all(a==b and a!=-1 for a,b in zip(blocks[i-1],blocks[i])) for i in range(1,len(blocks))):continue
            if any(all(row[j-1]==row[j] and row[j]!=-1 for row in blocks) for j in range(1,len(blocks[0]))):continue
            # Each unknown cell has at most four neighbours and nine possible
            # non-background colours, so at least two valid assignments exist.
            if any(-1 in row for row in blocks):raise ValueError('A compatible layout contains an erased block')
            answers.add(tuple(blocks))
            if len(answers)>1:raise ValueError('Several compatible block grids')
    if len(answers)!=1:raise ValueError('No compatible mosaic')
    return np.asarray(next(iter(answers)),dtype=int)


def solve(demonstrations,grid):
    if not demonstrations:raise ValueError('Demonstrations required')
    alive={0,1}
    for p in demonstrations:
        blocks=_recover(p['input']);expected=np.asarray(p['output'])
        alive &= {axis for axis in alive if np.array_equal(np.flip(blocks,axis=axis),expected)}
    if not alive:raise ValueError('No demonstrated mirror axis')
    blocks=_recover(grid);outputs=[np.flip(blocks,axis=a) for a in alive]
    if any(not np.array_equal(p,outputs[0]) for p in outputs[1:]):raise ValueError('Ambiguous mirror axis')
    return outputs[0].tolist()
'''


def build_program(d4,palette):
    return TEMPLATE.replace('__BG__',str(int(palette[0])))
