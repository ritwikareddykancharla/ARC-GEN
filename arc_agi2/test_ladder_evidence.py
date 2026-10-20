"""Keep ladder stubs and even lengths; distinguish rank from rung count."""
import unittest
from itertools import product
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.ladder_evidence import ladder_features,ladder_variants
from arc_agi2.direct_factories.task_a1aa0c1e import build_program
from tasks import task_a1aa0c1e as native


def pair(rows=(1,5,12,20),lengths=(1,6,7),colours=(1,2,3,9)):
    return native.generate(colors=list(colours),rows=list(rows),cols=[2,10,16,4],lengths=list(lengths))


def allowed_lengths():
    for start in (1,2):
        for a,b,c in product(range(4,9),repeat=3):
            if start+a+b+c not in (19,20):continue
            rows=[start,start+a,start+a+b,start+a+b+c]
            for x,y in product(range(a),range(b)):
                lengths=[x,y,c-1]
                if len(set(lengths)) in (1,3):yield rows,lengths


class LadderEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4,palette=None):
        ns={};exec(build_program(d4,self.palette if palette is None else palette),ns);return ns['solve']

    def test_exhaustive_native_gap_and_length_combinations(self):
        identity=list(range(10));lesson=pair();solve=self.solver(0,identity)
        count=0;all_equal=set();missing=False;stubs=False;even=False
        for rows,lengths in allowed_lengths():
            p=pair(rows,lengths)
            colours,recovered,rungs,reaches=ladder_features(p['input'],identity)
            self.assertEqual(recovered,lengths)
            self.assertEqual(rungs,[n//2 for n in lengths])
            self.assertEqual(reaches,[lengths[i]==rows[i+1]-rows[i]-1 for i in range(3)])
            self.assertEqual(ladder_variants(p['input'],identity,0)[0],p['output'])
            self.assertEqual(solve([lesson],p['input']),p['output'])
            count+=1;missing|=0 in lengths;stubs|=1 in lengths;even|=any(n>0 and n%2==0 for n in lengths)
            if len(set(lengths))==1:all_equal.add(lengths[0])
        self.assertGreater(count,1000);self.assertEqual(all_equal,{3,4,5})
        self.assertTrue(missing and stubs and even)

    def test_weak_context_rejected_and_stub_query_recovered(self):
        weak=native.validate()['train'];query=pair(colours=(4,6,7,9));strong=pair()
        for d4 in range(8):
            ds=apply_episode(weak,d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            lesson=apply_episode([strong],d4,self.palette)
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):require_colour_evidence('a1aa0c1e',ds,[payload],self.palette,d4)
                require_colour_evidence('a1aa0c1e',ds+lesson,[payload],self.palette,d4)
            with self.assertRaisesRegex(ValueError,'distinguish'):self.solver(d4)(ds,q['input'])
            self.assertEqual(self.solver(d4)(ds+lesson,q['input']),q['output'])

    def test_opposite_demonstrated_rule_changes_same_query(self):
        lesson=pair();query=pair(colours=(4,6,7,9))
        lesson['output']=ladder_variants(lesson['input'],list(range(10)),0)[1]
        query['output']=ladder_variants(query['input'],list(range(10)),0)[1]
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('a1aa0c1e',ds,[{'input':q['input']}],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_equal_absent_even_and_partial_ladders_under_all_d4(self):
        cases=[pair((1,8,16,20),(3,3,3)),pair((1,8,15,20),(4,4,4)),
               pair((1,7,13,19),(5,5,5)),pair((1,5,12,20),(0,6,7)),pair()]
        for d4 in range(8):
            ds=apply_episode([pair()],d4,self.palette)
            for original,p in zip(cases,apply_episode(cases,d4,self.palette)):
                native_variants=ladder_variants(original['input'],list(range(10)),0)
                self.assertEqual(ladder_variants(p['input'],self.palette,d4),
                                 [transformed(x,d4,self.palette) for x in native_variants])
                require_colour_evidence('a1aa0c1e',ds,[p],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,p['input']),p['output'])

    def test_canonical_context_accepted_where_rules_agree(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for p in apply_episode(data['test'],d4,self.palette):
                require_colour_evidence('a1aa0c1e',ds,[p],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,p['input']),p['output'])

    def test_invalid_context_and_broken_ladder_rejected(self):
        p=pair();p['output']=[[99]]
        with self.assertRaises(MissingColourEvidence):require_colour_evidence('a1aa0c1e',[p],[{'input':p['input']}])
        with self.assertRaisesRegex(ValueError,'Neither'):self.solver(0,list(range(10)))([p],p['input'])
        p=pair();p['input'][6][9]=0
        with self.assertRaises(MissingColourEvidence):ladder_features(p['input'],list(range(10)))


if __name__=='__main__':unittest.main()
