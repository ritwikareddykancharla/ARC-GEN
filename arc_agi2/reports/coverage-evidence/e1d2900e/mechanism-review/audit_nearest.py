"""Proposed input-preserving nearest-square constructor, original fixtures, strict gate."""
import hashlib,json,random,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import audit
from arc_agi2.nearest_square_evidence import nearest_predictions,require_nearest_square_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
factory=audit.load(HERE.parent/'factory.py','nearestfactory').build_program
native=audit.load(HERE/'native_constructor_before.py','nearestnative')
proposed=audit.load(HERE/'proposed_constructor.py','nearestproposed')
atlas=audit.load(HERE.parent/'independent-atlas/solutions.py','nearestindependent')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=dict(task_id='e1d2900e',passed=False,scope='Proposed constructor labels, unchanged native inputs and canonical fixtures; no admission',fresh_pairs_checked=0,augmented_pair_checks=0,fixture_variants_checked=0,context_retries=0,native_output_changes=0,input_comparisons=0,input_changes=0,query_tie_disagreement=0,sampler_rejections=[],factory_sha256=sha(HERE.parent/'factory.py'),native_constructor_sha256=sha(Path(native.__file__)),proposed_constructor_sha256=sha(Path(proposed.__file__)))
start=time.monotonic();seen=set();witnesses=[];weak=[];counter=0

def draw():
 global counter
 seed=882200000+counter;counter+=1
 random.seed(seed);old=audit.call(native.generate,seconds=15)
 random.seed(seed);p=audit.call(proposed.generate,seconds=15)
 r['input_comparisons']+=1
 assert old['input']==p['input'];assert p['output']==atlas.solve(p['input'])
 if old['output']!=p['output']:
  r['native_output_changes']+=1
  if len(witnesses)<8:witnesses.append(dict(seed=seed,native=old,proposed=p))
 return p
try:
 task=audit.reference('e1d2900e')['canonical'];assert proposed.validate()==task
 for pal in [list(range(10)),[3,9,0,7,2,8,1,6,4,5]]:
  for d4 in range(8):
   ep={'train':[{k:audit.transformed(p[k],d4,pal) for k in ['input','output']} for p in task['train']],'test':[{'input':audit.transformed(p['input'],d4,pal)} for p in task['test']],'solutions':[audit.transformed(p['output'],d4,pal) for p in task['test']]}
   src=factory(d4,pal);audit.audit_target('e1d2900e',src);require_nearest_square_evidence(ep['train'],ep['test'],pal);audit.verify(src,ep);r['fixture_variants_checked']+=1
 for i in range(250):
  query=draw()
  if len(set(nearest_predictions(query['input'],list(range(10)))))>1:r['query_tie_disagreement']+=1
  for retry in range(500):
   demos=[draw() for _ in range(3)]
   try:require_nearest_square_evidence(demos,[{'input':query['input']}],list(range(10)))
   except MissingColourEvidence:
    r['context_retries']+=1
    if len(weak)<5:weak.append(dict(query=query,demonstrations=demos,reason='Surviving tie orders disagree'))
    continue
   break
  else:raise RuntimeError('No informative context for fixed query')
  pairs=demos+[query];pal=list(range(10));random.Random(i).shuffle(pal)
  for d4 in range(8):
   ep=audit.episode(pairs,d4,pal);src=factory(d4,pal);audit.audit_target('e1d2900e',src);require_nearest_square_evidence(ep['train'],ep['test'],pal);audit.verify(src,ep);r['augmented_pair_checks']+=4
  r['fresh_pairs_checked']+=4;seen.update(json.dumps(p['input']) for p in pairs)
 r['passed']=True
except Exception as e:
 r['error']=repr(e)
 if 'ep' in globals():(HERE/'audit-failure.json').write_text(json.dumps(ep,indent=2)+'\n')
r.update(unique_base_inputs=len(seen),seconds=time.monotonic()-start)
for name,data in [('audit',r),('native-label-counterexamples',witnesses),('unresolved-context-examples',weak)]:
 (HERE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(r,indent=2))
if not r['passed']:raise SystemExit(1)
