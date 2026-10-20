import hashlib,importlib,json,random,tempfile,unittest
from collections import Counter
from pathlib import Path
import pyarrow.parquet as pq
from . import build_million as b
from .generators.registry import GENERATORS,generate
from .runtime import BASE,reference,solver,call,grid,check_reference
from .task_registry import NEW_TASK_IDS
from .augmentation import apply_episode,settings

class GeneratorTests(unittest.TestCase):
    def test_fixed_canvas_requests_do_not_silently_expand(self):
        for tid in ['cd3c21df','d4c90558']:
            module=importlib.import_module('tasks.task_'+tid)
            for seed in range(5):
                random.seed(seed)
                pair=call(lambda:module.generate(width=18,height=24),seconds=3)
                self.assertEqual((len(pair['input']),len(pair['input'][0])),(24,18))
        frame=importlib.import_module('tasks.task_d4c90558')
        with self.assertRaisesRegex(ValueError,'minimum frame'):
            frame.generate(width=3,height=3)
    def test_registered_standalone_sources_and_fixtures(self):
        # Validate the registered files, not only the older research registry.
        for tid in NEW_TASK_IDS:
            module=importlib.import_module('tasks.task_'+tid)
            source=Path(module.__file__).read_bytes()
            report=json.loads((BASE/'reports'/'standalone'/f'{tid}.json').read_text())
            self.assertEqual(hashlib.sha256(source).hexdigest(),report['stress_test']['sha256'],tid)
            self.assertTrue(report['stress_test']['ready'],tid)
            actual=call(module.validate,seconds=30)
            expected=reference(tid)['canonical']
            key=lambda p:json.dumps(p,sort_keys=True)
            for split in ['train','test']:
                self.assertEqual(sorted(map(key,actual[split])),sorted(map(key,expected[split])),(tid,split))
            solve=solver(tid)
            for seed in range(10000,10020):
                random.seed(seed)
                pair=call(module.generate,seconds=3)
                self.assertEqual(grid(pair['output']),grid(call(solve,grid(pair['input']),seconds=3)),(tid,seed))
    def test_colour_cycles_are_simultaneous_and_episode_wide(self):
        palette=[1,2,0,3,4,5,6,7,8,9]
        self.assertEqual(b.transformed([[0,1,2]],0,palette),[[1,2,0]])
        pairs=[{'input':[[0,1,2],[3,4,5]],'output':[[2,0]]},
               {'input':[[1],[2]],'output':[[0,2,1]]}]
        for d in range(8):
            result=apply_episode(pairs,d,palette)
            inverse_palette=[palette.index(i) for i in range(10)]
            inverse_d=next(i for i in range(8) if b.transformed(b.transformed(pairs[0]['input'],d,list(range(10))),i,list(range(10)))==pairs[0]['input'])
            self.assertEqual(apply_episode(result,inverse_d,inverse_palette),pairs)
            # Originals must not be mutated.
            self.assertEqual(pairs[0]['input'],[[0,1,2],[3,4,5]])
    def test_all_public_tasks_eligible_and_bulk_guard(self):
        inv={'tasks':[{'task_id':'former_holdout','held_out':True,'status':'extension_validated'},
                      {'task_id':'missing','held_out':False,'status':'generator_missing'}]}
        self.assertEqual(b.eligible_tasks(inv),['former_holdout'])
        with self.assertRaisesRegex(RuntimeError,'Coverage first'):
            b.require_complete_coverage(inv)
        all_ready={'tasks':[{'task_id':str(i),'held_out':True,'status':'extension_validated'} for i in range(1120)]}
        b.require_complete_coverage(all_ready)
        with self.assertRaisesRegex(RuntimeError,'eight-variant'):
            b.require_build_ready(all_ready)
    def test_default_augmentation_preserves_native_colours(self):
        rng=random.Random(42);seen=set()
        for _ in range(1000):
            d,p=settings(rng,'example',b.POLICY);seen.add(d)
            self.assertEqual(p,list(range(10)))
        self.assertEqual(seen,set(range(8)))
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
