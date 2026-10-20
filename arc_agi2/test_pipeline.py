import json,random,tempfile,unittest
from collections import Counter
from pathlib import Path
import pyarrow.parquet as pq
from . import build_million as b
from .generators.extended import GENERATORS,generate
from .runtime import solver,call,grid,check_reference

class GeneratorTests(unittest.TestCase):
    def test_original_and_independent_construction(self):
        for tid in GENERATORS:
            self.assertTrue(check_reference(tid)['canonical']['all_exact'],tid)
            solve=solver(tid)
            for s in range(20):
                p=generate(tid,s)
                self.assertEqual(p['output'],grid(call(solve,p['input'])),(tid,s))
    def test_split_is_invariant_to_rotations_and_colour_renaming(self):
        g=[[0,1,1],[2,0,3]];canonical=b.canonical_input(g)
        for d in range(8):
            palette=list(range(10));random.Random(d).shuffle(palette)
            self.assertEqual(canonical,b.canonical_input(b.transformed(g,d,palette)))
    def test_finite_capacity_and_missing_sizes_are_not_fabricated(self):
        rs=[{'task_id':'a','train_canonical':5,'train_strata':{'15|same_shape':5}}]
        alloc,stats=b.allocate(rs,'train',100,{'15|same_shape':1,'30|same_shape':1})
        self.assertEqual(sum(alloc['a'].values()),10)
        self.assertEqual(stats['shortfall_by_stratum']['30|same_shape'],50)
    def test_episode_contract_and_disjoint_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=b.OUT;b.OUT=Path(directory);(b.OUT/'pools').mkdir()
            try:
                tid='f931b4a8';rows=[]
                for s in range(300):
                    p=generate(tid,s);c=b.canonical_input(p['input']);split='validation' if int(c[:8],16)%20==0 else 'train'
                    rows.append(dict(task_id=tid,**p,seed=s,parameters='{}',generator_mode='extension',input_hash=b.digest(p['input']),canonical_input_hash=c,split=split,stratum=b.stratum(p)))
                pq.write_table(b.pa.Table.from_pylist(rows),b.OUT/'pools'/f'{tid}.parquet')
                alloc={split:dict(Counter(r['stratum'] for r in rows if r['split']==split)) for split in ['train','validation']}
                report=b.make_episodes((tid,alloc));used={}
                for split in ['train','validation']:
                    self.assertGreater(report['splits'][split]['episodes'],0)
                    saved=pq.read_table(b.OUT/'data'/split/f'{tid}.parquet').to_pylist();used[split]=set()
                    for r in saved:
                        self.assertEqual(len(r['train']),3);self.assertEqual(len(r['test']),1)
                        self.assertEqual(set(r['test'][0]),{'input'})
                        self.assertEqual(json.loads(r['completion']),{'outputs':r['solutions']})
                        self.assertEqual(json.loads(r['prompt'].split('\n',1)[1]),{'train':r['train'],'test':r['test']})
                        self.assertEqual(len(set(r['canonical_input_hashes'])),4)
                        used[split].update(r['canonical_input_hashes'])
                self.assertFalse(used['train'] & used['validation'])
            finally:b.OUT=previous
if __name__=='__main__':unittest.main()
