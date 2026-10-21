"""Independent directed-segment reachability oracle for a demonstrated split threshold."""
from arc_agi2.colour_evidence import MissingColourEvidence

def graph_outputs(g,palette,kmax):
 bg,red=palette[0],palette[2];H,W=len(g),len(g[0]);seed=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==red]
 if len(seed)!=1:raise MissingColourEvidence('One visible ray seed required')
 r,c=seed[0];ds=[]
 if c==0:ds.append((0,1))
 if c==W-1:ds.append((0,-1))
 if r==0:ds.append((1,0))
 if r==H-1:ds.append((-1,0))
 if len(ds)!=1:raise MissingColourEvidence('Seed inward direction ambiguous')
 first=(r,c,*ds[0]);segments={};pending=[first]
 # Construct all reachable segments once. Each edge stores run length; the
 # threshold only removes edges during the separate reachability calculation.
 while pending:
  node=pending.pop()
  if node in segments:continue
  r,c,dr,dc=node;line=[(r,c)];step=1;blocked=False
  while 0<=r+step*dr<H and 0<=c+step*dc<W:
   y,x=r+step*dr,c+step*dc
   if g[y][x] not in (bg,red):blocked=True;break
   line.append((y,x));step+=1
  end=line[-1];targets=[]
  if blocked:
   for turn in (-1,1):targets.append((*end,turn*dc,-turn*dr))
  segments[node]=(line,targets)
  pending.extend(t for t in targets if t not in segments)
 outputs=[]
 for k in range(kmax+1):
  seen=set();queue=[first];paint=set()
  while queue:
   n=queue.pop()
   if n in seen:continue
   seen.add(n);line,targets=segments[n];paint.update(line)
   if n==first or len(line)-1>=k:queue.extend(targets)
  out=[list(map(int,row)) for row in g]
  for y,x in paint:out[y][x]=red
  outputs.append(tuple(map(tuple,out)))
 return outputs

def require_ray_evidence(demos,queries,palette):
 if not demos:raise MissingColourEvidence('No split-threshold demonstrations')
 grids=[d['input'] for d in demos]+[q['input'] for q in queries]
 cap=max(max(len(g),len(g[0])) for g in grids)+1;alive=set(range(cap+1))
 for d in demos:
  expected=tuple(map(tuple,d['output']));preds=graph_outputs(d['input'],palette,cap)
  alive &={k for k,p in enumerate(preds) if p==expected}
 if not alive:raise MissingColourEvidence('No threshold fits every demonstration')
 for q in queries:
  preds=graph_outputs(q['input'],palette,cap)
  if len({preds[k] for k in alive})!=1:raise MissingColourEvidence('Split-threshold alternatives disagree on query')
 return {'surviving_thresholds':sorted(alive)}
