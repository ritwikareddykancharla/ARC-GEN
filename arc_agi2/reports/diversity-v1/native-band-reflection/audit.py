"""Fixed-query, split-matched, canonical-shape context audit; answers excluded from selection."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path
from tasks.task_e74e1818 import generate
from arc_agi2.runtime import BASE,reference,verification_solver,grid
from arc_agi2.episode_shape_policy import profile_from_task,describe
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.finite_input_policy import input_split
from arc_agi2.colour_evidence import require_colour_evidence,MissingColourEvidence
from arc_agi2.program_targets import make_record
from arc_agi2.augmentation import transformed


def main():
 random.seed(2026102510);started=time.monotonic();tid='e74e1818'
 checker=verification_solver(tid);profile=profile_from_task(reference(tid)['canonical'])['patterns'][0]
 results=[];rejections=Counter();checks=0;shapes=set();draws=0
 for i in range(500):
  q=generate();qid=input_orbit(q['input']);split=input_split(qid)
  assert grid(checker(q['input']))==q['output']
  shape=(len(q['input']),len(q['input'][0]));shapes.add(shape);accepted=False
  for attempt in range(64):
   ds=[];seen={qid};ds_shapes=set()
   for draw in range(1000):
    p=generate();draws+=1;h=input_orbit(p['input']);s=(len(p['input']),len(p['input'][0]))
    if h in seen or input_split(h)!=split or s==shape or s in ds_shapes:continue
    assert grid(checker(p['input']))==p['output']
    ds.append(p);seen.add(h);ds_shapes.add(s)
    if len(ds)==3:break
   if len(ds)!=3:
    rejections['split_pool_limit']+=1;continue
   assert describe(ds,q['input'])==profile and len(seen)==4
   pal=list(range(10));random.shuffle(pal)
   try:
    for d4 in range(8):
     demos=[{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in ds]
     query={'input':transformed(q['input'],d4,pal)}
     require_colour_evidence(tid,demos,[query],pal,d4)
   except MissingColourEvidence:
    rejections['ambiguous_demonstrations']+=1;continue
   # Only now read the target for soundness checking, never context selection.
   for d4 in range(8):
    demos=[{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in ds]
    ep=dict(task_id=tid,episode_id=f'band-audit-{i}-{d4}',train=demos,
      test=[{'input':transformed(q['input'],d4,pal)}],solutions=[transformed(q['output'],d4,pal)],
      d4_transform=d4,color_permutation=pal)
    assert make_record(ep)['verification']['all_exact'];checks+=1
   accepted=True;break
  results.append(dict(index=i,accepted=accepted,attempts=attempt+1,input_orbit=qid,split=split))
  if (i+1)%100==0:print(json.dumps(dict(queries=i+1,accepted=sum(r['accepted'] for r in results))),flush=True)
 files=['tasks/task_e74e1818.py','arc_agi2/band_reflection_evidence.py','arc_agi2/colour_evidence.py',
  'arc_agi2/verified_rules.py','arc_agi2/direct_factories/task_e74e1818.py','arc_agi2/direct_factories/e74e1818.json',
  'arc_agi2/program_targets.py','arc_agi2/episode_shape_policy.py','arc_agi2/finite_input_policy.py',
  'arc_agi2/diversity/prepare.py',str(Path(__file__).resolve().relative_to(BASE.parent))]
 out=dict(queries=500,accepted=sum(r['accepted'] for r in results),checks=checks,draws=draws,
  rejections=dict(rejections),shape_profile=profile,query_shapes=len(shapes),results=results,
  seconds=time.monotonic()-started,source_hashes={f:hashlib.sha256((BASE.parent/f).read_bytes()).hexdigest() for f in files},
  limitations='Eight competing readings only; not universal rule identifiability. Query inputs remain fixed.')
 (Path(__file__).parent/'context-audit.json').write_text(json.dumps(out,indent=2)+'\n')
 assert out['accepted']==500 and checks==4000

if __name__=='__main__':main()
