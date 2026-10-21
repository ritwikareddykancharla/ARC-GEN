"""Visible coloured-line reconstruction independent of emitted target parsing."""
from arc_agi2.colour_evidence import MissingColourEvidence
import numpy as np
from collections import Counter

def readings(grid,bg):
 g=np.asarray(grid);H,W=g.shape;threads=[]
 for colour in set(g.ravel().tolist())-{bg}:
  ys,xs=np.where(g==colour)
  if len(ys)<=2:continue
  if len(set(ys))==1:threads.append(('row',int(ys[0]),colour))
  if len(set(xs))==1:threads.append(('col',int(xs[0]),colour))
 out=[]
 for _,hr,hc in [x for x in threads if x[0]=='row']:
  for _,vc,vc0 in [x for x in threads if x[0]=='col']:
   if hc==vc0:continue
   off=g.copy();off[hr,:]=bg;off[:,vc]=bg
   if np.any(off!=bg):continue
   cross=int(g[hr,vc])
   if cross not in (hc,vc0):continue
   axes=[]
   for line,skip,col in [(g[:,vc],hr,vc0),(g[hr,:],vc,hc)]:
    ids=[i for i,v in enumerate(line) if i!=skip and v not in (bg,col)]
    if len(ids)!=2 or ids[1]-ids[0]<2 or line[ids[0]]!=line[ids[1]]:break
    axes.append((col,int(line[ids[0]]),ids))
   if len(axes)!=2 or len({x for a in axes for x in a[:2]})!=4:continue
   out.append((hr,vc,cross,axes))
 return out

def alternatives(grid,bg,h):
 axis,anchor_a,anchor_b,boundary=h;outs=[]
 for hr,vc,cross,axes in readings(grid,bg):
  ct,cm,am=axes[axis];wt,wm,bm=axes[1-axis];wp=(hr,vc)[axis]
  if min(am)<wp<max(am):continue
  if wp in am:continue
  amin,amax=min(am+[wp]),max(am+[wp]);bmin,bmax=min(bm),max(bm)
  av=np.arange(amin,amax+1);bv=np.arange(bmin,bmax+1)
  ae=((av-(amin if anchor_a else amax))%2==0)[:,None]
  be=((bv-(bmin if anchor_b else bmax))%2==0)[None,:]
  mark=np.where((av>=min(am))&(av<=max(am)),cm,wm)[:,None]
  region=np.where(ae,np.where(be,mark,ct),np.where(be,wt,cross))
  out=np.full(np.asarray(grid).shape,bg)
  if axis==0:out[amin:amax+1,bmin:bmax+1]=region
  else:out[bmin:bmax+1,amin:amax+1]=region.T
  if not boundary:outs.append(out.tolist())
  else:
   distance=min(abs(a-wp) for a in am)
   for near in [a for a in am if abs(a-wp)==distance]:
    result=out.copy()
    if distance%2==0:
     for b in bv[(bv-(bmin if anchor_b else bmax))%2==1]:
      r,c=(near,int(b)) if axis==0 else (int(b),near)
      result[r,c]=cross
    outs.append(result.tolist())
 return outs

def gate(demos,query,palette):
 bg=palette[0];hs=[(a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (False,True)]
 for d in demos:
  hs=[h for h in hs if d['output'] in alternatives(d['input'],bg,h)]
  if not hs:return {'status':'inconsistent_demonstration'}
 outs=[o for h in hs for o in alternatives(query,bg,h)]
 if not outs:return {'status':'no_visible_reading'}
 if any(o!=outs[0] for o in outs):return {'status':'context_shortfall','surviving_hypotheses':hs}
 return {'status':'unique','output':outs[0],'surviving_hypotheses':hs}


def require_evidence(demos,queries,palette):
 for x in list(demos)+list(queries):
  inp=x['input'] if isinstance(x,dict) else x
  result=gate(demos,inp,palette)
  if result['status']!='unique':raise MissingColourEvidence(result['status'])
