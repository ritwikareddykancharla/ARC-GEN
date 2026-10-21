import unittest,importlib.util,json,sys
from pathlib import Path
F=Path(__file__).resolve().parents[1];H=F/'arc_agi2';sys.path.insert(0,str(F))
from arc_agi2.runtime import reference
from arc_agi2.augmentation import transformed

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
factory=load(H/'direct_factories/task_e048c9ed.py','factory').build_program;G=load(H/'bar_length_hypothesis_evidence.py','gate');tid='e048c9ed'
C=reference(tid)['canonical'];ID=list(range(10))
# Exercise both scoped mechanisms using original canonical context and a
# uniformly generated context. This creates no teaching-label file or changes.
native_context=load(F/'tasks'/f'task_{tid}.py','native_context')
_original_generate=native_context.generate
def _uniform_generate(**kw):
 if tid=='e048c9ed':kw.pop('extra',None)
 elif kw.get('extra_colors'):
  rows=list(zip(kw['extra_rows'],kw['extra_cols'],kw['extra_colors'],kw['extra_grids']))
  rows=[x for x in rows if x[3]]
  for key,i in [('extra_rows',0),('extra_cols',1),('extra_colors',2),('extra_grids',3)]:kw[key]=[x[i] for x in rows]
 return _original_generate(**kw)
native_context.generate=_uniform_generate
try:T=native_context.validate()
finally:native_context.generate=_original_generate
def solve(d=0,p=ID):
 ns={};exec(factory(d,p),ns);return ns['solve']
class Tests(unittest.TestCase):
 def test_uniform_native_context_exact(self):
  for p in T['train']+T['test']:self.assertEqual(solve()(T['train'],p['input']),p['output'])
 def test_original_context_exact(self):
  for p in C['train']+C['test']:
   self.assertEqual(solve()(C['train'],p['input']),p['output'])
   self.assertEqual(G.gate(C['train'],p['input'],ID)['output'],p['output'])
 def test_no_hidden_d4_selection(self):
  for d in range(8):
   for p in T['test']:self.assertEqual(solve(d)(T['train'],p['input']),p['output'])
 def test_all_d4_and_palette(self):
  pal=[3,9,0,7,2,8,1,6,4,5]
  for d in range(8):
   ds=[{k:transformed(p[k],d,pal) for k in ['input','output']} for p in T['train']]
   for p in T['test']:
    qi=transformed(p['input'],d,pal);qo=transformed(p['output'],d,pal)
    self.assertEqual(solve(d,pal)(ds,qi),qo);self.assertEqual(G.gate(ds,qi,pal)['output'],qo)
 def test_bad_demo_not_skipped(self):
  ds=json.loads(json.dumps(T['train']));ds[0]['output'][0][0]=(ds[0]['output'][0][0]+1)%10
  self.assertIsNone(solve()(ds,T['test'][0]['input']))
 def test_invalid_blank_rejected(self):self.assertIsNone(solve()(T['train'],[[0]*10 for _ in range(10)]))
 def test_query_label_poison_ignored(self):
  ds=[dict(p,query_output=[[99]],hidden_d4=7) for p in T['train']]
  for p in T['test']:self.assertEqual(solve()(ds,p['input']),p['output'])
 def test_repeated_baseline_tie_abstains(self):
  native=load(F/'tasks/task_e048c9ed.py','native_e')
  q=native.generate(width=12,height=10,gcol=8,offset=1,bcols=[0]*5,lengths=[2,2,3,3,5],colors=[1,2,3,4,7])
  self.assertIsNone(solve()(C['train'],q['input']))
  gg=G.gate(C['train'],q['input'],ID);self.assertEqual(gg['status'],'context_shortfall');self.assertGreater(gg['distinct_outputs'],1)
  self.assertEqual(solve()(T['train'],q['input']),q['output'])
 def test_marker_inclusion_rival_is_disclosed(self):
  for p in C['test']:
   self.assertEqual(G.gate(C['train'],p['input'],ID,include_marker_rival=True)['status'],'context_shortfall')
 def test_contradictory_mechanism_evidence_rejected(self):
  self.assertIsNone(solve()(C['train']+[T['train'][2]],C['test'][0]['input']))
 def test_gate_ignores_query_output_fields(self):
  q=C['test'][0]['input']
  G.require_evidence(C['train'],[{'input':q,'output':[[99]],'solutions':[[88]]}],ID)
  self.assertEqual(G.gate(C['train'],q,ID)['output'],C['test'][0]['output'])
if __name__=='__main__':unittest.main()
