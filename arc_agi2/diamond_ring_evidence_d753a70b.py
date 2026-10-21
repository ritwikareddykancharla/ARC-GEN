"""Independent coordinate-set exact cover of 3–6 concentric Manhattan rings."""
from arc_agi2.colour_evidence import MissingColourEvidence

def ring_readings(g,palette):
 bg,shrink,grow=palette[7],palette[2],palette[5];h,w=len(g),len(g[0])
 points={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
 def perimeter(y,x,r):
  out=set()
  for row in range(max(0,y-r),min(h,y+r+1)):
   d=r-abs(row-y)
   for col in (x-d,x+d):
    if 0<=col<w:out.add((row,col))
  return out
 candidates=[];index={p:[] for p in points}
 for y in range(h):
  for x in range(w):
   radius=min(abs(r-y)+abs(c-x) for r,c in points)
   surface=perimeter(y,x,radius)
   if not surface<=points:continue
   colours={g[r][c] for r,c in surface}
   if len(colours)!=1:continue
   colour=next(iter(colours));nr=radius+(-1 if colour==shrink else 1 if colour==grow else 0)
   if nr<0:continue
   target=perimeter(y,x,nr);inside={(r,c) for r in range(h) for c in range(w) if abs(r-y)+abs(c-x)<nr}
   i=len(candidates);candidates.append((surface,target,inside,colour,(y,x,radius)))
   for p in surface:index[p].append(i)
 answers={};calls=0
 def search(rem,chosen,outpoints,forbidden):
  nonlocal calls
  calls+=1
  if calls>100000:raise MissingColourEvidence('Ring-cover search budget exhausted; no arbitrary answer')
  if len(answers)>1:return
  if not rem:
   if 3<=len(chosen)<=6:
    out=[[bg]*w for _ in range(h)]
    for i in chosen:
     for r,c in candidates[i][1]:out[r][c]=candidates[i][3]
    answers.setdefault(tuple(map(tuple,out)),[candidates[i][4] for i in chosen])
   return
  if len(chosen)>=6:return
  # Coordinate-set implementation uses first remaining pixel, unlike target's
  # minimum-compatible-count bitset branch choice.
  p=min(rem)
  for i in index[p]:
   surface,target,inside,_,_=candidates[i]
   if surface<=rem and not target&(outpoints|forbidden) and not inside&outpoints:
    search(rem-surface,chosen+[i],outpoints|target,forbidden|inside)
    if len(answers)>1:return
 search(points,[],set(),set())
 return answers

def require_ring_evidence(demos,queries,palette):
 for is_demo,p in [(True,p) for p in demos]+[(False,p) for p in queries]:
  outputs=ring_readings(p['input'],palette)
  if not outputs:raise MissingColourEvidence('No complete visible concentric-ring interpretation')
  if len(outputs)>1:raise MissingColourEvidence('Two valid visible ring decompositions disagree')
  if is_demo and tuple(map(tuple,p['output'])) not in outputs:
   raise MissingColourEvidence('Demonstration contradicts concentric-ring mechanism')
 return {'unique_visible_output':True}
