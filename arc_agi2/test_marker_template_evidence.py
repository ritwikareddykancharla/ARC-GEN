import importlib.util,json,sys,unittest
from pathlib import Path
F=Path(__file__).resolve().parents[1];H=F/'arc_agi2';sys.path.insert(0,str(F))
from arc_agi2.runtime import reference
from arc_agi2.augmentation import transformed

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
B=load(H/'direct_factories/task_ac0c5833.py','factory').build_program;G=load(H/'marker_template_evidence.py','gate');N=load(F/'tasks/task_ac0c5833.py','native')
C=reference('ac0c5833')['canonical'];ID=list(range(10))
PARAMS=dict(size=25,length=3,shown=1,brows=[2,5,13,19],bcols=[15,3,12,5],angles=[0,0,3,2],pattern='222202222')
PLAIN=N.generate(**PARAMS)
def solver(d=0,p=ID):
 ns={};exec(B(d,p),ns);return ns['solve']
class Tests(unittest.TestCase):
 def test_original_all16(self):
  for pal in [ID,[3,9,0,7,2,8,1,6,4,5]]:
   for d in range(8):
    ds=[{k:transformed(p[k],d,pal) for k in ['input','output']} for p in C['train']]
    for p in C['train']+C['test']:
     qi=transformed(p['input'],d,pal);qo=transformed(p['output'],d,pal)
     self.assertEqual(solver(d,pal)(ds,qi),qo);self.assertEqual(G.gate(ds,qi,pal)['output'],qo)
 def test_native_ring_not_always_trimmed(self):
  self.assertEqual(PLAIN['input'],C['train'][2]['input']);self.assertNotEqual(PLAIN['output'],C['train'][2]['output'])
  self.assertEqual(solver()([PLAIN],PLAIN['input']),PLAIN['output'])
  self.assertEqual(solver()(C['train'],PLAIN['input']),C['train'][2]['output'])
 def test_missing_hollow_evidence_abstains(self):
  ds=C['train'][:2];q=PLAIN['input']
  self.assertIsNone(solver()(ds,q));self.assertEqual(G.gate(ds,q,ID)['status'],'context_shortfall')
 def test_query_label_poison_does_not_select(self):
  for label in [PLAIN['output'],C['train'][2]['output'],[[99]]]:
   with self.assertRaises(ValueError):G.require_evidence(C['train'][:2],[{'input':PLAIN['input'],'output':label}],ID)
 def test_contradictory_demos_rejected(self):
  ds=C['train']+[PLAIN];self.assertIsNone(solver()(ds,PLAIN['input']));self.assertEqual(G.gate(ds,PLAIN['input'],ID)['status'],'inconsistent_demonstration')
 def test_source_independent_of_d4(self):self.assertEqual(len({B(d,ID) for d in range(8)}),1)
 def test_old_overlap_regression(self):
  e=json.loads((H/'reports/ac0c5833-original-regression.json').read_text());ep=e['episode'];s=solver(e['d4'],e['palette'])
  for p in ep['train']:self.assertEqual(s(ep['train'],p['input']),p['output'])
  for p,o in zip(ep['test'],ep['solutions']):self.assertEqual(s(ep['train'],p['input']),o)
 def test_unexplained_marker_rejected(self):
  q=[r[:] for r in C['test'][0]['input']];q[0][0]=4
  self.assertIsNone(solver()(C['train'],q));self.assertEqual(G.gate(C['train'],q,ID)['status'],'no_visible_reading')
 def test_missing_template_rejected(self):
  q=[[0 if v==2 else v for v in row] for row in C['test'][0]['input']]
  self.assertIsNone(solver()(C['train'],q))
 def test_corrupt_demo_not_skipped(self):
  ds=json.loads(json.dumps(C['train']));ds[0]['output'][0][0]=7
  self.assertIsNone(solver()(ds,C['test'][0]['input']))
 def test_two_geometric_owners_rejected(self):
  q=[[0]*25 for _ in range(25)]
  for r in range(10,13):
   for c in range(10,13):
    if r in (10,12) or c in (10,12):q[r][c]=2
  for r,c in [(12,14),(14,12),(14,14),(8,8),(8,10),(10,8)]:q[r][c]=4
  self.assertIsNone(solver()(C['train'],q));self.assertEqual(G.gate(C['train'],q,ID)['status'],'no_visible_reading')
if __name__=='__main__':unittest.main()
