"""Batch-2 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Counts native 782b5218 inputs with a column lacking red, and compares the factory top-edge flood with native outputs (3000 seeded draws).
"""
import sys, random
sys.path.insert(0,'.')
from tasks import task_782b5218 as m
import importlib.util
spec=importlib.util.spec_from_file_location('f','arc_agi2/direct_factories/task_782b5218.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
ns={}; exec(f.build_program(0,list(range(10))), ns)
random.seed(0); N=3000; miss=0; dis=0; ex=0
for _ in range(N):
    p=m.generate(); g=p['input']
    if any(all(g[r][c]!=2 for r in range(10)) for c in range(10)): miss+=1
    try:
        o=ns['_apply'](g,'top').tolist()
        if o!=p['output']: dis+=1
    except Exception as e: ex+=1
print('cols_without_red',miss,'factory_top_disagree',dis,'exceptions',ex,'of',N)
