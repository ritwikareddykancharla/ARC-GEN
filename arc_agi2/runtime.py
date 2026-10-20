"""Load local reference solvers with the helper environment used in their original replay.

Reference code is trusted project data, not an execution service for arbitrary uploads.
All calls have deadlines; canonical and corrected teaching fixtures remain distinct.
"""
import json,signal
from pathlib import Path
import numpy as np
from . import helpers
BASE=Path(__file__).parent

def alarm(*_):raise TimeoutError('reference/generator deadline')
def call(fn,*args,seconds=3,**kwargs):
    old=signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:return fn(*args,**kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
def reference(tid):return json.loads((BASE/'references'/f'{tid}.json').read_text())
def solver(tid):
    r=reference(tid)
    ns={k:v for k,v in vars(helpers).items() if not k.startswith('_')}
    ns.update(np=np,emit=lambda *a,**kw:None,__name__='reference')
    call(exec,compile(r['code'],f'reference/{tid}','exec'),ns)
    return ns['transform']
def verification_solver(tid):
    """Use a documented improved verifier when the archived code is disproven."""
    from .verified_rules import VERIFIERS
    return VERIFIERS[tid] if tid in VERIFIERS else solver(tid)

def verification_basis(tid):
    from .verified_rules import VERIFIER_EVIDENCE
    return VERIFIER_EVIDENCE.get(tid,{'mode':'archived_pair_solver'})

def grid(x):
    a=np.asarray(x)
    if a.ndim!=2 or not all(1<=n<=30 for n in a.shape) or not np.issubdtype(a.dtype,np.integer) or np.any(a<0) or np.any(a>9):
        raise ValueError('Invalid ARC grid')
    return a.astype(int).tolist()
def pairs(task):return task['train']+task['test']
def check_reference(tid):
    r=reference(tid);f=solver(tid);result={}
    for name in ['canonical','teaching_fixture']:
        task=r[name]
        # frozen tasks use the usual train/test schema
        scores=[]
        for p in pairs(task):
            try:scores.append(grid(call(f,p['input']))==p['output'])
            except Exception:scores.append(False)
        result[name]={'correct':sum(scores),'total':len(scores),'all_exact':all(scores)}
    return result
