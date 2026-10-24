"""Reproduce the dense-scene checker discrepancy without changing labels."""
import hashlib,json,random
from pathlib import Path
from collections import Counter
from tasks.task_e74e1818 import generate
from arc_agi2.runtime import BASE,solver,verification_solver,grid
from arc_agi2.direct_factories.task_e74e1818 import build_program
ns={};exec(build_program(0,list(range(10))),ns)
old=solver('e74e1818');new=verification_solver('e74e1818');bad=[];shapes=set()
for seed in range(2000):
 random.seed(seed);p=generate();shapes.add((len(p['input']),len(p['input'][0])))
 assert grid(new(p['input']))==p['output']==ns['solve']([],p['input'])
 got=grid(old(p['input']))
 if got!=p['output']:
  counts=Counter(sum(p['input'],[]))
  bad.append(dict(seed=seed,pair=p,archived_prediction=got,colour_counts=dict(counts),modal_colour=counts.most_common(1)[0][0]))
files=['tasks/task_e74e1818.py','arc_agi2/verified_rules.py','arc_agi2/direct_factories/task_e74e1818.py','arc_agi2/references/e74e1818.json']
out=Path(__file__).parent
(out/'archived-checker-failures.json').write_text(json.dumps(bad,indent=2)+'\n')
r=dict(seeds=[0,1999],queries=2000,shapes=len(shapes),archived_failures=len(bad),registered_failures=0,factory_failures=0,
 source_hashes={f:hashlib.sha256((BASE.parent/f).read_bytes()).hexdigest() for f in files})
(out/'checker-comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
