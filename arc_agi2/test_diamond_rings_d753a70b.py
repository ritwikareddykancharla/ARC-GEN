"""Tests of the uncertain concentric teaching hypothesis, not canonical acceptance."""
import unittest
from arc_agi2.runtime import reference
from arc_agi2.augmentation import transformed
from arc_agi2.direct_factories.task_d753a70b import build_program
from arc_agi2.diamond_ring_evidence_d753a70b import require_ring_evidence,ring_readings
from arc_agi2.colour_evidence import MissingColourEvidence
from tasks.task_d753a70b import generate
PAL=list(range(10))
def corrected_pair():
 return generate(rows=[3,4,8,10,15,15],cols=[12,4,10,3,4,13],lengths=[3,0,2,1,1,1],colors=[2,5,8,2,5,9])
class DiamondTests(unittest.TestCase):
 def solve(self,p,pal=PAL):
  ns={};exec(build_program(0,pal),ns);return ns['solve']([],p['input'])
 def test_exactly_ten_disputed_canonical_cells(self):
  original=reference('d753a70b')['canonical']['train'][0];p=corrected_pair()
  self.assertEqual(original['input'],p['input']);self.assertEqual(self.solve(p),p['output'])
  changes=[(r,c) for r,row in enumerate(p['output']) for c,v in enumerate(row) if v!=original['output'][r][c]]
  self.assertEqual(len(changes),10)
  with self.assertRaises(MissingColourEvidence):require_ring_evidence([original],[],PAL)
 def test_other_canonical_pairs(self):
  t=reference('d753a70b')['canonical']
  for p in t['train'][1:]+t['test']:self.assertEqual(self.solve(p),p['output'])
 def test_joined_same_colour_objects(self):
  p=generate(rows=[3,3,10,12],cols=[3,6,10,3],lengths=[1,1,0,0],colors=[2,2,5,9])
  self.assertEqual(self.solve(p),p['output']);require_ring_evidence([], [dict(input=p['input'])],PAL)
 def test_D4_clipping_and_colour_permutation(self):
  pal=[3,9,0,7,2,8,1,6,4,5];p=corrected_pair()
  for d4 in range(8):
   q={k:transformed(p[k],d4,pal) for k in ['input','output']}
   require_ring_evidence([q],[],pal);self.assertEqual(self.solve(q,pal),q['output'])
 def test_query_output_is_ignored_even_if_poisoned(self):
  p=corrected_pair()
  expected=require_ring_evidence([], [{'input':p['input']}],PAL)
  self.assertEqual(require_ring_evidence([], [{'input':p['input'],'output':[[99]]}],PAL),expected)
 def test_query_output_is_never_accessed(self):
  class Query(dict):
   def __getitem__(self,key):
    if key=='output':raise AssertionError('Query label accessed')
    return super().__getitem__(key)
   def __contains__(self,key):
    if key=='output':raise AssertionError('Query label membership checked')
    return super().__contains__(key)
  p=corrected_pair()
  require_ring_evidence([], [Query(input=p['input'],output=[[99]])],PAL)
 def test_isolated_shrinking_dot_invalid(self):
  p=generate(rows=[3,3,10,12],cols=[3,6,10,3],lengths=[1,1,0,0],colors=[2,2,5,9]);p['input'][12][12]=2
  with self.assertRaises(ValueError):self.solve(p)
  with self.assertRaises(MissingColourEvidence):require_ring_evidence([], [dict(input=p['input'])],PAL)
if __name__=='__main__':unittest.main()
