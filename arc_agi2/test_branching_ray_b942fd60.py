import unittest,sys,random
from pathlib import Path
from arc_agi2 import branching_ray_evidence_b942fd60 as E
from arc_agi2.direct_factories.task_b942fd60 import build_program as factory
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.runtime import reference
from arc_agi2.augmentation import transformed
from tasks import task_b942fd60 as native
class ThresholdTests(unittest.TestCase):
 def solve(self,demos,q,pal=list(range(10))):
  ns={};exec(factory(0,pal),ns);return ns['solve'](demos,q)
 def test_canonical_original_all_pairs(self):
  t=reference('b942fd60')['canonical']
  for p in t['train']+t['test']:self.assertEqual(self.solve(t['train'],p['input']),p['output'])
 def test_no_fallback(self):
  t=reference('b942fd60')['canonical'];q=t['test'][0]['input']
  with self.assertRaises(ValueError):self.solve([],q)
  d=dict(input=q,output=[[0]*len(q[0]) for _ in q])
  with self.assertRaises(ValueError):self.solve([d],q)
 def test_weak_context_rejected(self):
  t=reference('b942fd60')['canonical'];weak=[t['train'][3]];q=t['train'][1]['input']
  with self.assertRaises(ValueError):self.solve(weak,q)
  with self.assertRaises(MissingColourEvidence):E.require_ray_evidence(weak,[dict(input=q)],list(range(10)))
 def test_demonstrated_threshold_changes_answer(self):
  t=reference('b942fd60')['canonical'];q=t['train'][1]['input']
  p=native.generate(width=12,height=12,colors=[v for row in q for v in row])
  self.assertNotEqual(p['output'],t['train'][1]['output'])
  self.assertEqual(self.solve([p],q),p['output'])
  self.assertEqual(self.solve(t['train'],q),t['train'][1]['output'])
 def test_D4_and_palette(self):
  t=reference('b942fd60')['canonical'];pal=[3,9,0,7,2,8,1,6,4,5]
  for d4 in range(8):
   demos=[{k:transformed(p[k],d4,pal) for k in ['input','output']} for p in t['train']]
   q=transformed(t['test'][0]['input'],d4,pal);expected=transformed(t['test'][0]['output'],d4,pal)
   E.require_ray_evidence(demos,[dict(input=q)],pal);self.assertEqual(self.solve(demos,q,pal),expected)
if __name__=='__main__':unittest.main()
