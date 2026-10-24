"""Reproduce expanded shift-domain and fixed-query context evidence."""
import hashlib, json, random, subprocess
from collections import Counter
from pathlib import Path
from tasks.task_6d1d5c90 import generate
from arc_agi2.runtime import BASE, reference
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.colour_evidence import require_colour_evidence,MissingColourEvidence
from arc_agi2.program_targets import make_record
from arc_agi2.augmentation import transformed

seed=2026102503
random.seed(seed)
counts=Counter(); shapes=set(); examples={}; queries=[]
for i in range(1000):
 p=generate();shapes.add((len(p['input']),len(p['input'][0])))
 n=len({c for row in p['input'] for c in row});counts[n]+=1
 examples.setdefault(n,p)
 if i<500:queries.append(p)
results=[]; modes=Counter()
for index,q in enumerate(queries):
 h,w=len(q['input']),len(q['input'][0])-1
 qid=input_orbit(q['input']); failures=Counter();accepted=False
 # Query is fixed; only demonstrations are resampled. Never examine query
 # answer to decide which context to accept.
 for attempt in range(100):
  demos=[generate(height=h,width=w) for _ in range(3)]
  identities=[qid]+[input_orbit(p['input']) for p in demos]
  if len(set(identities))!=4:
   failures['duplicate_context_identity']+=1;continue
  pal=list(range(10));random.shuffle(pal);d4=random.randrange(8)
  ds=[{k:transformed(g,d4,pal) for k,g in p.items()} for p in demos]
  qi=transformed(q['input'],d4,pal)
  try:require_colour_evidence('6d1d5c90',ds,[{'input':qi}],pal,d4)
  except MissingColourEvidence:
   failures['ambiguous_context']+=1;continue
  ep={'episode_id':f'native-h-{index:05d}','task_id':'6d1d5c90','train':ds,'test':[{'input':qi}],
      'solutions':[transformed(q['output'],d4,pal)],'d4_transform':d4,'color_permutation':pal}
  record=make_record(ep,source_repo='ritwikareddykancharla/ARC-GEN',source_revision='native-h-audit')
  assert record['verification']['all_exact'];accepted=True;break
 results.append({'query_index':index,'shape':[h,w+1],'accepted':accepted,'attempts':attempt+1,'failures':dict(failures)})
 modes.update(failures)
files=['tasks/task_6d1d5c90.py','arc_agi2/marker_roll_evidence.py','arc_agi2/colour_evidence.py','arc_agi2/direct_factories/task_6d1d5c90.py','arc_agi2/program_targets.py']
report={'seed':seed,'pair_draws':1000,'unique_shapes':len(shapes),'shapes':sorted(shapes),
 'used_input_colours':dict(sorted(counts.items())),'canonical_input_colours':[len({c for row in p['input'] for c in row}) for p in reference('6d1d5c90')['canonical']['train']+reference('6d1d5c90')['canonical']['test']],
 'fixed_queries':500,'accepted_queries':sum(r['accepted'] for r in results),'failures':dict(modes),'queries':results,
 'source_hashes':{f:hashlib.sha256((BASE.parent/f).read_bytes()).hexdigest() for f in files},
 'limits':'Finite affine marker-shift hypothesis class, not universal identifiability. Shape-specific orbit capacity can limit four-distinct-input episodes. Explicit supplied legacy colours preserve labels. No query-answer selection.'}
out=Path(__file__).parent/'audit.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['queries','shapes','source_hashes']}))
