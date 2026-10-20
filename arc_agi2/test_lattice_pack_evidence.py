"""Packing mechanisms must be identifiable after arbitrary reflections."""
import itertools
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.lattice_pack_evidence import pack_options,surviving_pack_rules
from arc_agi2.direct_factories.task_afe3afe9 import build_program
from tasks import task_afe3afe9 as native


def example(variant=0,flip=0,flop=0,xpose=0):
    colours=[0]*42
    for r in range(7):
        colours[6*r+3+r%3]=8
        if r%2:colours[6*r+3+(r+1)%3]=8
        if r!=3:
            colours[6*r+r%3]=2 if r<3 else 3
            if variant:colours[6*r+(r+1)%3]=2 if r<3 else 3
    return native.generate(colors=colours,flip=flip,flop=flop,xpose=xpose)


class LatticePackingEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_native_odd_handed_case_retained_with_informative_context(self):
        odd=example(flop=1);query=example(1,flop=1)
        self.assertNotEqual(odd['input'],query['input'])
        opts=pack_options(query['input'],list(range(10)))
        self.assertEqual(opts['eight'],query['output']);self.assertNotEqual(opts['cw'],query['output'])
        for d4 in range(8):
            weak=apply_episode(native.validate()['train'],d4,self.palette)
            strong=apply_episode([example(),odd,example(xpose=1)],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('afe3afe9',weak,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(weak,q['input'])
            for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_colour_evidence('afe3afe9',strong,[payload],self.palette,d4)
            self.assertEqual(self.solver(d4)(strong,q['input']),q['output'])

    def test_counterfactual_clockwise_context_changes_same_query(self):
        ds=[example(),example(flop=1)];q=example(1,flop=1)
        native_output=q['output']
        for p in ds+[q]:p['output']=pack_options(p['input'],list(range(10)))['cw']
        self.assertNotEqual(q['output'],native_output)
        for d4 in range(8):
            demos=apply_episode(ds,d4,self.palette);query=apply_episode([q],d4,self.palette)[0]
            require_colour_evidence('afe3afe9',demos,[query],self.palette,d4)
            self.assertEqual(self.solver(d4)(demos,query['input']),query['output'])

    def test_all_eight_native_orientations_and_eight_external_transforms(self):
        lessons=[example(),example(flop=1),example(xpose=1)]
        for flip,flop,xpose in itertools.product((0,1),repeat=3):
            q=example(1,flip,flop,xpose)
            for d4 in range(8):
                ds=apply_episode(lessons,d4,self.palette);p=apply_episode([q],d4,self.palette)[0]
                require_colour_evidence('afe3afe9',ds,[p],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,p['input']),p['output'])

    def test_colour_and_edge_permutations_do_not_supply_hidden_handedness(self):
        # Hypothesis labels cw and ccw may swap under reflection; their set of
        # predictions remains closed under the same transformation.
        p=example(1,flop=1);options=pack_options(p['input'],list(range(10)))
        for d4 in range(8):
            q=apply_episode([p],d4,self.palette)[0]
            transformed=apply_episode([dict(input=p['input'],output=o) for o in options.values()],d4,self.palette)
            observed=pack_options(q['input'],self.palette)
            self.assertEqual({str(x['output']) for x in transformed},{str(x) for x in observed.values()})

    def test_canonical_fixtures(self):
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette)
            for q in apply_episode(native.validate()['test'],d4,self.palette):
                require_colour_evidence('afe3afe9',ds,[q],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_absent_conflicting_and_malformed_demos_reject(self):
        a=example();b=example();b['output']=pack_options(b['input'],list(range(10)))['ccw']
        for ds in ([],[a,b],[dict(input=a['input'],output=[[0]])]):
            with self.assertRaises(MissingColourEvidence):surviving_pack_rules(ds,list(range(10)))
            demos=apply_episode(ds,0,self.palette)
            with self.assertRaises(ValueError):self.solver(0)(demos,apply_episode([a],0,self.palette)[0]['input'])
        malformed=example();malformed['input'][0][0]=0
        with self.assertRaises(ValueError):pack_options(malformed['input'],list(range(10)))


if __name__=='__main__':unittest.main()
