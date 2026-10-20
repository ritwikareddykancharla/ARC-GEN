"""Colour roles and ordered claiming must be taught where they affect queries."""
import random
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.paint_order_evidence import paint_variants
from tasks import task_9385bd28 as paint


class PaintOrderEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]

    def nested(self,bg=0,shift=0):
        return paint.generate(width=16,height=16,bg=bg,legend=[(1,3),(2,0)],
            legend_pos=(12,0),objects=[('pair',1,shift,shift,7+shift,7+shift,'main'),
                                      ('pair',2,2+shift,2+shift,5+shift,5+shift,'main')])

    def check(self,weak,strong,query):
        for d4 in range(8):
            ds = apply_episode(weak,d4,self.palette)
            ss = apply_episode(strong,d4,self.palette)
            q = apply_episode([query],d4,self.palette)[0]
            with self.subTest(d4=d4):
                for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[0]])):
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence('9385bd28',ds,[payload],self.palette,d4)
                require_colour_evidence('9385bd28',ds+ss,[{'input':q['input']}],self.palette,d4)

    def test_empty_reserve_region_is_kept_with_evidence(self):
        # Preserve the original synthetic extension rather than reject all
        # deeply nested reserves. Its teaching example distinguishes the rule.
        strong,query = self.nested(),self.nested(shift=1)
        self.assertEqual(strong['output'][2][2],2)
        self.assertEqual(paint_variants(strong['input'],list(range(10)),0)[4][2][2],0)
        self.check(paint.validate()['train'],[strong],query)

    def test_erase_role_and_timing_need_visible_evidence(self):
        data = paint.validate()
        self.check([data['train'][i] for i in (0,1,3)],
                   [self.nested(bg=5)],self.nested(bg=5,shift=1))

    def test_erasing_inline_differs_from_erasing_before_filling(self):
        p = self.nested(bg=5)
        variants = paint_variants(p['input'],list(range(10)),0)
        self.assertEqual(variants[0],p['output'])
        self.assertNotEqual(variants[0],variants[12])
        self.assertNotEqual(variants[0],variants[24])
        self.assertNotEqual(variants[0],variants[36])

    def test_canonical_order_ambiguity_is_documented_not_exempted(self):
        data = paint.validate();alive = set(range(48))
        for p in data['train']:
            alive &= {i for i,v in enumerate(paint_variants(p['input'],list(range(10)),0)) if v == p['output']}
        self.assertEqual(alive,{0,2,4,6,14,18})
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('9385bd28',data['train'],[{'input':data['test'][0]['input']}])
        require_colour_evidence('9385bd28',data['train'],[{'input':data['test'][1]['input']}])
        require_colour_evidence('9385bd28',data['train']+[self.nested()],
                               [{'input':p['input']} for p in data['test']])

    def test_native_predictions_and_hypothesis_sets_transform_consistently(self):
        state = random.getstate()
        try:
            random.seed(938528)
            data = paint.validate()
            pairs = data['train']+data['test']+[paint.generate() for _ in range(12)]
            pairs += [self.nested(),self.nested(bg=5)]
            for pair in pairs:
                original = paint_variants(pair['input'],list(range(10)),0)
                for d4 in range(8):
                    p = apply_episode([pair],d4,self.palette)[0]
                    variants = paint_variants(p['input'],self.palette,d4)
                    self.assertEqual(variants[0],p['output'])
                    expected = {tuple(map(tuple,apply_episode([dict(input=pair['input'],output=v)],d4,self.palette)[0]['output'])) for v in original}
                    observed = {tuple(map(tuple,v)) for v in variants}
                    self.assertEqual(expected,observed)
        finally: random.setstate(state)


if __name__ == '__main__': unittest.main()
