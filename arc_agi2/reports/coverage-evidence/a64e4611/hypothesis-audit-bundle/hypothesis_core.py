"""Demo-selected visible clearance hypotheses over run1..30 × prune0..30.

This finite family includes the archived atlas convention12/3 but never prefers
it. Every demonstration is checked; every survivor must agree on the query.
"""
from functools import lru_cache
BG=0
FILL=3
PARAMETERS=tuple((run,prune) for run in range(1,31) for prune in range(31))

def _transpose(rows,width):
 return tuple(sum(((bits>>c)&1)<<r for r,bits in enumerate(rows)) for c in range(width))

def _runs(bits):
 while bits:
  start=(bits&-bits).bit_length()-1
  tail=bits>>start;n=(tail^(tail+1)).bit_length()-1
  mask=((1<<n)-1)<<start
  yield start,n,mask
  bits^=mask

@lru_cache(maxsize=64)
def _initials(grid):
 h=len(grid);w=len(grid[0]);full=(1<<w)-1
 occupied=tuple(sum((v!=BG)<<c for c,v in enumerate(row)) for row in grid)
 safe=[]
 for r in range(h):
  near=occupied[r]|(occupied[r-1] if r else 0)|(occupied[r+1] if r+1<h else 0)
  safe.append(full&~(near|(near<<1)|(near>>1)))
 transposed=_transpose(safe,w);initials=[]
 for length in range(1,31):
  horizontal=tuple(sum(mask for _,n,mask in _runs(bits) if n>=length) for bits in safe)
  vertical=_transpose(tuple(sum(mask for _,n,mask in _runs(bits) if n>=length) for bits in transposed),h)
  initials.append(tuple(a|b for a,b in zip(horizontal,vertical)))
 return occupied,tuple(initials)

def _directional_cuts(paint,occupied,width,prune):
 cuts=[]
 for r,bits in enumerate(paint):
  removed=0
  for start,n,mask in _runs(bits):
   if n>prune:continue
   # The maximal paint run already has no paint at either horizontal end.
   if start and (occupied[r]>>(start-1))&1:continue
   if start+n<width and (occupied[r]>>(start+n))&1:continue
   exposed=(r>0 and not mask&(paint[r-1]|occupied[r-1])) or (r+1<len(paint) and not mask&(paint[r+1]|occupied[r+1]))
   if exposed:removed|=mask
  cuts.append(removed)
 return tuple(cuts)

@lru_cache(maxsize=4096)
def _prune(occupied,initial,width,limit):
 if not limit:return initial
 paint=initial;vertical_occupied=_transpose(occupied,width)
 while True:
  horizontal=_directional_cuts(paint,occupied,width,limit)
  vertical=_transpose(_directional_cuts(_transpose(paint,width),vertical_occupied,len(paint),limit),len(paint))
  nxt=tuple(p&~(a|b) for p,a,b in zip(paint,horizontal,vertical))
  if nxt==paint:return paint
  paint=nxt

def _freeze(grid):
 g=tuple(tuple(row) for row in grid)
 if not g or not g[0] or len(g)>30 or len(g[0])>30 or any(len(row)!=len(g[0]) for row in g):raise ValueError('Expected rectangular grid within30×30')
 return g

def _target_mask(g,y):
 if len(g)!=len(y) or any(len(a)!=len(b) for a,b in zip(g,y)):raise ValueError('Demonstration output shape mismatch')
 mask=[]
 for a,b in zip(g,y):
  bits=0
  for c,(v,t) in enumerate(zip(a,b)):
   if t==FILL and v==BG:bits|=1<<c
   elif t!=v:raise ValueError('Demonstration changes a cell outside clearance painting')
  mask.append(bits)
 return tuple(mask)

def _prediction(g,run,prune):
 occupied,initials=_initials(g)
 return _prune(occupied,initials[run-1],len(g[0]),prune)

def fit(demonstrations):
 candidates=PARAMETERS
 for p in demonstrations:
  g=_freeze(p['input']);target=_target_mask(g,p['output'])
  candidates=tuple((r,k) for r,k in candidates if _prediction(g,r,k)==target)
  if not candidates:raise ValueError('No visible-clearance parameter hypothesis fits all demonstrations')
 return candidates

def solve(demonstrations,grid):
 candidates=fit(demonstrations);g=_freeze(grid);answer=None
 for run,prune in candidates:
  mask=_prediction(g,run,prune)
  if answer is None:answer=mask
  elif mask!=answer:raise ValueError('Demo-compatible clearance hypotheses disagree on query')
 return [[FILL if answer[r]>>c&1 else v for c,v in enumerate(row)] for r,row in enumerate(g)]
