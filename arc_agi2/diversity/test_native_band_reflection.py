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

# Explicit width/height/colors calls are legacy compatibility, not the certified
# random grammar: labels must equal the pre-238f085 generator wherever it
# returned, and ValueError must replace each of its crashes.
def _module(rev):
 m=types.ModuleType('m'+rev)
 exec(subprocess.check_output(['git','show',f'{rev}:tasks/task_e74e1818.py'],cwd=BASE.parent),m.__dict__)
 return m

def _outcome(f,**kw):
 try:return f(**kw)
 except Exception as e:return type(e)

SCENE_5X7=[[0]*5,[0,1,0,0,0],[0,0,1,0,0],[0,2,0,0,0],[0,0,0,1,0],[0,1,0,0,0],[0]*5]
LEGACY_CASES={
 'repeated_nonadjacent_colour':(5,7,sum(SCENE_5X7,[])),
 'repeated_colour_three_runs':(4,7,[0,0,0,0, 0,3,3,0, 0,5,0,0, 0,3,0,0, 0,0,3,0, 0,5,5,0, 0,0,0,0]),
 'ink_in_border_rows':(4,5,[7,0,0,7, 0,1,0,0, 0,0,1,0, 0,2,0,0, 6,6,0,0]),
 'ink_in_border_columns':(4,5,[0,0,0,0, 1,0,0,0, 0,0,0,1, 2,0,0,2, 0,0,0,0]),
 'width_one':(1,5,[0,4,4,9,0]),
 'width_two':(2,4,[0,0, 1,0, 0,1, 0,0]),
 'height_two':(3,2,[1,2,3, 4,5,6]),
 'partial_fill':(3,4,[0,0,0, 0,5,0, 2]),
 'mixed_rows':(4,6,[0,0,0,0, 0,9,8,0, 0,8,9,0, 0,1,2,0, 0,2,0,0, 0,0,0,0]),
}

@pytest.mark.parametrize('name',sorted(LEGACY_CASES))
def test_explicit_legacy_labels_equal_parent_generator(name):
 w,h,cols=LEGACY_CASES[name];old=_module('e300a93')
 expected=old.generate(width=w,height=h,colors=list(cols))
 state=random.getstate()
 assert task.generate(width=w,height=h,colors=list(cols))==expected
 assert random.getstate()==state

def test_legacy_5x7_scene_reflects_each_run_but_lies_outside_certificate():
 got=task.generate(width=5,height=7,colors=sum(SCENE_5X7,[]))['output']
 assert got==[[0]*5,[0,0,1,0,0],[0,1,0,0,0],[0,2,0,0,0],[0,1,0,0,0],[0,0,0,1,0],[0]*5]
 # Documented scope: the coordinate checker reflects each colour's whole row
 # span, which equals per-run reflection only in the random grammar.
 assert grid(verification_solver('e74e1818')(SCENE_5X7))!=got

def test_small_explicit_grammar_matches_parent_including_failures():
 old=_module('e300a93');checked=0
 import itertools
 cases=[(w,h,c) for w in (1,2,3) for h in (2,3) for n in range(w*h+1)
        for c in itertools.product((0,1,2),repeat=n)]
 rng=random.Random(2026)
 for _ in range(2000):
  w,h=rng.randint(1,8),rng.randint(2,8);pal=rng.sample(range(1,10),rng.randint(1,3))
  n=rng.choice([w*h,rng.randint(0,w*h),w*h+1])
  cases.append((w,h,tuple(rng.choice(pal) if rng.random()<.6 else 0 for _ in range(n))))
 for w,h,c in cases:
  a=_outcome(old.generate,width=w,height=h,colors=list(c));b=_outcome(task.generate,width=w,height=h,colors=list(c))
  assert b==(ValueError if isinstance(a,type) else a),(w,h,c,a,b);checked+=1
 assert checked>30000

@pytest.mark.parametrize('w,h,cols',[(3,4,[0,0,0, 0,1,0, 0,0,0, 0,0,0]),(3,3,[0]*10),(3,1,[0,1,0]),
 (0,2,[]),(3,3,[0,0,0,0,10,0,0,0,0]),(3,3,[0,0,0,0,True,0,0,0,0]),(True,3,[1,1,1]),(31,3,[1]*93),(3,3,5)])
def test_explicit_calls_outside_legacy_definition_raise(w,h,cols):
 with pytest.raises(ValueError):task.generate(width=w,height=h,colors=cols)

def test_random_grammar_unchanged_from_238f085():
 head=_module('238f085')
 for seed in range(200):
  for kw in ({},{'symmetric':True},{'height':3,'width':30},{'num_bands':1}):
   random.seed(seed);a=head.generate(**kw);sa=random.getstate()
   random.seed(seed);assert task.generate(**kw)==a and random.getstate()==sa

def test_recertified_record_keeps_history_and_mirror():
 rec=(BASE/'direct_factories/e74e1818.json').read_text()
 assert rec==(BASE/'reports/diversity-v1/native-certificates/e74e1818.json').read_text()
 r=json.loads(rec);old=json.loads((REPORT/'historical-238f085/certificate-e74e1818.json').read_text())
 assert r['constructor_sha256']==hashlib.sha256((BASE.parent/'tasks/task_e74e1818.py').read_bytes()).hexdigest()
 assert r['passed'] and (r['fresh_pairs_checked'],r['augmented_pair_checks'],r['fixture_variants_checked'])==(1000,8000,16)
 for k in ('provenance','draft_notes','draft_notes_status','previous_certificate','previous_domain_limitations'):
  assert r[k]==old[k],k
 assert r['certificate_history'][-1]['constructor_sha256']==old['constructor_sha256']=='1163953c6c859624c01dffa38e91e9e06e7095a24f4fa8c9f5478137d8c61434'
 assert 'not certified' in r['certificate_scope']
