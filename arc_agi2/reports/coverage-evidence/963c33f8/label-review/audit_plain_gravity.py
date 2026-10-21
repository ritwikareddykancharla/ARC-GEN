"""Audit the competing eight-cell plain-gravity interpretation; not native admission."""
import hashlib,json,random,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import audit
source=(HERE.parent/'factory.py').read_text().replace('FLOOR_REACH = 2','FLOOR_REACH = 0')
(HERE/'alternative_eight_cell_factory.py').write_text(source)
factory=audit.load(HERE/'alternative_eight_cell_factory.py','alt963').build_program
native=audit.load(audit.FORK/'tasks/task_963c33f8.py','native963plain')
def plain(g):
 out=[row[:] for row in g];H,W=len(g),len(g[0]);cols=[c for c in range(W) if g[0][c]==9]
 for c in cols:
  for r in range(3):out[r][c]=7
 for c in cols:
  stop=next((r-1 for r in range(3,H) if out[r][c]==5),H-1) if g[2][c]==1 else H-1
  for j in range(3):out[stop-2+j][c]=g[j][c]
 return out
r=dict(task_id='963c33f8',status='alternative plain-gravity eight-cell interpretation; all random inputs retained but labels regenerated; audit-only',passed=False,fresh_pairs_checked=0,augmented_pair_checks=0,fixture_variants_checked=0,native_labels_changed=0)
start=time.monotonic();examples=[]
try:
 task=audit.reference('963c33f8')['teaching_fixture']
 for s in ['train','test']:
  for p in task[s]:assert plain(p['input'])==p['output']
 for pal in [list(range(10)),[3,9,0,7,2,8,1,6,4,5]]:
  for d4 in range(8):
   ep={'train':[{k:audit.transformed(p[k],d4,pal) for k in ['input','output']} for p in task['train']],'test':[{'input':audit.transformed(p['input'],d4,pal)} for p in task['test']],'solutions':[audit.transformed(p['output'],d4,pal) for p in task['test']]}
   src=factory(d4,pal);audit.audit_target('963c33f8',src);audit.verify(src,ep);r['fixture_variants_checked']+=1
 for batch in range(250):
  random.seed(963330000+batch);native_pairs=[audit.call(native.generate,seconds=10) for _ in range(4)]
  pairs=[]
  for p in native_pairs:
   expected=plain(p['input']);pairs.append(dict(input=p['input'],output=expected))
   if expected!=p['output']:
    r['native_labels_changed']+=1
    if len(examples)<5:examples.append(dict(native=p,plain_gravity_output=expected))
  pal=list(range(10));random.Random(batch+963).shuffle(pal)
  for d4 in range(8):
   src=factory(d4,pal);audit.audit_target('963c33f8',src);audit.verify(src,audit.episode(pairs,d4,pal));r['augmented_pair_checks']+=4
  r['fresh_pairs_checked']+=4
 r['passed']=True
except Exception as exc:r['error']=repr(exc)
r['seconds']=time.monotonic()-start
(HERE/'audit-eight-cell-alternative.json').write_text(json.dumps(r,indent=2)+'\n')
(HERE/'native-versus-plain-counterexamples.json').write_text(json.dumps(examples,indent=2)+'\n')
print(json.dumps(r,indent=2))
if not r['passed']:raise SystemExit(1)
