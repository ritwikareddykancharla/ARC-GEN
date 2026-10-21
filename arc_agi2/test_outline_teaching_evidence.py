import importlib,json,unittest
from pathlib import Path
from .augmentation import transformed
from .colour_evidence import MissingColourEvidence
from .outline_teaching_evidence import ring_output,outline_outputs,require_ring_teaching_evidence,require_outline_teaching_evidence

class TeachingOutlineTests(unittest.TestCase):
 def setUp(self):self.pal=list(range(10))
 def ref(self,tid):return json.loads((Path(__file__).parent/'references'/f'{tid}.json').read_text())
 def test_labelled_copies_pass_canonical_rejected(self):
  for tid,gate in [('a3f84088',require_ring_teaching_evidence),('d931c21c',require_outline_teaching_evidence)]:
   ref=self.ref(tid);t=ref['teaching_fixture'];gate(t['train'],[p['input'] for p in t['test']],self.pal)
   with self.assertRaises(MissingColourEvidence):gate(ref['canonical']['train'],[p['input'] for p in t['test']],self.pal)
 def test_no_demonstrations_rejected(self):
  for gate in (require_ring_teaching_evidence,require_outline_teaching_evidence):
   with self.assertRaises(MissingColourEvidence):gate([],[],self.pal)
 def test_ring_rule_independent_of_canvas_size(self):
  from tasks.task_a3f84088 import generate
  p=generate(size=13,width=9,row=1,col=1);out=ring_output(p['input'],self.pal)
  self.assertEqual(out[5][5],5);self.assertEqual(p['output'][5][5],5)
  self.assertEqual(self.ref('a3f84088')['canonical']['train'][3]['output'][5][5],0)
  p2=generate(size=14,width=9,row=1,col=1);self.assertEqual(out,[row[:13] for row in ring_output(p2['input'],self.pal)[:13]])
 def test_seam_mechanisms_need_demonstration(self):
  # Union of offset rectangles with a seam >=3 cells long.
  inside={(r,c) for r in range(2,7) for c in range(2,4)}|{(r,c) for r in range(3,8) for c in range(4,7)}
  wall={(r+dr,c+dc) for r,c in inside for dr in (-1,0,1) for dc in (-1,0,1)}-inside
  g=[[int((r,c) in wall) for c in range(10)] for r in range(11)]
  candidates=outline_outputs(g,self.pal);self.assertNotEqual(candidates['pieces'],candidates['touch'])
  t=self.ref('d931c21c')['teaching_fixture']
  with self.assertRaises(MissingColourEvidence):require_outline_teaching_evidence(t['train'],[g],self.pal)
  demo={'input':g,'output':candidates['pieces']};require_outline_teaching_evidence([demo],[g],self.pal)
  module=importlib.import_module('arc_agi2.direct_factories.task_d931c21c');ns={};exec(module.build_program(0,self.pal),ns)
  with self.assertRaises(ValueError):ns['solve'](t['train'],g)
  self.assertEqual(ns['solve']([demo],g),candidates['pieces'])
 def test_query_answer_ignored_and_colours_demonstrated(self):
  for tid,gate in [('a3f84088',require_ring_teaching_evidence),('d931c21c',require_outline_teaching_evidence)]:
   t=self.ref(tid)['teaching_fixture']
   gate(t['train'],[{'input':p['input'],'output':[['POISON']]} for p in t['test']],self.pal)
  t=self.ref('d931c21c')['teaching_fixture']
  with self.assertRaises(MissingColourEvidence):require_outline_teaching_evidence([t['train'][1]],[{'input':t['train'][0]['input']}],self.pal)
 def test_source_d4_independence(self):
  for tid in ('a3f84088','d931c21c'):
   f=importlib.import_module('arc_agi2.direct_factories.task_'+tid)
   self.assertEqual(f.build_program(0,self.pal),f.build_program(7,self.pal))

if __name__=='__main__':unittest.main()
