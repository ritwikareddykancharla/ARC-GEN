"""Do not silently decide assembly swaps by orientation or enumeration order."""
import random
import unittest

from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.packing_evidence import optimal_packings,packing_candidates,select_packing_demonstrations
from arc_agi2.program_targets import compile_target,verify
from tasks import task_b7cb93ac as task


class PackingEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]

    def teaching(self):
        pairs=[]
        for seed in (72,79):
            random.seed(1065000+seed)
            pairs.append(task.generate(tie=True))
        return pairs+[task.validate()['train'][0]]

    def test_canonical_tie_requires_teaching_context_within_three_demos(self):
        data=task.validate();strong=self.teaching()
        self.assertEqual(len(strong),3)
        for d4 in range(8):
            weak=apply_episode(data['train'],d4,self.palette)
            ds=apply_episode(strong,d4,self.palette)
            query=apply_episode(data['test'],d4,self.palette)[0]
            for q in ({'input':query['input']},query,dict(input=query['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('b7cb93ac',weak,[q],self.palette,d4)
                require_colour_evidence('b7cb93ac',ds,[q],self.palette,d4)

    def test_independent_exact_cover_cost_and_indistinguishable_copies(self):
        data=task.validate()
        observed=[]
        for p in data['train']+data['test']:
            types,tilings,cost=optimal_packings(p['input'],0,3,4)
            observed.append((cost,len(tilings)))
            for tiling in tilings:
                mask=0
                for ti,pm,rotation in tiling:
                    self.assertFalse(mask&pm)
                    mask|=pm
                self.assertEqual(mask,(1<<12)-1)
                self.assertEqual(sum(x[2] for x in tiling),cost)
        self.assertEqual(observed,[(0,1),(1,1),(1,2),(1,2)])
        random.seed(3516)
        p=task.generate(width=6,height=6,num_pieces=6)
        options=packing_candidates(tuple(map(tuple,p['input'])),0,3,4)
        self.assertIn(tuple(map(tuple,p['output'])),set().union(*options))

    def test_complete_hypothesis_sets_transform_equivariantly(self):
        data=task.validate();pairs=data['train']+data['test']+self.teaching()
        random.seed(741851)
        pairs += [task.generate() for _ in range(12)]
        for p in pairs:
            native=packing_candidates(tuple(map(tuple,p['input'])),0,3,4)
            self.assertIn(tuple(map(tuple,p['output'])),set().union(*native))
            for d4 in range(8):
                q=apply_episode([p],d4,self.palette)[0]
                oh,ow=len(q['output']),len(q['output'][0])
                observed=set(packing_candidates(tuple(map(tuple,q['input'])),self.palette[0],oh,ow))
                expected={frozenset(tuple(map(tuple,transformed([list(r) for r in painting],d4,self.palette)))
                                    for painting in group) for group in native}
                self.assertEqual(observed,expected)

    def test_above_left_tie_not_removed_from_constructor_or_target(self):
        p=task.generate(width=14,height=14,
            regions=[[(0,0),(0,1),(0,2),(0,3),(1,0),(1,3)],
                     [(1,1),(2,0),(2,1)],[(1,2),(2,2),(2,3)]],
            colors=[8,3,6],rotations=[0,0,3],offsets=[(9,3),(1,1),(6,8)])
        self.assertEqual(p['output'],task.validate()['test'][0]['output'])
        for d4 in range(8):
            q=apply_episode([p],d4,self.palette)[0]
            verify(compile_target('b7cb93ac',d4,self.palette)[0],
                   dict(train=apply_episode(task.validate()['train'],d4,self.palette),
                        test=[{'input':q['input']}],solutions=[q['output']]))

    def test_inconsistent_paint_and_dimensions_rejected(self):
        data=task.validate();bad=dict(input=data['train'][0]['input'],output=[[7]*4 for _ in range(3)])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('b7cb93ac',[bad],[{'input':data['test'][0]['input']}])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('b7cb93ac',[],[{'input':data['test'][0]['input']}])

    def test_context_search_recovers_query_that_needs_all_three_examples(self):
        examples=[]
        for seed in (0,72,40,8):
            random.seed(1065000+seed)
            examples.append(task.generate(tie=True))
        query=examples[0];pool=examples[1:]
        selected=select_packing_demonstrations(pool,query['input'],random.Random(0))
        self.assertIsNotNone(selected)
        self.assertEqual(len(selected),3)
        require_colour_evidence('b7cb93ac',selected,[{'input':query['input']}])
        for missing in range(3):
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('b7cb93ac',[p for i,p in enumerate(selected) if i!=missing],
                                        [{'input':query['input']}])

    def test_context_search_returns_none_if_only_unique_examples_available(self):
        data=task.validate()
        self.assertIsNone(select_packing_demonstrations(data['train'],data['test'][0]['input'],random.Random(0)))
        rows=self.teaching()
        for i,p in enumerate(rows):p['canonical_input_hash']=str(i)
        # Excluding both tied witnesses makes the query ambiguous; duplicated
        # copies of the remaining witness do not count as distinct demos.
        rows[1]['canonical_input_hash']='0'
        self.assertIsNone(select_packing_demonstrations(rows,data['test'][0]['input'],random.Random(0)))

    def test_context_search_spreads_usage_and_preserves_scarce_tie_examples(self):
        data=task.validate();rows=list(data['train'])
        for seed in range(80):
            random.seed(1065000+seed)
            rows.append(task.generate(tie=True))
        for i,row in enumerate(rows):
            row['input_hash']=str(i)
        query=data['test'][0]
        first=select_packing_demonstrations(rows,query['input'],random.Random(0))
        self.assertIsNotNone(first)
        usage={p['input_hash']:31 for p in first}
        second=select_packing_demonstrations(rows,query['input'],random.Random(0),pair_uses=usage)
        self.assertIsNotNone(second)
        self.assertTrue(all(usage.get(p['input_hash'],0)==0 for p in second))
        require_colour_evidence('b7cb93ac',second,[{'input':query['input']}])
        # A unique-painting query can use ordinary examples and should not
        # consume the tie witnesses merely because their usage is low.
        simple=select_packing_demonstrations(rows,data['train'][0]['input'],random.Random(4))
        self.assertTrue(all(p['input_hash'] in {'0','1','2'} for p in simple))


if __name__=='__main__':unittest.main()
