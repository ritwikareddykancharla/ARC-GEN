"""Broken diagonals remain valid; unresolved mechanism and ties must reject."""
import unittest
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.diagonal_evidence import diagonal_options,surviving_rules
from arc_agi2.direct_factories.task_aa300dc3 import build_program
from tasks import task_aa300dc3 as native


def broken(extra=False):
    tops=[1,1,3,1,1,1,1,1,1,1]
    if extra:tops[5]=2
    p=native.generate(tops=tops,lefts=[1,1,1,1,1,1,1,2,1,1],
                      rights=[1,2,1,1,1,1,1,1,1,1],bottoms=[1,2,2,1,1,1,1,2,1,1])
    assert p['input'] is not None
    return p


def paint(g,cells,ink):
    out=[row[:] for row in g]
    for r,c in cells:out[r][c]=ink
    return out


def altered_tie():
    # Change an off-winner protrusion in the original second demonstration;
    # the same three anti-diagonals remain tied, with a unique most-central one.
    return native.generate(tops=[1,4,2,1,3,1,2,1,1,1],lefts=[1,1,1,1,2,3,1,1,1,1],
                           rights=[1,1,1,1,1,2,1,1,1,1],bottoms=[1,2,1,2,1,1,2,3,3,1])


class DiagonalEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4,palette=None):
        ns={};exec(build_program(d4,self.palette if palette is None else palette),ns);return ns['solve']

    def test_broken_winner_is_reachable_and_informative_context_recovers(self):
        data=native.validate();lesson=broken();query=broken(True)
        self.assertNotEqual(lesson['input'],query['input'])
        options=diagonal_options(query['input'],list(range(10)))
        self.assertEqual({len(x) for x in options[0]},{7})
        self.assertEqual({len(x) for x in options[5]},{6})
        self.assertEqual(query['output'][1][1],8);self.assertEqual(query['output'][2][2],5)
        for d4 in range(8):
            weak=apply_episode(data['train'],d4,self.palette)
            strong=apply_episode([lesson],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):require_colour_evidence('aa300dc3',weak,[payload],self.palette,d4)
                require_colour_evidence('aa300dc3',weak+strong,[payload],self.palette,d4)
            with self.assertRaisesRegex(ValueError,'unresolved'):self.solver(d4)(weak,q['input'])
            self.assertEqual(self.solver(d4)(weak+strong,q['input']),q['output'])

    def test_opposite_run_demonstrations_change_same_query(self):
        lesson=broken();query=broken(True)
        for p in (lesson,query):
            opts=diagonal_options(p['input'],list(range(10)))[9]
            self.assertEqual(len(opts),1);p['output']=paint(p['input'],next(iter(opts)),8)
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('aa300dc3',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_central_tie_rule_generalizes_beyond_demo_input(self):
        data=native.validate();query=altered_tie()
        self.assertIsNotNone(query['input']);self.assertNotEqual(query['input'],data['train'][1]['input'])
        self.assertEqual(len(diagonal_options(query['input'],list(range(10)))[0]),3)
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('aa300dc3',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_symmetric_unresolved_tie_is_not_resolved_by_scan_order(self):
        p=native.generate(tops=[1]*10,lefts=[1]*10,rights=[1]*10,bottoms=[1]*10)
        for d4 in range(8):
            ds=apply_episode(native.validate()['train']+[broken()],d4,self.palette)
            q=apply_episode([p],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('aa300dc3',ds,[q],self.palette,d4)
            with self.assertRaisesRegex(ValueError,'unresolved'):self.solver(d4)(ds,q['input'])

    def test_all_tie_prediction_sets_are_d4_closed(self):
        pairs=native.validate()['train']+native.validate()['test']+[broken(),broken(True),altered_tie()]
        for p in pairs:
            original=diagonal_options(p['input'],list(range(10)))
            for d4 in range(8):
                observed=diagonal_options(transformed(p['input'],d4,self.palette),self.palette)
                for choices,result in zip(original,observed):
                    expected=set()
                    for cells in choices:
                        mask=paint([[0]*10 for _ in range(10)],cells,1)
                        rotated=transformed(mask,d4,list(range(10)))
                        expected.add(frozenset((r,c) for r,row in enumerate(rotated) for c,v in enumerate(row) if v))
                    self.assertEqual(result,expected)

    def test_canonical_queries_and_invalid_demonstrations(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for q in apply_episode(data['test'],d4,self.palette):
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])
        bad=broken();bad['output']=[[99]]
        with self.assertRaises(MissingColourEvidence):surviving_rules([bad],list(range(10)))
        bad=broken();bad['output'][0][0]=8
        with self.assertRaises(MissingColourEvidence):surviving_rules([bad],list(range(10)))


if __name__=='__main__':unittest.main()
