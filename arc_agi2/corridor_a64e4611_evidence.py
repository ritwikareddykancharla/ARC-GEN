"""Independent array-based930-hypothesis clearance gate. Query labels ignored."""
import numpy as np
import os
from functools import lru_cache
try:
 from arc_agi2.colour_evidence import MissingColourEvidence
except ImportError:
 class MissingColourEvidence(ValueError):pass
PARAMETERS=tuple((r,k) for r in range(1,31) for k in range(31))

def _run_bounds(mask):
 width=mask.shape[1];columns=np.arange(width)[None,:]
 starts=mask & ~np.pad(mask[:,:-1],((0,0),(1,0)))
 ends=mask & ~np.pad(mask[:,1:],((0,0),(0,1)))
 left=np.maximum.accumulate(np.where(starts,columns,0),axis=1)
 right=np.minimum.accumulate(np.where(ends,columns,width-1)[:,::-1],axis=1)[:,::-1]
 return left,right

def _mark_runs(mask,length):
 left,right=_run_bounds(mask)
 return mask & (right-left+1>=length)

@lru_cache(maxsize=64)
def _initials(g,bg):
 a=np.array(g);h,w=a.shape;pad=np.pad(a,1,constant_values=bg);safe=np.ones((h,w),bool)
 for dr in range(3):
  for dc in range(3):safe&=pad[dr:dr+h,dc:dc+w]==bg
 left,right=_run_bounds(safe);horizontal=right-left+1
 left,right=_run_bounds(safe.T);vertical=(right-left+1).T
 return tuple((safe & ((horizontal>=r)|(vertical>=r))).tobytes() for r in range(1,31))

@lru_cache(maxsize=4096)
def _prune(g,paint_bytes,limit,bg,fill):
 if os.environ.get('ARCGEN_CORRIDOR_JIT') == '1':
  from .corridor_a64e4611_jit import prune_array
  a=np.array(g,dtype=np.int64)
  result=prune_array(a,np.frombuffer(paint_bytes,dtype=bool).reshape(a.shape),limit,bg,fill)
  return tuple(map(tuple,result.tolist()))
 a=np.array(g);pad=np.pad(a,1,constant_values=bg);pad[1:-1,1:-1][np.frombuffer(paint_bytes,dtype=bool).reshape(a.shape)]=fill
 if limit:
  while True:
   removed=np.zeros_like(pad,bool)
   for k in range(4):
    b=np.rot90(pad,k);cut=np.zeros_like(b,bool)
    mask=b[2:-1,1:-1]==fill
    if not mask.size:continue
    left,right=_run_bounds(mask)
    left_colour=np.take_along_axis(b[2:-1],left,axis=1)
    right_colour=np.take_along_axis(b[2:-1],right+2,axis=1)
    occupied_above=np.pad(np.cumsum(b[1:-2,1:-1]!=bg,axis=1),((0,0),(1,0)))
    blocked=np.take_along_axis(occupied_above,right+1,axis=1)-np.take_along_axis(occupied_above,left,axis=1)
    cut[2:-1,1:-1]=mask & (right-left+1<=limit) & (left_colour==bg) & (right_colour==bg) & (blocked==0)
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
