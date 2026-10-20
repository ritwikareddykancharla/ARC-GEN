"""Independent finite-state path walker over immutable observed cells."""
from .colour_evidence import MissingColourEvidence


FRAMES=[(u,v) for u in ((-1,0),(1,0),(0,-1),(0,1)) for v in ((-1,0),(1,0),(0,-1),(0,1)) if u[0]*v[0]+u[1]*v[1]==0]


def path_output(grid,up,side,palette,reverse_starts=False):
    bg,path,exit,turn,mark,wall,hit=(palette[c] for c in (0,2,3,4,6,7,8))
    h,w=len(grid),len(grid[0]);read=lambda r,c:grid[r][c]
    valid=lambda r,c:0<=r<h and 0<=c<w
    starts=[(r,c) for r in range(h) for c in range(w) if grid[r][c]==mark]
    if not starts or any(valid(r-up[0],c-up[1]) for r,c in starts):raise ValueError('No unique incoming edge')
    if reverse_starts:starts.reverse()
    additions={}
    for sr,sc in starts:
        r,c=sr+up[0],sc+up[1];phase='forward';updates={};moved=False
        if not valid(r,c) or read(r,c)!=bg:raise ValueError('Blocked initial cell')
        for _ in range(h*w*2):
            ar,ac=r+up[0],c+up[1]
            if not valid(r,c) or read(r,c)!=bg:raise ValueError('Blocked path cell')
            if phase=='forward':
                if not valid(ar,ac):updates[r,c]=mark;break
                if read(ar,ac)==bg:
                    updates[r,c]=path;r,c=ar,ac;continue
                if read(ar,ac)!=wall:raise ValueError('Unexpected colour ahead')
                nr,nc=r+side[0],c+side[1]
                if not valid(nr,nc):raise ValueError('Lateral overflow')
                if read(nr,nc)==wall:updates[r,c]=mark;break
                if read(nr,nc)!=bg:raise ValueError('Blocked lateral start')
                updates[r,c]=turn;updates[ar,ac]=hit;r,c=nr,nc;phase='lateral';moved=True
            else:
                if read(ar,ac)==wall:
                    updates[r,c]=path;r,c=r+side[0],c+side[1]
                elif read(ar,ac)==bg:
                    updates[r,c]=exit;r,c=ar,ac;phase='forward'
                else:raise ValueError('Unexpected obstacle colour')
        else:raise ValueError('Path did not terminate')
        if not moved:raise ValueError('Path never moved laterally')
        if set(additions)&set(updates):raise ValueError('Path collision')
        additions.update(updates)
    return [[additions.get((r,c),v) for c,v in enumerate(row)] for r,row in enumerate(grid)]


def require_obstacle_path_evidence(demonstrations,queries,palette):
    if not demonstrations:raise MissingColourEvidence('891232d6: demonstrations required')
    alive=FRAMES[:]
    for p in demonstrations:
        good=[]
        for u,v in alive:
            try:
                if path_output(p['input'],u,v,palette)==p['output']:good.append((u,v))
            except (ValueError,IndexError):pass
        alive=good
    if not alive:raise MissingColourEvidence('891232d6: no demonstrated orientation')
    for q in queries:
        answers=set()
        for u,v in alive:
            try:answers.add(tuple(map(tuple,path_output(q['input'],u,v,palette))))
            except (ValueError,IndexError):pass
        if len(answers)!=1:raise MissingColourEvidence('891232d6: unresolved paths')
