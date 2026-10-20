"""Keep early-stop spirals, but do not invent their unseen turn convention."""
import unittest
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.spiral_evidence import spiral_variants
from tasks import task_e5c44e8f as task


class SpiralEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def test_short_stop_does_not_teach_turn_but_informative_demo_recovers(self):
        weak=task.generate(prow=5,pcol=5,rows=[4],cols=[5])
        strong=task.generate(prow=4,pcol=5,rows=[],cols=[])
        query=task.generate(prow=6,pcol=5,rows=[],cols=[])
        for d4 in range(8):
            ds=apply_episode([weak],d4,self.palette)
            good=apply_episode([strong],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('e5c44e8f',ds,[payload],self.palette,d4)
                require_colour_evidence('e5c44e8f',ds+good,[payload],self.palette,d4)

    def test_query_agreement_preserves_fully_blocked_queries(self):
        p=task.generate(prow=5,pcol=5,rows=[4,5,6,5],cols=[5,6,5,4])
        q=task.generate(prow=6,pcol=6,rows=[5,6,7,6],cols=[6,7,6,5])
        self.assertTrue(all(out==p['input'] for out in spiral_variants(p['input'],list(range(10)))))
        for d4 in range(8):
            ds=apply_episode([p],d4,self.palette)
            query=apply_episode([q],d4,self.palette)[0]
            require_colour_evidence('e5c44e8f',ds,[{'input':query['input']}],self.palette,d4)

    def test_boundary_exit_and_reentry_for_every_seed_position(self):
        for r in range(11):
            for c in range(11):
                p=task.generate(prow=r,pcol=c,rows=[],cols=[])
                self.assertEqual(spiral_variants(p['input'],list(range(10)))[0],p['output'])

    def test_hypothesis_sets_and_canonical_episodes_are_d4_closed(self):
        data=task.validate()
        for p in data['train']+data['test']:
            native=spiral_variants(p['input'],list(range(10)))
            for d4 in range(8):
                q=apply_episode([p],d4,self.palette)[0]
                observed={tuple(map(tuple,x)) for x in spiral_variants(q['input'],self.palette)}
                expected={tuple(map(tuple,transformed(x,d4,self.palette))) for x in native}
                self.assertEqual(observed,expected)
                ds=apply_episode(data['train'],d4,self.palette)
                require_colour_evidence('e5c44e8f',ds,[{'input':q['input']}],self.palette,d4)

    def test_corrupt_demonstration_or_extra_seed_rejected(self):
        p=task.generate(prow=5,pcol=5,rows=[],cols=[])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('e5c44e8f',[dict(input=p['input'],output=[[0]])],[{'input':p['input']}])
        bad=[row[:] for row in p['input']];bad[0][0]=3
        with self.assertRaises(MissingColourEvidence):
            spiral_variants(bad,list(range(10)))


if __name__=='__main__':unittest.main()
