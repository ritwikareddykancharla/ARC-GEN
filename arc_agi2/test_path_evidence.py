"""Path tie evidence, independent route search and augmentation invariance."""
import random
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.path_evidence import route_evidence, detour_variants
from tasks import task_cc9053aa as maze, task_c87289bb as falling


class PathEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def test_canonical_maze_needs_a_tie_demonstration(self):
        data = maze.validate()
        strong = maze.generate(width=11, height=9, wall_rows=[1,3,5,7],
                               wall_cols=[2,4,6,8], oranges=[(2,5),(4,5)],
                               endpoints=[(0,2),(0,8)])
        for d4 in range(8):
            demos = apply_episode(data['train'], d4, self.palette)
            q = apply_episode(data['test'], d4, self.palette)[0]
            s = apply_episode([strong], d4, self.palette)[0]
            with self.subTest(d4=d4):
                # Query answers cannot rescue missing evidence.
                for query in ({'input': q['input']}, q, dict(input=q['input'], output=[[0]])):
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence('cc9053aa', demos, [query], self.palette, d4)
                require_colour_evidence('cc9053aa', demos+[s], [{'input': q['input']}], self.palette, d4)
                require_colour_evidence('cc9053aa', demos, [{'input': demos[0]['input']}], self.palette, d4)

    def test_maze_witness_and_wrong_demo(self):
        data = maze.validate()
        info = route_evidence(data['test'][0]['input'], list(range(10)))
        self.assertEqual((info['steps'], info['min_turns'], info['max_turns']), (20,2,6))
        self.assertNotEqual(info['minimum_turn_output'], info['maximum_turn_output'])
        wrong = dict(input=data['test'][0]['input'], output=info['maximum_turn_output'])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('cc9053aa', [wrong], data['test'])

    def test_equal_turn_routes_are_not_silently_selected(self):
        # 2x2 open cycle between opposite corners: both two-step routes turn once.
        g = [[9,8],[8,9]]
        info = route_evidence(g,list(range(10)))
        self.assertEqual(info['optimal_routes_capped'],2)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('cc9053aa',maze.validate()['train'],[{'input':g}])

    def test_independent_shortest_dag_matches_native_random_search(self):
        state = random.getstate()
        try:
            random.seed(9053)
            for _ in range(100):
                p = maze.generate()
                g = p['input']
                ends = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 9]
                cost, count, _ = maze._best_route(g,*ends,True)
                info = route_evidence(g,list(range(10)))
                self.assertEqual((info['steps'],info['min_turns']),cost)
                self.assertEqual(info['optimal_routes_capped'],min(2,count))
                self.assertEqual(info['shortest_routes_capped'],min(2,maze._shortest_count(g,*ends)))
                self.assertEqual(info['minimum_turn_output'],p['output'])
        finally:
            random.setstate(state)

    def test_detour_tie_needs_evidence_but_untied_query_does_not(self):
        data = falling.validate()
        weak, strong = data['train'][:2], data['train'][2:3]
        query, untied = data['train'][3], data['test'][0]
        for d4 in range(8):
            ds = apply_episode(weak,d4,self.palette)
            ss = apply_episode(strong,d4,self.palette)
            q,a = apply_episode([query,untied],d4,self.palette)
            with self.subTest(d4=d4):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('c87289bb',ds,[q],self.palette,d4)
                require_colour_evidence('c87289bb',ds+ss,[{'input':q['input']}],self.palette,d4)
                require_colour_evidence('c87289bb',ds,[{'input':a['input']}],self.palette,d4)
                require_colour_evidence('c87289bb',ds+ss,[dict(input=q['input'],output=[[0]])],self.palette,d4)

    def test_detour_conventions_are_identified_from_demo_outputs(self):
        data = falling.validate()
        for d4 in range(8):
            ps = apply_episode(data['train']+data['test'],d4,self.palette)
            self.assertTrue(all(p['output'] in detour_variants(p['input'],self.palette,d4) for p in ps))
            # Same visible inputs, opposite convention: the gate follows evidence.
            opposite = [dict(input=p['input'],output=detour_variants(p['input'],self.palette,d4)[0]) for p in ps[:4]]
            require_colour_evidence('c87289bb',opposite,[{'input':ps[3]['input']}],self.palette,d4)


if __name__ == '__main__': unittest.main()
