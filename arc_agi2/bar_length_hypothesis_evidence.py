"""Independent component extraction and explicit competing scalar rules."""
from arc_agi2.colour_evidence import MissingColourEvidence
from collections import Counter

def layouts(g,palette):
 bg=palette[0];mark=palette[5];H,W=len(g),len(g[0]);remaining={(r,c) for r in range(H) for c in range(W) if g[r][c]!=bg};objects=[]
 while remaining:
  start=min(remaining);remaining.remove(start);cells=[start];todo=[start]
  while todo:
   r,c=todo.pop()
   for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
    if q in remaining and g[q[0]][q[1]]==g[r][c]:remaining.remove(q);cells.append(q);todo.append(q)
  objects.append(cells)
 singles=[o[0] for o in objects if len(o)==1 and g[o[0][0]][o[0][1]]==mark]
 if len(singles)!=1:return []
 mr,mc=singles[0];bars=[o for o in objects if o!=[singles[0]]];found=[]
 for axis in [0,1]:
  mline=(mr,mc)[axis];mpos=(mc,mr)[axis];N=(H,W)[axis]
  if mline not in (0,N-1) or not bars:continue
  valid=True;positions=[];signs=set();records=[]
  for cells in bars:
   lines={q[axis] for q in cells};across=sorted(q[1-axis] for q in cells)
   if len(lines)!=1 or len(cells) not in (2,3,4,5) or across!=list(range(min(across),max(across)+1)):valid=False;break
   line=next(iter(lines));positions.append(line)
   sign=-1 if max(across)<mpos else 1 if min(across)>mpos else 0;signs.add(sign)
   records.append((line,len(cells),g[cells[0][0]][cells[0][1]]))
  ds=sorted(abs(r-mline) for r in positions)
  if not valid or len(signs)!=1 or 0 in signs or len(set(positions))!=len(bars):continue
  if ds[0] not in (1,2) or ds!=list(range(ds[0],N,2)):continue
  found.append((axis,mpos,records))
 return found

def alternatives(g,palette,rule):
 outs=[]
 for axis,pos,bars in layouts(g,palette):
  eligible=[L for _,L,c in bars if rule=='repeated_all' or c!=palette[5]]
  counts=Counter(eligible)
  # All repeated reference lengths; no first-occurrence or largest-count tie break.
  bases=[None] if rule=='plain' else [L for L,n in counts.items() if n>1] or [None]
  for base in bases:
   out=[row[:] for row in g]
   for line,L,_ in bars:
    offset=L-1 if base is None or L==base else L-base
    v=palette[(offset**2)%10]
    r,c=(line,pos) if axis==0 else (pos,line);out[r][c]=v
   outs.append(out)
 return outs

def gate(demos,query,palette,include_marker_rival=False):
 rules=['plain','repeated_nonmarker']+(['repeated_all'] if include_marker_rival else [])
 for d in demos:
  rules=[r for r in rules if d['output'] in alternatives(d['input'],palette,r)]
  if not rules:return {'status':'inconsistent_demonstration'}
 outs=[o for r in rules for o in alternatives(query,palette,r)]
 if not outs:return {'status':'no_visible_reading'}
 if any(o!=outs[0] for o in outs):return {'status':'context_shortfall','surviving_mechanisms':rules,'distinct_outputs':len({repr(o) for o in outs})}
 return {'status':'unique','output':outs[0],'surviving_mechanisms':rules}


def require_evidence(demos,queries,palette):
 for x in list(demos)+list(queries):
  inp=x['input'] if isinstance(x,dict) else x
  result=gate(demos,inp,palette)
  if result['status']!='unique':raise MissingColourEvidence(result['status'])
