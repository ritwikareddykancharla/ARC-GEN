"""Demonstrated motifs, including counterfactual patterns absent from the table."""
import unittest
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.line_motif_evidence import solve_visible_motifs
from arc_agi2.program_targets import compile_target
from tasks import task_98c475bf as task


class LineMotifEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        source=compile_target('98c475bf',d4,self.palette)[0]
        namespace={};exec(source,namespace)
        return namespace['solve']

    def test_unseen_query_motif_rejected_by_gate_and_program(self):
        data=task.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            q=apply_episode(data['test'],d4,self.palette)[0]
            solve=self.solver(d4)
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('98c475bf',ds[:3],[payload],self.palette,d4)
                require_colour_evidence('98c475bf',ds,[payload],self.palette,d4)
            with self.assertRaises(ValueError):solve(ds[:3],q['input'])
            with self.assertRaises(ValueError):solve([],q['input'])
            self.assertEqual(solve(ds,q['input']),q['output'])
            self.assertEqual(solve_visible_motifs(ds,q['input'],self.palette[0]),q['output'])

    def reflect_colour(self,g,colour=3):
        out=[[0 if v==colour else v for v in row] for row in g]
        for r,row in enumerate(g):
            for c,v in enumerate(row):
                if v==colour:out[r][len(row)-1-c]=colour
        return out

    def test_changed_lesson_changes_answer_instead_of_using_hidden_motif_table(self):
        data=task.validate()
        ds=[{k:self.reflect_colour(p[k]) for k in ('input','output')} for p in data['train']]
        q=data['test'][0]
        query=self.reflect_colour(q['input']);expected=self.reflect_colour(q['output'])
        self.assertEqual(query,q['input'])
        self.assertNotEqual(expected,q['output'])
        for d4 in range(8):
            demos=apply_episode(ds,d4,self.palette)
            qi=transformed(query,d4,self.palette);answer=transformed(expected,d4,self.palette)
            self.assertEqual(self.solver(d4)(demos,qi),answer)
            self.assertEqual(solve_visible_motifs(demos,qi,self.palette[0]),answer)
            require_colour_evidence('98c475bf',demos,[{'input':qi}],self.palette,d4)

    def test_conflicting_lessons_raise(self):
        data=task.validate();altered=[{k:self.reflect_colour(p[k]) for k in ('input','output')}
                                   for p in data['train']]
        ds=apply_episode(data['train']+altered,0,self.palette)
        q=transformed(data['test'][0]['input'],0,self.palette)
        with self.assertRaises(ValueError):self.solver(0)(ds,q)
        with self.assertRaises(MissingColourEvidence):solve_visible_motifs(ds,q,self.palette[0])

    def test_clipping_and_span_mismatch_raise_instead_of_falling_back(self):
        data=task.validate();ds=apply_episode(data['train'],0,self.palette)
        for width,row in ((20,0),(21,5)):
            bad=[[8]+[0]*(width-2)+[8] for _ in range(12)]
            bad[row][1]=bad[row][-2]=3
            q=transformed(bad,0,self.palette)
            with self.assertRaises(ValueError):self.solver(0)(ds,q)
            with self.assertRaises(MissingColourEvidence):solve_visible_motifs(ds,q,self.palette[0])


if __name__=='__main__':unittest.main()
