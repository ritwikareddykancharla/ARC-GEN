import hashlib,json,random,subprocess,types
from pathlib import Path
import pytest
from tasks import task_e74e1818 as task
from arc_agi2.runtime import BASE,reference,verification_solver,grid
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import require_colour_evidence,MissingColourEvidence
from arc_agi2.band_reflection_evidence import variants

REPORT=BASE/'reports/diversity-v1/native-band-reflection'

def test_canonical_replay_and_explicit_legacy_labels():
 assert task.validate()==reference('e74e1818')['canonical']
 old=types.ModuleType('old')
 src=subprocess.check_output(['git','show','e300a93:tasks/task_e74e1818.py'],cwd=BASE.parent)
 exec(src,old.__dict__)
 for i in range(100):
  random.seed(i);p=old.generate();g=p['input']
  assert task.generate(width=len(g[0]),height=len(g),colors=sum(g,[]))==p

@pytest.mark.parametrize('h,w',[(3,3),(3,30),(30,3),(30,30),(8,19),(19,8)])
@pytest.mark.parametrize('symmetric',[False,True])
def test_shapes_rules_and_count_preservation(h,w,symmetric):
 for i in range(10):
  random.seed(i);p=task.generate(height=h,width=w,symmetric=symmetric)
  assert len(p['input'])==h and len(p['input'][0])==w
  assert grid(verification_solver('e74e1818')(p['input']))==p['output']
  assert sorted(sum(p['input'],[]))==sorted(sum(p['output'],[]))
  if symmetric:assert all(row==row[::-1] for row in p['input'])

@pytest.mark.parametrize('kw',[{'height':True},{'width':31},{'height':2},{'num_bands':10},
 {'height':3,'num_bands':2},{'symmetric':1},{'colors':[0]}])
def test_invalid_requests(kw):
 with pytest.raises(ValueError):task.generate(**kw)

def test_dense_checker_witnesses_preserved():
 witnesses=json.loads((REPORT/'archived-checker-failures.json').read_text())
 assert witnesses
 for case in witnesses:
  p=case['pair'];assert grid(verification_solver('e74e1818')(p['input']))==p['output']

def test_symmetric_demos_cannot_identify_asymmetric_query():
 random.seed(991)
 ds=[task.generate(height=h,width=w,num_bands=2,symmetric=True) for h,w in [(7,9),(9,7),(8,10)]]
 q=task.generate(height=10,width=12,num_bands=2,symmetric=False)
 assert variants(q['input'])[1]!=variants(q['input'])[3]
 for d4 in range(8):
  pal=[3,9,0,7,2,8,1,6,4,5]
  demos=[{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in ds]
  query={'input':transformed(q['input'],d4,pal),'output':'not read'}
  with pytest.raises(MissingColourEvidence):require_colour_evidence('e74e1818',demos,[query],pal,d4)
  informative=task.generate(height=11,width=13,num_bands=2,symmetric=False)
  demos[0]={k:transformed(informative[k],d4,pal) for k in ('input','output')}
  require_colour_evidence('e74e1818',demos,[query],pal,d4)

def test_context_audit_and_source_bindings():
 r=json.loads((REPORT/'context-audit.json').read_text())
 assert r['queries']==r['accepted']==500 and r['checks']==4000
 for name,h in r['source_hashes'].items():assert hashlib.sha256((BASE.parent/name).read_bytes()).hexdigest()==h,name
