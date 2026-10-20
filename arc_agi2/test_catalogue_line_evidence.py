"""Require visible evidence for partial lines and each success/failure fill."""
import random
import unittest

from arc_agi2.augmentation import apply_episode
from arc_agi2.catalogue_line_evidence import decode_catalogue, paint_roles
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from tasks import task_d8e07eb2 as catalogue


class CatalogueLineEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]

    def pair(self,top):
        return catalogue.generate(catalogue=catalogue.CANON,top=top)

    def check(self,demos,query,d4=0,accept=True):
        ds = apply_episode(demos,d4,self.palette)
        q = apply_episode([query],d4,self.palette)[0]
        for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
            if accept:
                require_colour_evidence('d8e07eb2',ds,[payload],self.palette,d4)
            else:
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('d8e07eb2',ds,[payload],self.palette,d4)

    def test_canonical_queries_pass_all_d4_and_ignore_query_labels(self):
        data = catalogue.validate()
        for d4 in range(8):
            for query in data['test']:
                self.check(data['train'],query,d4)

    def test_partial_row_and_column_need_their_own_demonstrated_evidence(self):
        base = catalogue.validate()['train']
        row_demo = self.pair([(0,0),(0,2)])
        col_demo = self.pair([(0,0),(2,0)])
        row_query = self.pair([(1,0),(1,2),(1,3)])
        col_query = self.pair([(0,1),(2,1),(3,1)])
        for d4 in range(8):
            self.check(base,row_query,d4,False)
            self.check(base,col_query,d4,False)
            self.check(base+[row_demo],row_query,d4)
            self.check(base+[row_demo],col_query,d4,False)
            self.check(base+[row_demo,col_demo],col_query,d4)

    def test_query_branch_requires_demonstrated_fill_roles(self):
        data = catalogue.validate()
        succeeds,fails = data['train'][:2],data['train'][2:]
        for d4 in range(8):
            self.check(succeeds,data['test'][1],d4,False)
            self.check(fails,data['test'][0],d4,False)
            self.check(data['train'],data['test'][1],d4)

    def test_independent_decoder_handles_narrow_glyphs_and_rectangular_catalogues(self):
        random.seed(837613)
        pairs = [catalogue.generate(rows=rows,cols=cols)
                 for rows,cols in ((2,5),(4,3),(3,5),(4,5)) for _ in range(12)]
        pairs += catalogue.validate()['train']
        for p in pairs:
            for d4 in range(8):
                q = apply_episode([p],d4,self.palette)[0]
                scene = decode_catalogue(q['input'],self.palette)
                out = [row[:] for row in q['input']]
                for (r,c),role in paint_roles(scene,(2,2)).items():
                    out[r][c] = self.palette[2] if role == 'failure_result' else self.palette[3]
                self.assertEqual(out,q['output'])

    def test_corrupted_demonstrations_and_changed_colour_roles_rejected(self):
        data = catalogue.validate()
        wrong = dict(input=data['train'][0]['input'],output=[[0]])
        self.check([wrong],data['test'][0],accept=False)
        # Even internally consistent altered roles cannot retain the native
        # program target: it would silently teach the opposite palette.
        altered = []
        for p in data['train']:
            out = [row[:] for row in p['output']]
            for r,row in enumerate(out):
                for c,ink in enumerate(row):
                    if p['input'][r][c] != ink:
                        out[r][c] = 9
            altered.append(dict(input=p['input'],output=out))
        self.check(altered,data['test'][0],accept=False)


if __name__ == '__main__':
    unittest.main()
