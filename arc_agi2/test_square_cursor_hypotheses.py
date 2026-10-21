import unittest, json, importlib
from pathlib import Path
from .colour_evidence import MissingColourEvidence

def reference(tid):
 return json.loads((Path(__file__).parent/'references'/(tid+'.json')).read_text())

class ContextHypothesisTests(unittest.TestCase):
 def setUp(self):
  self.pal=list(range(10));self.f={};self.e={};self.ns={}
  for tid in ('b1986d4b','dd2401ed'):
   self.f[tid]=importlib.import_module('arc_agi2.direct_factories.task_'+tid)
   self.e[tid]=importlib.import_module('arc_agi2.'+{'b1986d4b':'square_stack_hypothesis_evidence','dd2401ed':'cursor_recolour_evidence'}[tid])
   ns={};exec(self.f[tid].build_program(0,self.pal),ns);self.ns[tid]=ns
 def test_both_canonical_and_poisoned_query(self):
  for tid in self.f:
   task=reference(tid)['canonical'];query=task['test'][0]
   self.e[tid].require_evidence(task['train'],[{'input':query['input'],'output':[['POISON']]}],self.pal)
   self.assertEqual(self.ns[tid]['solve'](task['train'],query['input']),query['output'])
 def test_square_cap_requires_discriminating_demonstration(self):
  from tasks.task_b1986d4b import generate
  def pair(n):
   return generate(width=25,height=25,colors=[0,9,1,2,3],brows=[1,1,8,8]+[15]*n,bcols=[1,10,1,10]+list(range(1,1+4*n,4)),sizes=[4,4,3,3]+[2]*n,backdrop=[0]*625)
  demo=pair(2);query=pair(5);tid='b1986d4b';source=self.ns[tid]
  with self.assertRaises(MissingColourEvidence):self.e[tid].require_evidence([demo],[{'input':query['input']}],self.pal)
  with self.assertRaises(ValueError):source['solve']([demo],query['input'])
  self.e[tid].require_evidence([demo,query],[{'input':query['input']}],self.pal)
  self.assertEqual(source['solve']([demo,query],query['input']),query['output'])
 def test_even_cursor_query_requires_disambiguation(self):
  from tasks.task_dd2401ed import generate
  def pair(even):
   colors=[0]*105
   for r,c in [(0,0),(1,3),(2,9)]+([(3,1)] if even else []):colors[15*r+c]=1
   return generate(cursor=2,extra=0,colors=colors)
  demo=pair(False);query=pair(True);tid='dd2401ed'
  with self.assertRaises(MissingColourEvidence):self.e[tid].require_evidence([demo],[{'input':query['input']}],self.pal)
  with self.assertRaises(ValueError):self.ns[tid]['solve']([demo],query['input'])
  self.e[tid].require_evidence([query],[{'input':query['input']}],self.pal)
  self.assertEqual(self.ns[tid]['solve']([query],query['input']),query['output'])
 def test_minority_background_and_unobservable_role_twins(self):
  from tasks.task_b1986d4b import generate
  backdrop=[8 if r%2==0 and c%2==0 else 9 for r in range(25) for c in range(25)]
  kwargs=dict(width=25,height=25,brows=[2,10,18],bcols=[2,10,18],sizes=[4,3,2],backdrop=backdrop)
  a=generate(colors=[8,9,1,2,3],**kwargs);b=generate(colors=[9,8,1,2,3],**kwargs)
  self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])
  tid='b1986d4b'
  with self.assertRaises(ValueError):self.ns[tid]['_features'](a['input'])
  with self.assertRaises(ValueError):self.e[tid].features(a['input'])
  # One visible background block removes the ambiguity without majority voting.
  for r in (0,1):
   for c in (0,1):backdrop[25*r+c]=8
  a=generate(colors=[8,9,1,2,3],**kwargs)
  self.assertGreater(sum(row.count(9) for row in a['input']),sum(row.count(8) for row in a['input']))
  self.assertEqual(self.ns[tid]['_features'](a['input'])[0],8)
  self.assertEqual(self.e[tid].features(a['input'])[0],8)
  self.assertEqual(self.ns[tid]['solve']([a],a['input']),a['output'])
 def test_orientation_not_factory_oracle(self):
  for tid,f in self.f.items():self.assertEqual(f.build_program(0,self.pal),f.build_program(7,self.pal))
 def test_no_demo_or_bad_label_rejected(self):
  for tid in self.f:
   task=reference(tid)['canonical'];g=task['test'][0]['input']
   with self.assertRaises(MissingColourEvidence):self.e[tid].require_evidence([], [{'input':g}],self.pal)
   with self.assertRaises(MissingColourEvidence):self.e[tid].require_evidence([{'input':task['train'][0]['input'],'output':[[9]]}],[{'input':g}],self.pal)

if __name__=='__main__':unittest.main()
