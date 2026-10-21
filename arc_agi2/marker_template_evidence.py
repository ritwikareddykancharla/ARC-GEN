"""Independent marker-component and anchor-offset hypothesis gate.

Declared finite scope: copy intact, or trim the non-corner pixels on the two
outward-facing sides of a hollow square before copying. Demonstrations select
between these rules; neither is inferred from the query answer. This is not a
claim that the original benchmark uniquely establishes this hypothesis class.
"""
from arc_agi2.colour_evidence import MissingColourEvidence

def alternatives(g,pal,trim):
 bg,tc,dc=pal[0],pal[2],pal[4];H,W=len(g),len(g[0])
 if any(v not in (bg,tc,dc) for row in g for v in row):return []
 dots={(r,c) for r in range(H) for c in range(W) if g[r][c]==dc};todo=set(dots);groups=[]
 while todo:
  point=min(todo);todo.remove(point);stack=[point];group={point}
  while stack:
   r,c=stack.pop();neighbours={p for p in todo if abs(p[0]-r)<=2 and abs(p[1]-c)<=2}
   todo-=neighbours;stack.extend(neighbours);group|=neighbours
  groups.append(group)
 anchors=[]
 for group in groups:
  ys={r for r,c in group};xs={c for r,c in group}
  if len(group)!=3 or len(ys)!=2 or len(xs)!=2 or max(ys)-min(ys)!=2 or max(xs)-min(xs)!=2:return []
  corners={(r,c) for r in ys for c in xs};missing=corners-group
  if len(missing)!=1:return []
  r,c=missing.pop();anchors.append((r,c,-1 if r==min(ys) else 1,-1 if c==min(xs) else 1))
 cells={(r,c) for r in range(H) for c in range(W) if g[r][c]==tc}
 if not cells:return []
 ymin,ymax=min(r for r,c in cells),max(r for r,c in cells);xmin,xmax=min(c for r,c in cells),max(c for r,c in cells);L=ymax-ymin+1
 if L!=xmax-xmin+1 or L not in (2,3):return []
 owners=[a for a in anchors if {a[2]*(r-a[0]) for r,c in cells}==set(range(L)) and {a[3]*(c-a[1]) for r,c in cells}==set(range(L))]
 if len(owners)!=1:return []
 outlist=[]
 for mr,mc,sy,sx in owners:
  offsets={(sy*(r-mr),sx*(c-mc)) for r,c in cells}
  if {r for r,c in offsets}!=set(range(L)) or {c for r,c in offsets}!=set(range(L)):continue
  perimeter={(r,c) for r in range(L) for c in range(L) if r in (0,L-1) or c in (0,L-1)}
  if trim and offsets==perimeter:
   offsets=offsets-{(L-1,k) for k in range(1,L-1)}-{(k,L-1) for k in range(1,L-1)}
  result=[[bg]*W for _ in range(H)]
  for r,c in dots:result[r][c]=dc
  valid=True
  for ar,ac,dy,dx in anchors:
   square={(ar+dy*r,ac+dx*c) for r in range(L) for c in range(L)}
   if any(not(0<=r<H and 0<=c<W) for r,c in square):valid=False;break
   pixels={(ar+dy*r,ac+dx*c) for r,c in offsets}
   if pixels&dots:valid=False;break
   for r,c in pixels:result[r][c]=tc
  if valid:outlist.append(result)
 return outlist

def gate(demos,query,palette):
 rules=[False,True]
 for d in demos:
  rules=[r for r in rules if d['output'] in alternatives(d['input'],palette,r)]
  if not rules:return {'status':'inconsistent_demonstration'}
 outs=[o for r in rules for o in alternatives(query,palette,r)]
 if not outs:return {'status':'no_visible_reading'}
 if any(o!=outs[0] for o in outs):return {'status':'context_shortfall','surviving_rules':rules}
 return {'status':'unique','output':outs[0],'surviving_rules':rules}

def require_evidence(demonstrations,queries,palette):
 for item in list(demonstrations)+list(queries):
  inp=item['input'] if isinstance(item,dict) else item
  status=gate(demonstrations,inp,palette)['status']
  if status!='unique':raise MissingColourEvidence('ac0c5833: '+status)
