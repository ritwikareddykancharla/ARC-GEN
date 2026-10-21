"""Audit only. Proposed generator labels, original canonical fixtures. No admission."""
import hashlib,json,random,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import audit
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=audit.load(HERE/'native_constructor_before.py','native935')
proposed=audit.load(HERE/'proposed_constructor.py','proposed935')
factory=audit.load(HERE.parent/'factory.py','factory935').build_program

def independent(grid):
    """Set-perimeter drawing: independent of the target's distance-mask algorithm."""
    out=[r[:] for r in grid];H,W=len(grid),len(grid[0])
    legend=grid[0][:max(i for i,x in enumerate(grid[0]) if x!=0)+1]
    seed=[(r,c) for r in range(2,H) for c in range(W) if grid[r][c]!=0]
    assert len(seed)==1
    r,c=seed[0]
    for k,col in enumerate(legend):
        perimeter={(r-k,x) for x in range(c-k,c+k+1)}|{(r+k,x) for x in range(c-k,c+k+1)}|{(y,c-k) for y in range(r-k,r+k+1)}|{(y,c+k) for y in range(r-k,r+k+1)}
        inside={(y,x) for y,x in perimeter if 2<=y<H and 0<=x<W}
        for y,x in inside:out[y][x]=col
        if len(inside)!=len(perimeter):out[0][k]=5
    return out

def diffs(a,b):return [dict(row=r,col=c,old=x,new=b[r][c]) for r,row in enumerate(a) for c,x in enumerate(row) if x!=b[r][c]]

r=dict(task_id='9356391f',status='audit-only proposed constructor; canonical unchanged; not admitted',fresh_pairs_checked=0,augmented_pair_checks=0,fixture_variants_checked=0,native_label_changes=0,input_changes=0,passed=False,factory_sha256=sha(HERE.parent/'factory.py'),native_constructor_sha256=sha(Path(native.__file__)),proposed_constructor_sha256=sha(Path(proposed.__file__)))
start=time.monotonic();seen=set();witnesses=[]
try:
 task=audit.reference('9356391f')['canonical']
 assert proposed.validate()==task
 for split in ['train','test']:
  for p in task[split]:assert independent(p['input'])==p['output']
 for pal in [list(range(10)),[3,9,0,7,2,8,1,6,4,5]]:
  for d4 in range(8):
   ep={'train':[{k:audit.transformed(p[k],d4,pal) for k in ['input','output']} for p in task['train']],'test':[{'input':audit.transformed(p['input'],d4,pal)} for p in task['test']],'solutions':[audit.transformed(p['output'],d4,pal) for p in task['test']]}
   source=factory(d4,pal);audit.audit_target('9356391f',source);audit.verify(source,ep);r['fixture_variants_checked']+=1
 for batch in range(250):
  pairs=[]
  for i in range(4):
   seed=935639100+4*batch+i
   random.seed(seed);old=audit.call(native.generate,seconds=5)
   random.seed(seed);new=audit.call(proposed.generate,seconds=5)
   assert old['input']==new['input'];assert independent(new['input'])==new['output']
   delta=diffs(old['output'],new['output'])
   if delta:
    r['native_label_changes']+=1
    if len(witnesses)<12:witnesses.append(dict(seed=seed,native=old,proposed=new,differences=delta))
   pairs.append(new);seen.add(json.dumps(new['input']))
  pal=list(range(10));random.Random(batch+935).shuffle(pal)
  for d4 in range(8):
   source=factory(d4,pal);audit.audit_target('9356391f',source);audit.verify(source,audit.episode(pairs,d4,pal));r['augmented_pair_checks']+=4
  r['fresh_pairs_checked']+=4
 # Deliberately separate competing hypotheses: seed-column gray vs clipping gray.
 counters=[]
 for params in [dict(colors=[2,3,4,8],row=9,col=3),dict(colors=[2,3,4,8],row=13,col=6),dict(colors=[2,3,4,8],row=9,col=2)]:
  p=proposed.generate(**params);o=native.generate(**params)
  counters.append(dict(parameters=params,native=o,proposed=p,clipping_swatches=[d['col'] for d in diffs(o['output'],p['output'])],seed_column_hypothesis_would_modify=params['col'] if params['col']<len(params['colors']) else None))
 (HERE/'counterfactual-hypotheses.json').write_text(json.dumps(counters,indent=2)+'\n')
 r['passed']=True
except Exception as exc:r['error']=repr(exc)
r.update(unique_base_inputs=len(seen),seconds=time.monotonic()-start)
(HERE/'native-label-counterexamples.json').write_text(json.dumps(witnesses,indent=2)+'\n')
(HERE/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if not r['passed']:raise SystemExit(1)
