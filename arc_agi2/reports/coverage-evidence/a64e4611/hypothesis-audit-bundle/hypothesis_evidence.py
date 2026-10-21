"""Independent array-based930-hypothesis clearance gate. Query labels ignored."""
import numpy as np
from functools import lru_cache
try:
 from arc_agi2.colour_evidence import MissingColourEvidence
except ImportError:
 class MissingColourEvidence(ValueError):pass
PARAMETERS=tuple((r,k) for r in range(1,31) for k in range(31))

def _mark_runs(mask,length):
 result=np.zeros_like(mask)
 for r,row in enumerate(mask):
  changes=np.diff(np.concatenate(([False],row,[False])).astype(int));starts=np.flatnonzero(changes==1);ends=np.flatnonzero(changes==-1)
  for a,b in zip(starts,ends):
   if b-a>=length:result[r,a:b]=True
 return result

@lru_cache(maxsize=64)
def _initials(g,bg):
 a=np.array(g);h,w=a.shape;pad=np.pad(a,1,constant_values=bg);safe=np.ones((h,w),bool)
 for dr in range(3):
  for dc in range(3):safe&=pad[dr:dr+h,dc:dc+w]==bg
 return tuple((_mark_runs(safe,r)|_mark_runs(safe.T,r).T).tobytes() for r in range(1,31))

@lru_cache(maxsize=4096)
def _prune(g,paint_bytes,limit,bg,fill):
 a=np.array(g);pad=np.pad(a,1,constant_values=bg);pad[1:-1,1:-1][np.frombuffer(paint_bytes,dtype=bool).reshape(a.shape)]=fill
 if limit:
  while True:
   removed=np.zeros_like(pad,bool)
   for k in range(4):
    b=np.rot90(pad,k);cut=np.zeros_like(b,bool)
    for r in range(2,len(b)-1):
     mask=b[r,1:-1]==fill;changes=np.diff(np.concatenate(([False],mask,[False])).astype(int))
     for start,end in zip(np.flatnonzero(changes==1)+1,np.flatnonzero(changes==-1)+1):
      if end-start<=limit and b[r,start-1]==bg and b[r,end]==bg and np.all(b[r-1,start:end]==bg):cut[r,start:end]=True
    removed|=np.rot90(cut,-k)
   if not removed.any():break
   pad[removed]=bg
 return tuple(map(tuple,pad[1:-1,1:-1].tolist()))

def fit(demos,palette):
 bg,fill=palette[0],palette[3];params=PARAMETERS
 for p in demos:
  g=tuple(map(tuple,p['input']));expected=tuple(map(tuple,p['output']));initials=_initials(g,bg)
  params=tuple((r,k) for r,k in params if _prune(g,initials[r-1],k,bg,fill)==expected)
  if not params:raise MissingColourEvidence('No parameter hypothesis fits all demonstrations')
 return params

def query_predictions(demos,query_input,palette):
 params=fit(demos,palette);g=tuple(map(tuple,query_input));initials=_initials(g,palette[0]);outputs={}
 for r,k in params:
  y=_prune(g,initials[r-1],k,palette[0],palette[3]);outputs.setdefault(y,[]).append((r,k))
 return params,outputs

def require_corridor_evidence(demos,queries,palette):
 params=fit(demos,palette)
 for q in queries:
  g=tuple(map(tuple,q['input']));initials=_initials(g,palette[0]);answer=None
  for r,k in params:
   y=_prune(g,initials[r-1],k,palette[0],palette[3])
   if answer is None:answer=y
   elif y!=answer:raise MissingColourEvidence('Demo-compatible clearance parameters disagree on query')
 return {'parameters':params,'parameter_count':len(params),'query_label_access':False}
