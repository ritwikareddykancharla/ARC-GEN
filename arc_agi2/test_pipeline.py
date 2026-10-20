import hashlib,importlib,json,random,tempfile,unittest
from collections import Counter,defaultdict
from pathlib import Path
from unittest.mock import patch
import pyarrow.parquet as pq
from . import build_million as b
from .generators.registry import GENERATORS,generate
from .runtime import BASE,reference,solver,call,grid,check_reference
from .task_registry import NEW_TASK_IDS
from .fixture_policy import fixture_basis
from .augmentation import apply_episode,settings,exhaustive_variants

class GeneratorTests(unittest.TestCase):
    def test_containment_keeps_outside_distractors_at_requested_counts(self):
        m=importlib.import_module('tasks.task_9720b24f')
        original=m._random_scene;scenes=[]
        def trace(*args,**kwargs):
            scene=original(*args,**kwargs);scenes.append(scene);return scene
        with patch.object(m,'_random_scene',trace):
            for n in (0,9,12):
                random.seed(40000)
                pair=m.generate(width=30,height=30,num_containers=1,num_loose=n)
                self.assertEqual(len(scenes[-1][2]),n)
                self.assertEqual(pair['output'],grid(call(solver('9720b24f'),pair['input'])))
        with self.assertRaises(ValueError):m.generate(width=4,height=4,num_containers=1,num_loose=12)
        for n in (-1,True,13):
            with self.assertRaises(ValueError):m.generate(num_loose=n)

    def test_containment_background_and_valid_identity(self):
        m=importlib.import_module('tasks.task_9720b24f')
        pair=m.validate()['train'][0];freq=Counter(sum(pair['input'],[]))
        self.assertGreater(freq[1],freq[0])
        self.assertEqual(pair['output'][1][1],0)
        self.assertEqual(pair['output'],grid(call(solver('9720b24f'),pair['input'])))
        identity=m.generate(width=3,height=3,containers=[],num_containers=0,num_loose=0)
        self.assertEqual(identity['input'],identity['output'])
        with self.assertRaises(ValueError):m.generate(width=3,height=3,containers=[],num_loose=1)

    def test_containment_explicit_size_and_colour_qualifications(self):
        m=importlib.import_module('tasks.task_9720b24f')
        ring=[(y,x) for y in range(1,8) for x in range(1,8) if y in (1,7) or x in (1,7)]
        p=m.generate(width=9,height=9,containers=[(2,ring)],inners=[(3,[(3,3)])],loose=[(2,[(4,4)])])
        self.assertEqual(p['output'][4][4],2);self.assertEqual(p['output'][3][3],0)
        self.assertEqual(p['output'],grid(call(solver('9720b24f'),p['input'])))
        border=[(1,x) for x in range(1,7)]+[(y,1) for y in range(2,7)]
        larger=[(y,x) for y in range(2,6) for x in range(3,6)]
        for cells in (larger,larger[:-1]):
            p=m.generate(width=8,height=8,containers=[(2,border)],inners=[(3,[(5,2)])],loose=[(4,cells)])
            self.assertEqual(sum(row.count(4) for row in p['output']),len(cells))
            self.assertEqual(p['output'][5][2],0)
            self.assertEqual(p['output'],grid(call(solver('9720b24f'),p['input'])))

    def test_anchor_reflection_rejects_rotation_shortcuts_and_fits_extremes(self):
        m=importlib.import_module('tasks.task_963f59bc')
        for kw in [dict(sides=['right'],box_height=3,box_width=5),
                   dict(sides=['down'],box_height=5,box_width=3),
                   dict(width=26,height=26,num_markers=4,box_height=8,box_width=8),
                   dict(width=7,height=3,sides=['right'],box_height=3,box_width=3)]:
            for seed in range(20):
                random.seed(seed);pair=m.generate(**kw)
                cells={(y,x) for y,row in enumerate(pair['input']) for x,v in enumerate(row) if v==1}
                ys,xs=zip(*cells);t,b,l,r=min(ys),max(ys),min(xs),max(xs)
                self.assertNotEqual(cells,{(t+b-y,x) for y,x in cells})
                self.assertNotEqual(cells,{(y,l+r-x) for y,x in cells})
                self.assertEqual(pair['output'],grid(call(solver('963f59bc'),pair['input'])))
                if 'num_markers' in kw:
                    colours=set(sum(pair['input'],[]))-{0,1}
                    self.assertEqual(len(colours),kw['num_markers'])
                    for c in colours:self.assertEqual(sum(row.count(c) for row in pair['output']),len(cells))

    def test_anchor_reflection_clipping_and_container_validation(self):
        m=importlib.import_module('tasks.task_963f59bc')
        cells=[(4,1),(4,2),(5,2),(6,1),(6,2),(6,3),(6,4)]
        pair=m.generate(width=11,height=12,shape=cells,markers=[(5,10,6)])
        self.assertLess(sum(row.count(6) for row in pair['output']),len(cells))
        self.assertEqual(pair['output'],grid(call(solver('963f59bc'),pair['input'])))
        for kw in [dict(sides=3),dict(colors=3),dict(shape=3,width=12,height=12),
                   dict(shape=cells,markers=3,width=12,height=12)]:
            with self.assertRaises(ValueError):m.generate(**kw)

    def test_bracket_count_is_retained_and_tight_packing_is_constructive(self):
        m=importlib.import_module('tasks.task_93c31fbe')
        random.seed(40000)
        with patch.object(m,'_sample_boxes',return_value=None):
            pair=m.generate(width=5,height=30,num_frames=4,colour=2)
        self.assertEqual(sum(row.count(2) for row in pair['input']),48)
        self.assertEqual(pair['output'],grid(call(solver('93c31fbe'),pair['input'])))
        attempts=[];original=m._sample_boxes
        def fail_45(h,w,n):
            attempts.append(n)
            return None if len(attempts)<=45 else original(h,w,n)
        random.seed(6)
        with patch.object(m,'_sample_boxes',fail_45):m.generate(width=30,height=30)
        self.assertEqual(len(set(attempts)),1)

    def test_bracket_explicit_marker_density_and_malformed_containers(self):
        m=importlib.import_module('tasks.task_93c31fbe')
        for kw in ({'frames':[5],'ones':[]},{'frames':5,'ones':[]},
                   {'frames':[(0,0,4,5)],'ones':[3]}):
            with self.assertRaises(ValueError):m.generate(width=10,height=10,**kw)
        pair=m.generate(width=10,height=10,colour=2,frames=[(0,0,8,9)],
                        ones=[(r,c) for r in range(1,8) for c in range(1,5)])
        counts=Counter(sum(pair['output'],[]))
        self.assertGreater(counts[1],counts[0])
        self.assertEqual(pair['output'],grid(call(solver('93c31fbe'),pair['input'])))

    def test_panel_small_canvas_and_transposed_dot_span(self):
        m=importlib.import_module('tasks.task_94133066')
        for h,w in [(11,11),(12,12),(14,14),(7,11),(11,7),(10,25)]:
            random.seed(40021)
            pair=m.generate(height=h,width=w,transform='transpose')
            self.assertEqual((len(pair['input']),len(pair['input'][0])),(h,w))
            self.assertEqual(pair['output'],grid(call(solver('94133066'),pair['input'])))
        with self.assertRaisesRegex(ValueError,'feasible'):
            m.generate(height=10,width=10)
        with self.assertRaisesRegex(ValueError,'feasible'):
            m.generate(panel_height=26,panel_width=5,transform='rot90')
        for _ in range(10):
            self.assertGreaterEqual(m._sep_axis(20,5,2,True,None,10)[1],14)
            self.assertLessEqual(m._sep_axis(20,5,2,False,None,10)[1],4)

    def test_panel_connected_border_guard_and_corrected_reference_prose(self):
        m=importlib.import_module('tasks.task_94133066')
        cells=[(r,c) for r in range(2,12) for c in range(2,12)
               if (r,c) not in {(6,6),(6,7),(7,6),(7,7)}]
        with self.assertRaisesRegex(ValueError,'unique largest'):
            m.generate(height=30,width=30,panel_top=1,panel_left=1,
                       panel_height=14,panel_width=14,corners=(2,3,4,0),
                       shape_color=5,shape_cells=cells,transform='rot90')
        r=reference('94133066')
        self.assertIn('180° rotation',r['original_teacher_explanation'])
        self.assertIn('required transform is anti-transpose',r['explanation'])
        self.assertEqual(r['explanation_review']['canonical_transforms'],
                         ['transpose','anti_transpose','flip_v','anti_transpose'])
        self.assertTrue(check_reference('94133066')['canonical']['all_exact'])

    def test_noise_triangle_counts_cells_excludes_marker_and_preserves_figure(self):
        m=importlib.import_module('tasks.task_902510d5')
        figure=[(4,4),(5,5),(6,4),(7,5),(8,4)]
        pair=m.generate(width=10,height=10,figure=figure,figure_color=4,
                        corner='tl',corner_color=2,
                        noise=[(0,4,4),(0,5,4),(2,8,2)])
        expected=[[0]*10 for _ in range(10)]
        for r,c in figure:expected[r][c]=4
        for r in range(3):
            for c in range(3-r):expected[r][c]=4
        self.assertEqual(pair['output'],expected)
        self.assertEqual(pair['output'],grid(call(solver('902510d5'),pair['input'])))
        bad=dict(width=6,height=6,figure=[5],figure_color=1,
                 corner='tl',corner_color=2,noise=[(0,3,1)])
        with self.assertRaises(ValueError):m.generate(**bad)
        with self.assertRaises(ValueError):m.generate(**(bad|{'figure':5}))

    def test_noise_triangle_large_figures_scale_with_canvas(self):
        m=importlib.import_module('tasks.task_902510d5')
        random.seed(40000);pair=m.generate(width=30,height=30)
        main=max(m._components(pair['input'],30,30),key=len)
        self.assertGreaterEqual(len(main),45)
        self.assertLessEqual(len(main),112)
        self.assertFalse(m._has_block(main))
        self.assertEqual(pair['output'],grid(call(solver('902510d5'),pair['input'])))

    def test_legend_erases_before_earlier_fill_and_reserves_background(self):
        m=importlib.import_module('tasks.task_9385bd28')
        pair=m.validate()['train'][2]
        # Later 4->0 row erases these pieces before earlier 2->9 and1->6 fills.
        self.assertEqual(pair['input'][4][6],4)
        self.assertEqual(pair['output'][4][6],9)
        self.assertEqual(pair['input'][8][9],4)
        self.assertEqual(pair['output'][8][9],6)
        reserve=m.validate()['train'][0]
        self.assertEqual(reserve['output'][3][5],0)
        self.assertEqual(reserve['output'],grid(call(solver('9385bd28'),reserve['input'])))
        random.seed(40000)
        hard=m.generate(width=10,height=10,require_erase_first=True)
        self.assertEqual(hard['output'],grid(call(solver('9385bd28'),hard['input'])))
        with self.assertRaises(ValueError):m.generate(bg=0,require_erase_first=True)
        with self.assertRaises(ValueError):m.generate(require_erase_first=1)

    def test_legend_explicit_detection_and_input_key_positions(self):
        m=importlib.import_module('tasks.task_9385bd28')
        with self.assertRaisesRegex(ValueError,'identifiable'):
            m.generate(width=10,height=10,bg=0,legend=[(1,0),(2,0)],
                       legend_pos=(8,0),objects=[])
        with self.assertRaisesRegex(ValueError,'plurality'):
            m.generate(width=2,height=2,bg=0,legend=[(1,2),(3,4)],
                       legend_pos=(0,0),objects=[])
        pair=m.validate()['test'][1]
        self.assertEqual(pair['output'][1][1],2)  # Only the original8 block.
        self.assertEqual(pair['output'][4][9],8)  # Newly painted8 is not a new key.
        self.assertEqual(pair['output'],grid(call(solver('9385bd28'),pair['input'])))

    def test_reachable_boundary_marker_floating_and_whole_objects(self):
        m=importlib.import_module('tasks.task_8f3a5a89')
        pair=m.generate(height=10,width=10,objects=[[[0,3,2,5]],[[4,6,5,7]]])
        self.assertEqual(pair['output'][0][4],1)  # Interior of a surviving wall.
        self.assertEqual(pair['output'][4][5],8)  # Floating island gets no frame.
        self.assertEqual(pair['output'][8][1],8)  # The marker is not a wall.
        self.assertEqual(pair['output'],grid(call(solver('8f3a5a89'),pair['input'])))
        pair=m.generate(height=5,width=7,objects=[[[0,3,4,3]]])
        self.assertEqual((len(pair['input']),len(pair['input'][0])),(5,7))
        self.assertEqual(pair['output'][0],[7,7,7,1,8,8,8])
        self.assertEqual(pair['output'],grid(call(solver('8f3a5a89'),pair['input'])))
        boxed=m.generate(height=5,width=5,objects=[[[3,0,3,1],[4,1,4,1]]])
        self.assertEqual({v for row in boxed['output'] for v in row},{6,8})

    def test_reachable_boundary_bounds_before_allocation_and_near_bulges(self):
        m=importlib.import_module('tasks.task_8f3a5a89')
        with patch.object(m,'_rect_cells',side_effect=AssertionError('allocated')):
            with self.assertRaisesRegex(ValueError,'bounds'):
                m.generate(height=10,width=10,objects=[[[0,0,10**9,10**9]]])
        for objects in [2,[2],[[]],[[[True,0,1,1]]]]:
            with self.assertRaises(ValueError):m.generate(height=10,width=10,objects=objects)
        random.seed(4)
        wall={(y,8) for y in range(20)}
        augmented=m._add_bulges(20,20,wall,(19,0))
        self.assertTrue(wall<=augmented)
        self.assertTrue(all(x<=8 for y,x in augmented))

    def test_reachable_boundary_retains_mode_after_failed_proposal(self):
        m=importlib.import_module('tasks.task_8f3a5a89');attempts=[];original=m._try_scene
        def fail_once(h,w,mode):
            attempts.append(mode)
            return None if len(attempts)==1 else original(h,w,mode)
        random.seed(212)
        with patch.object(m,'_try_scene',fail_once):pair=m.generate(height=10,width=10)
        self.assertGreater(len(attempts),1)
        self.assertEqual(len(set(attempts)),1)
        self.assertEqual(pair['output'],grid(call(solver('8f3a5a89'),pair['input'])))

    def test_comb_slot_full_depth_and_near_miss_rejections(self):
        m=importlib.import_module('tasks.task_8b9c3697')
        base=dict(width=20,height=20,background=3,ink=4,
                  combs=[(2,5,'down',1,2,1,3)])
        p=m.generate(**base,pieces=[(9,8,2,2)],targets=[0])
        self.assertEqual(p['output'],grid(call(solver('8b9c3697'),p['input'])))
        self.assertEqual(sum(row.count(2) for row in p['output']),4)
        self.assertEqual(sum(row.count(0) for row in p['output']),10)
        for piece in [(9,8,3,2),(2,0,1,1),(9,8,1,1),(9,7,1,3)]:
            p=m.generate(**base,pieces=[piece])
            self.assertFalse(any(2 in row or 0 in row for row in p['output']))
            self.assertEqual(p['output'],grid(call(solver('8b9c3697'),p['input'])))

    def test_comb_distractor_in_path_becomes_trail(self):
        m=importlib.import_module('tasks.task_8b9c3697')
        base=dict(width=20,height=20,background=3,ink=4,
                  combs=[(2,5,'down',1,2,1,3)])
        p=m.generate(**base,pieces=[(10,8,1,2),(7,8,1,1)],targets=[0,None])
        self.assertEqual(p['output'][7][8],0)
        self.assertEqual(p['output'],grid(call(solver('8b9c3697'),p['input'])))
        p=m.generate(**base,pieces=[])
        self.assertEqual(p['input'],p['output'])

    def test_tally_control_containers_and_maximum_frames(self):
        m=importlib.import_module('tasks.task_8f215267')
        for kw in [dict(frame_colors=3),dict(frame_colors=[[1]]),
                   dict(frame_colors={1,2}),dict(counts=2),dict(counts={1,2}),
                   dict(distractor_colors=4),dict(distractor_colors={3,4}),
                   dict(num_frames=8,frame_height=3),dict(num_frames=6)]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):m.generate(**kw)
        random.seed(41000)
        p=m.generate(num_frames=7,frame_height=3,frame_width=7)
        self.assertEqual(p['output'],grid(call(solver('8f215267'),p['input'])))

    def test_tally_dense_valid_counts_and_nonhollow_border_shape(self):
        m=importlib.import_module('tasks.task_8f215267')
        random.seed(0)
        p=m.generate(frame_width=27,frame_height=9,num_frames=2,counts=[12,12])
        self.assertEqual(p['output'],grid(call(solver('8f215267'),p['input'])))
        with self.assertRaisesRegex(ValueError,'capacity'):
            m.generate(frame_width=27,frame_height=9,num_frames=2,counts=[13,12])
        p=m.generate(width=24,height=20,background=0,left=1,top=1,
                     frame_colors=[2],shapes=[(2,8,15,['#####','##..#','#...#','#####'])])
        self.assertEqual(p['output'],grid(call(solver('8f215267'),p['input'])))
        self.assertEqual(p['output'][3][9],2)
        self.assertEqual(sum(p['output'][3][2:11]),2)

    def test_vertical_symmetry_canonical_latents_need_no_replay(self):
        m=importlib.import_module('tasks.task_8e5c0c38')
        with patch.object(m,'_replay',side_effect=AssertionError('replay used')):
            result=m.validate()
        self.assertEqual(result,reference('8e5c0c38')['canonical'])

    def test_vertical_symmetry_uses_leftmost_tied_axis(self):
        m=importlib.import_module('tasks.task_8e5c0c38')
        shape=dict(colour=2,top=2,left=2,w=3,
                   core=[(0,0),(0,2),(1,0),(1,2)],extras=[(0,3),(1,3)])
        p=m.generate(width=8,height=8,background=0,shapes=[shape])
        self.assertEqual(p['output'],grid(call(solver('8e5c0c38'),p['input'])))
        self.assertEqual(p['output'][2][2:6],[2,0,2,0])
        # The same input also has a tied axis at local s=3, but it is later.
        wrong={**shape,'w':4,'core':[(0,0),(0,3),(1,0),(1,3)],
               'extras':[(0,2),(1,2)]}
        with self.assertRaisesRegex(ValueError,'leftmost best'):
            m.generate(width=8,height=8,background=0,shapes=[wrong])
        for kw in [dict(width=8,height=8,num_shapes=1,tie_rate=1),
                   dict(width=30,height=30,num_shapes=4,tie_rate=1),
                   dict(tie_rate=0)]:
            random.seed(41000);p=m.generate(**kw)
            self.assertEqual(p['output'],grid(call(solver('8e5c0c38'),p['input'])))

    def test_vertical_symmetry_explicit_types_and_json_axis_keys(self):
        m=importlib.import_module('tasks.task_8e5c0c38')
        p=m.generate(input_rows=['000','010','011'],background=0,axes={'1':2})
        self.assertEqual(p['output'],[[0,0,0],[0,1,0],[0,1,0]])
        for kw in [dict(colours=5),dict(shapes=[1]),dict(shapes=5),
                   dict(tie_rate=True),dict(tie_rate=-0.1),dict(tie_rate=float('nan')),
                   dict(input_rows=['000','010','011'],background=0,axes={'1':2,1:2}),
                   dict(input_rows=[123],background=0,axes={1:2}),
                   dict(input_rows=['000','010','011'],background=0,axes=5),
                   dict(width=10,height=10,background=0,shapes=[dict(colour=2,
                        top=1,left=1,w=3,core=[5],extras=[])]),
                   dict(width=10,height=10,shapes=[dict(colour=[2])])]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):m.generate(**kw)

    def test_scaled_assembly_retains_scale_after_rejected_render(self):
        m=importlib.import_module('tasks.task_898e7135');original=m._zero_majority
        for seed in range(41000,41008):
            calls=[]
            def reject_first(g):
                calls.append(True)
                return False if len(calls)==1 else original(g)
            expected=random.Random(seed).choice([2,2,3]);random.seed(seed)
            with patch.object(m,'_zero_majority',side_effect=reject_first):
                params=m._sample(None,None,None,None,None)
            self.assertGreaterEqual(len(calls),2)
            self.assertEqual(params[2],expected)

    def test_scaled_assembly_explicit_noise_and_scale_extensions(self):
        m=importlib.import_module('tasks.task_898e7135')
        cases=[dict(height=30,width=30,k=2,
                    board=['#####','#1###','#####','###1#','#####'],
                    board_colour=2,board_pos=[0,0],
                    pieces=[[0,7,1,['1']],[3,7,1,['1']]],noise_colour=7,
                    noise=[[25,25],[25,26],[26,25],[26,26],[20,20]]),
               dict(height=20,width=20,k=5,
                    board=['######','#1####','######','######','######','######'],
                    board_colour=2,board_pos=[0,0],pieces=[[0,8,1,['1']]],
                    noise_colour=7,noise=[[18,18]])]
        for kw in cases:
            p=m.generate(**kw)
            self.assertEqual(p['output'],grid(call(solver('898e7135'),p['input'])))
        self.assertEqual(len(p['output']),30)
        # Without an isolated dot the blob does not identify itself as noise.
        cases[0]['noise'].pop()
        with self.assertRaisesRegex(ValueError,'isolated single dot'):
            m.generate(**cases[0])

    def test_partial_glyph_requires_joint_hint_evidence(self):
        m=importlib.import_module('tasks.task_8a6d367c')
        glyphs=[['101','010','101'],['001','010','101'],['101','010','100']]
        kw=dict(width=20,height=20,glyphs=glyphs,colors=[1,2,3],
                glyph_cols=[1,5,9],glyph_top=1,frame_top=6,frame_left=2,
                cell_h=2,cell_w=2,frame_color=4,fill_color=5,target=0,
                hints=[(0,0),(2,2)])
        p=m.generate(**kw)
        self.assertEqual(p['output'],grid(call(solver('8a6d367c'),p['input'])))
        for hint in kw['hints']:
            with self.assertRaisesRegex(ValueError,'more than one glyph'):
                m.generate(**{**kw,'hints':[hint]})
        for field,value in [('hints',5),('hints',(0,0)),('colors',1),
                            ('glyph_cols',2),('glyphs',[[1,0,1]]),
                            ('num_glyphs',3.0),('num_hints',2.0),
                            ('glyph_h',3.0),('glyph_w',3.0)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.generate(**{**kw,field:value})

    def test_partial_glyph_dense_requested_controls(self):
        m=importlib.import_module('tasks.task_8a6d367c')
        random.seed(41000)
        p=m.generate(glyph_h=3,glyph_w=3,num_glyphs=6,num_hints=6)
        self.assertEqual(p['output'],grid(call(solver('8a6d367c'),p['input'])))
        for kw in [dict(num_hints=1),dict(cell_h=6,cell_w=6,num_hints=2)]:
            random.seed(41000);p=m.generate(**kw)
            self.assertEqual(p['output'],grid(call(solver('8a6d367c'),p['input'])))

    def test_frames_reject_unrecoverable_explicit_divider(self):
        frames=importlib.import_module('tasks.task_89565ca0')
        kw=dict(height=20,width=20,noise_color=5,
                frames=[(1,0,0,8,8,[('v',4,0,8)])],
                noise=[(r,4) for r in range(2,7)]+[(12,c) for c in range(0,20,2)])
        with self.assertRaisesRegex(ValueError,'visible evidence'):
            frames.generate(**kw)
        # A two-cell covered run with a continuing wall is recoverable.
        kw['noise']=[(3,4),(4,4)]+[(12,c) for c in range(0,20,2)]
        p=frames.generate(**kw)
        self.assertEqual(p['output'],[[1,1]])
        self.assertEqual(p['output'],grid(call(solver('89565ca0'),p['input'])))

    def test_frames_count_survives_rejected_placement(self):
        frames=importlib.import_module('tasks.task_89565ca0')
        original=frames._place_frames
        for seed in range(41000,41008):
            seen=[]
            def reject_first(h,w,counts,tie):
                seen.append(len(counts))
                return None if len(seen)==1 else original(h,w,counts,tie)
            expected=random.Random(seed).choice([3,4,5]);random.seed(seed)
            with patch.object(frames,'_place_frames',side_effect=reject_first):
                p=frames.generate()
            self.assertGreaterEqual(len(seen),2)
            self.assertEqual(set(seen),{expected})
            self.assertEqual(len(p['output']),expected)

    def test_frames_asymmetric_small_five_frame_controls(self):
        frames=importlib.import_module('tasks.task_89565ca0')
        for h,w in [(14,22),(22,14),(18,18)]:
            random.seed(41000)
            p=frames.generate(height=h,width=w,num_frames=5)
            self.assertEqual((len(p['input']),len(p['input'][0])),(h,w))
            self.assertEqual(len(p['output']),5)
            self.assertEqual(p['output'],grid(call(solver('89565ca0'),p['input'])))
        with self.assertRaises(ValueError):
            frames.generate(height=14,width=21,num_frames=5)

    def test_snake_target_rejects_metric_dependent_distractor(self):
        snake=importlib.import_module('tasks.task_88bcf3b4')
        scene=dict(line_colour=1,end=(10,10),direction=(1,0),length=5,
                   side=(0,1),snake_colour=2,
                   snake_cells=[(10,11),(9,12),(8,12),(7,13)],
                   target_colour=3,target_cells=[(15,15)])
        # Target offset (5,4) is closer in Chebyshev distance but farther
        # in Manhattan distance than the distractor at offset (0,6).
        self.assertFalse(snake._nearest_is_robust(scene,[[(10,17)]]))
        p=snake.generate(width=30,height=30,background=0,scenes=[scene],
                         extras=[(6,[(10,17)])])
        self.assertFalse(snake._reading_is_unique(p['input'],0,[scene]))
        self.assertTrue(snake._nearest_is_robust(scene,[[(24,24)]]))
        p=snake.generate(width=30,height=30,background=0,scenes=[scene],
                         extras=[(6,[(24,24)])])
        self.assertTrue(snake._reading_is_unique(p['input'],0,[scene]))

    def test_snake_count_is_retained_after_rejected_attempt(self):
        snake=importlib.import_module('tasks.task_88bcf3b4')
        original=snake._reading_is_unique
        for seed in range(41000,41008):
            calls=[]
            def reject_first(*args,**kwargs):
                calls.append(True)
                return False if len(calls)==1 else original(*args,**kwargs)
            expected=random.Random(seed).choice((1,1,1,2,2,3))
            random.seed(seed)
            with patch.object(snake,'_reading_is_unique',side_effect=reject_first):
                _,_,_,scenes,_=snake._sample(None,None,None,None)
            self.assertGreaterEqual(len(calls),2)
            self.assertEqual(len(scenes),expected)

    def test_snake_explicit_geometry_rejects_missing_and_bad_cells(self):
        import copy
        snake=importlib.import_module('tasks.task_88bcf3b4')
        base=dict(line_colour=8,end=[3,5],direction=[-1,0],length=4,
                  side=[0,-1],snake_colour=4,
                  snake_cells=[[3,3],[3,4],[4,3],[5,2],[5,3],[6,1]],
                  target_colour=2,target_cells=[[1,5]])
        variants=[]
        missing=copy.deepcopy(base);del missing['side'];variants.append(missing)
        for key,value in [('end',3),('snake_cells',5),
                          ('snake_cells',[[3,4],[3,4]]),
                          ('target_cells',[[3,5]]),
                          ('target_cells',[[1,5],[0,0]])]:
            item=copy.deepcopy(base);item[key]=value;variants.append(item)
        for item in variants:
            with self.subTest(scene=item),self.assertRaises(ValueError):
                snake.generate(width=7,height=7,background=0,scenes=[item])
        with self.assertRaises(ValueError):
            snake.generate(width=7,height=7,background=0,scenes=[base],extras=3)

    def test_sliding_wall_markers_preserve_interior_pillars(self):
        sliding=importlib.import_module('tasks.task_88e364bc')
        original_attempt,original_place=sliding._attempt,sliding._place_shape
        successful_shapes=[]
        def track_attempt(*args,**kwargs):
            successful_shapes.clear()
            return original_attempt(*args,**kwargs)
        def track_place(*args,**kwargs):
            shape=original_place(*args,**kwargs)
            if shape is not None:successful_shapes.append(shape)
            return shape
        with patch.object(sliding,'_attempt',side_effect=track_attempt), \
             patch.object(sliding,'_place_shape',side_effect=track_place):
            for seed in range(42000,42010):
                random.seed(seed)
                pair=sliding.generate(colours=[8],pillars=True,
                                      wall_marker=True,touching=False)
                starts={(r,c) for r,row in enumerate(pair['input'])
                        for c,v in enumerate(row) if v==4}
                rings=set().union(*(s['ring'] for s in successful_shapes))
                pillars=set().union(*(s['pillar'] for s in successful_shapes))
                self.assertTrue(pillars)
                self.assertEqual(len(starts&rings),1)
                self.assertFalse(starts&pillars)
                for r,c in pillars:
                    self.assertEqual(pair['input'][r][c],8)
                    self.assertEqual(pair['output'][r][c],8)
                self.assertEqual(pair['output'],
                                 grid(call(solver('88e364bc'),pair['input'])))

    def test_sliding_replay_requires_markers_and_separate_paths(self):
        sliding=importlib.import_module('tasks.task_88e364bc')
        for markers in (None,[],3):
            with self.subTest(markers=markers),self.assertRaises(ValueError):
                sliding.generate(layout=['00000']*3,markers=markers)
        with self.assertRaisesRegex(ValueError,'another marker'):
            sliding.generate(layout=['00000']*3,
                             markers=[(0,0,0,1),(0,2,1,0)])

    def test_sliding_bad_colour_types_reject_cleanly(self):
        sliding=importlib.import_module('tasks.task_88e364bc')
        for colours in ([[3]],[{}],[True],[3.5]):
            with self.subTest(colours=colours),self.assertRaises(ValueError):
                sliding.generate(colours=colours)

    def test_slab_random_retries_keep_selected_piece_count(self):
        slab=importlib.import_module('tasks.task_83eb0a57')
        for seed in range(41000,41012):
            expected=random.Random(seed).choice([1,2,2,3,3,4])
            random.seed(seed)
            pair=slab.generate()
            g=pair['input'];bg=Counter(sum(g,[])).most_common(1)[0][0]
            pending={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
            components=0
            while pending:
                components+=1;stack=[pending.pop()]
                while stack:
                    r,c=stack.pop()
                    for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if p in pending:
                            pending.remove(p);stack.append(p)
            self.assertEqual(components,expected+1)
            self.assertEqual(pair['output'],grid(call(solver('83eb0a57'),g)))

    def test_slab_explicit_offset_defines_visible_host_keys(self):
        slab=importlib.import_module('tasks.task_83eb0a57')
        pair=slab.generate(size=[30,30],bg=8,host=[2,15,9,5,1],
                           pieces=[[16,5,[[3,3,3],[2,2,2],[3,3,3]],3,0,1]])
        self.assertEqual(pair['output'][0][1:4],[3,3,3])
        self.assertEqual(pair['output'][1][1:4],[2,2,2])
        self.assertEqual(pair['output'],grid(call(solver('83eb0a57'),pair['input'])))

    def test_slab_explicit_overlap_and_more_than_four_pieces(self):
        slab=importlib.import_module('tasks.task_83eb0a57')
        p=slab.generate(size=[30,30],bg=0,host=[0,0,8,8,1],pieces=[
            [12,0,[[3]*4,[2]*4,[2]*4],3,1,1],
            [12,8,[[4]*3,[5]*3],5,3,3]])
        self.assertEqual(p['output'][3][3:6],[4,4,4])
        self.assertEqual(p['output'],grid(call(solver('83eb0a57'),p['input'])))
        parts=[[22+3*(i//3),9*(i%3),[[i+2]+[1]*(i+1)],i+2,2+2*i,2]
               for i in range(6)]
        p=slab.generate(size=[30,30],bg=0,host=[0,0,20,20,1],
                        pieces=parts,num_pieces=6)
        self.assertEqual(p['output'],grid(call(solver('83eb0a57'),p['input'])))

    def test_slab_malformed_patterns_reject_cleanly(self):
        slab=importlib.import_module('tasks.task_83eb0a57')
        for pat in (5,[5],[[3,3],5],[[3,3],[]]):
            with self.subTest(pattern=pat),self.assertRaises(ValueError):
                slab.generate(size=[30,30],bg=8,host=[2,15,9,5,1],
                              pieces=[[16,5,pat,3,1,1]])
        with self.assertRaises(ValueError):
            slab.generate(bg=8,host=[2,15,9,5,1],pieces=7,num_pieces=1)

    def test_border_cycle_preserves_skeleton_and_palette_direction(self):
        cycle=importlib.import_module('tasks.task_880c1354')
        colours=[0,9,2,6,5,3,8,1]
        transfer={col:colours[i-1] for i,col in enumerate(colours)}
        for width,height in ((30,30),(30,6),(6,30)):
            random.seed(44000+width)
            pair=cycle.generate(width=width,height=height,colors=colours)
            self.assertEqual((len(pair['input']),len(pair['input'][0])),
                             (height,width))
            self.assertEqual(set(sum(pair['input'],[]))-{4,7},set(colours))
            self.assertEqual(pair['output'],
                             [[transfer.get(c,c) for c in row]
                              for row in pair['input']])
            self.assertEqual(pair['output'],
                             grid(call(solver('880c1354'),pair['input'])))

    def test_border_cycle_small_four_region_controls(self):
        cycle=importlib.import_module('tasks.task_880c1354')
        for h in (6,7):
            for seed in range(6):
                random.seed(42000+seed)
                p=cycle.generate(width=6,height=h,num_regions=4)
                self.assertEqual(len(set(sum(p['input'],[]))-{4,7}),4)
                self.assertEqual(p['output'],
                                 grid(call(solver('880c1354'),p['input'])))

    def test_border_cycle_malformed_layout_rejects_cleanly(self):
        cycle=importlib.import_module('tasks.task_880c1354')
        for layout in ([7], [True], [[]], [None], ['aaa',7,'bbb']):
            with self.subTest(layout=layout),self.assertRaises(ValueError):
                cycle.generate(layout=layout,colors=[1,2])

    def test_legend_sampling_reaches_compact_native_layouts(self):
        legend=importlib.import_module('tasks.task_845d6e51')
        strips=set()
        compact=False
        for seed in range(41000,41100):
            random.seed(seed)
            p=legend.generate()
            g=p['input']
            wr=max(r for r,row in enumerate(g) if 5 in row)
            wc=max(c for row in g for c,v in enumerate(row) if v==5)
            strips.add(len(g[0])-wc-1)
            compact |= len(g)==10 and wr==3
            self.assertEqual(p['output'],grid(call(solver('845d6e51'),g)))
        self.assertTrue({2,3,4,5}.issubset(strips))
        self.assertTrue(compact)

    def test_legend_malformed_explicit_shapes_reject_cleanly(self):
        legend=importlib.import_module('tasks.task_845d6e51')
        base=dict(width=10,height=10,wall_row=3,wall_col=7,
                  legend=[(2,[(0,0),(1,0)]),(4,[(0,2),(0,3),(1,2)])])
        for malformed in (3,[3],[(0,3)],[(0,[5,6])],[(0,[(1,)])]):
            with self.subTest(malformed=malformed),self.assertRaises(ValueError):
                legend.generate(**base,greens=malformed)

    def test_legend_dense_count_is_honoured(self):
        legend=importlib.import_module('tasks.task_845d6e51')
        random.seed(43000)
        p=legend.generate(width=30,height=30,num_greens=40)
        remaining={(r,c) for r,row in enumerate(p['input'])
                   for c,v in enumerate(row) if v==3}
        count=0
        while remaining:
            stack=[remaining.pop()]
            count+=1
            while stack:
                r,c=stack.pop()
                for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if q in remaining:
                        remaining.remove(q)
                        stack.append(q)
        self.assertEqual(count,40)
        self.assertEqual(p['output'],grid(call(solver('845d6e51'),p['input'])))

    def test_stencil_partial_masks_respect_output_bounds(self):
        stamps=importlib.import_module('tasks.task_bf45cf4b')
        mask=[[1,1],[1,0],[1,1],[0,1],[1,1],[1,0],[1,1]]
        for candidate in (mask,list(map(list,zip(*mask)))):
            for seed in range(5):
                random.seed(46000+seed)
                p=stamps.generate(mask=candidate)
                self.assertLessEqual(len(p['output']),30)
                self.assertLessEqual(len(p['output'][0]),30)
                self.assertEqual(p['output'],grid(call(solver('bf45cf4b'),p['input'])))
        for candidate in ([[1,1]]*11,[[1]*11]*2):
            with self.assertRaisesRegex(ValueError,'mask too large'):
                stamps.generate(mask=candidate)

    def test_stencil_tile_identification_keeps_valid_islands(self):
        stamps=importlib.import_module('tasks.task_bf45cf4b')
        tile=[[5]*7]+[[5]+[0]*5+[5] for _ in range(5)]+[[5]*7]
        for r in range(2,5):
            for c in range(2,5):tile[r][c]=6+(r+c)%2
        with self.assertRaisesRegex(ValueError,'identifiable'):
            stamps.generate(width=12,height=12,background=0,tile=tile,
                            mask=[[1,0],[0,1]],stencil_color=1)
        tile=[[0]*7 for _ in range(7)]
        for r in range(7):
            for c in range(7):
                if r in (0,6) or c in (0,6):tile[r][c]=5+(r+c)%2
        tile[3][3]=7
        p=stamps.generate(width=20,height=20,background=0,tile=tile,
                         mask=[[1,0],[0,1]],stencil_color=1)
        self.assertEqual(p['output'][3][3],7)
        self.assertEqual(p['output'][10][10],7)
        self.assertEqual(p['output'],grid(call(solver('bf45cf4b'),p['input'])))
        p=stamps.generate(width=10,height=10,background=0,tile=[[1,2]],
                         mask=[[1,0,1]],stencil_color=3)
        self.assertEqual(p['output'],[[1,2,0,0,1,2]])

    def test_ring_replay_checks_visible_marker_witnesses(self):
        import copy
        rings=importlib.import_module('tasks.task_8b7bacbf')
        with self.assertRaisesRegex(ValueError,'visible marker path'):
            rings.generate(input_grid=[[0,2,0],[2,0,2],[0,2,0]],
                           fills=[(1,1,4)])
        original=rings.generate
        calls=[]
        def capture(*args,**kwargs):
            calls.append(copy.deepcopy(kwargs))
            return original(*args,**kwargs)
        with patch.object(rings,'generate',side_effect=capture):
            rings.validate()
        kw=copy.deepcopy(calls[0])
        kw['fills']=kw['fills'][1:]
        with self.assertRaisesRegex(ValueError,'omit'):
            original(**kw)
        kw=copy.deepcopy(calls[0])
        kw['fills']=kw['fills']+[kw['fills'][0]]
        with self.assertRaisesRegex(ValueError,'only once'):
            original(**kw)

    def test_orthogonal_strip_can_cross_diagonal_route(self):
        rings=importlib.import_module('tasks.task_8b7bacbf')
        body={(r,r) for r in range(2,20)}
        site=[(r,10) for r in range(8,13)]
        local={(r,r) for r in range(8,13)}
        self.assertTrue(rings._site_ok(site,local,body,(2,2),set(),set(),30,30))
        # Remote contact is still forbidden; only the local crossing stretch
        # may touch the strip, and only its central cell may be overwritten.
        self.assertFalse(rings._site_ok(site,local,body|{(8,11)},(2,2),
                                       set(),set(),30,30))

    def test_line_repairs_reject_unjustified_explicit_edits(self):
        lines=importlib.import_module('tasks.task_7b80bb43')
        base=dict(width=10,height=10,background=0,color=5)
        with self.assertRaisesRegex(ValueError,'at least one line'):
            lines.generate(**base,lines=[],diagonals=[(2,2,1,1,2)])
        with self.assertRaisesRegex(ValueError,'declared edits'):
            lines.generate(**base,lines=[('h',4,0,9)],
                           diagonals=[(4,4,1,1,1)])
        with self.assertRaisesRegex(ValueError,'declared edits'):
            lines.generate(**base,lines=[('h',4,0,9)],
                           diagonals=[(1,1,1,1,2)],bridges=[('h',2,5,6)])
        p=lines.generate(**base,lines=[('h',4,0,9)],diagonals=[(1,1,1,1,2)])
        self.assertEqual(p['output'][4],[5]*10)
        self.assertEqual(p['output'][1][1],0)
        self.assertEqual(p['output'],grid(call(solver('7b80bb43'),p['input'])))

    def test_gravity_gap_stacking_and_explicit_domain(self):
        gravity=importlib.import_module('tasks.task_825aa9e9')
        p=gravity.generate(width=5,height=8,heights=[1]*5,ground_colors=5,
                          movers=[(3,[(0,2)]),(3,[(2,2)])])
        self.assertEqual(p['output'][4][2],3)
        self.assertEqual(p['output'][5][2],3)
        self.assertEqual(p['output'][6][2],7)
        self.assertEqual(p['output'][7][2],5)
        lateral=gravity.generate(width=5,height=6,heights=[4,0,0,0,4],
                                 ground_colors=5,movers=[(3,[(0,1)])])
        self.assertEqual(lateral['output'][4][1],3)
        self.assertEqual(lateral['output'][4][0],5)
        self.assertEqual(lateral['output'],
                         grid(call(solver('825aa9e9'),lateral['input'])))
        with self.assertRaisesRegex(ValueError,'visible ground'):
            gravity.generate(heights=[0]*5,ground_colors=3)
        with self.assertRaisesRegex(ValueError,'eight movers'):
            gravity.generate(width=30,height=10,heights=[1]*30,ground_colors=5,
                             movers=[(3,[(0,2*k)]) for k in range(9)])

    def test_diamond_endpoint_rays_and_clipped_segments(self):
        rays=importlib.import_module('tasks.task_80a900e0')
        p=rays.generate(width=14,height=20,
            patterns=[(10,6,3,[(-1,1,8),(1,-1,8)])])
        self.assertEqual(p['output'][6][8],8)
        self.assertEqual(p['output'][8][10],8)
        self.assertEqual(p['output'][7][9],1)  # Middle segment cell emits no ray.
        self.assertEqual(p['output'][13][3],1)
        clipped=rays.generate(width=29,height=29,
            patterns=[(2,14,3,[(-1,1,2),(1,-1,2)])])
        self.assertEqual(clipped['output'][0][18],2)
        self.assertEqual(clipped['output'],grid(call(solver('80a900e0'),clipped['input'])))
        for seed in range(3):
            random.seed(42000+seed)
            p=rays.generate(width=30,height=30,num_patterns=4)
            self.assertEqual(p['output'],grid(call(solver('80a900e0'),p['input'])))

    def test_branch_patch_textures_reject_silent_numeric_coercion(self):
        import copy
        branch=importlib.import_module('tasks.task_800d221b')
        original=branch.generate
        calls=[]
        def capture(*args,**kwargs):
            calls.append(copy.deepcopy(kwargs))
            return original(*args,**kwargs)
        with patch.object(branch,'generate',side_effect=capture):
            branch.validate()
        for bad in (True,2.9,'2'):
            kw=copy.deepcopy(calls[0])
            top,left,rows=kw['patches'][0]
            rows=[[int(v) for v in row] for row in rows]
            rows[0][0]=bad
            kw['patches'][0]=(top,left,rows)
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                original(**kw)
        for bad in (True,2.9,'2',None):
            kw=copy.deepcopy(calls[0])
            i,points=kw['paths'][0]
            points=[list(p) for p in points]
            points[0][0]=bad
            kw['paths'][0]=(i,points)
            with self.subTest(waypoint=bad),self.assertRaises(ValueError):
                original(**kw)
        for field,value in [('patches',[None]),('paths',[None])]:
            kw=copy.deepcopy(calls[0])
            kw[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                original(**kw)

    def test_fresh_hole_shapes_long_snakes_and_proximity_counts(self):
        holes=importlib.import_module('tasks.task_67e490f4')
        random.seed(30000)
        bank=holes._shape_bank('procedural')
        original={holes._canon(holes._cells(p)) for p in holes._LIB}
        keys={holes._canon(holes._cells(p)) for p in bank}
        self.assertEqual(len(keys),10)
        self.assertFalse(keys & original)
        p=holes.generate(width=30,height=30,shape_mode='procedural',allow_unmatched=True)
        self.assertEqual(p['output'],grid(call(solver('67e490f4'),p['input'])))
        snake=importlib.import_module('tasks.task_696d4842')
        random.seed(30000)
        observed=[];render=snake._render
        def capture(*args):
            observed.append(args[2])
            return render(*args)
        with patch.object(snake,'_render',side_effect=capture):
            p=snake.generate(height=30,width=30,num_paths=2,extension=12,num_segments=4)
        self.assertEqual(len(observed[-1]),2)
        for path in observed[-1]:
            self.assertEqual(path['n'],12)
            self.assertEqual(len(path['segments']),4)
        self.assertEqual(p['output'],grid(call(solver('696d4842'),p['input'])))
        proximity=importlib.import_module('tasks.task_6df30ad6')
        # Two markers cannot be assigned three or four distinct colours.
        for seed in range(20):
            random.seed(seed)
            p=proximity.generate(width=20,height=20,num_markers=2)
            self.assertEqual(sum(v not in (0,5) for row in p['input'] for v in row),2)
            self.assertEqual(p['output'],grid(call(solver('6df30ad6'),p['input'])))
        random.seed(30060)
        p=proximity.generate(width=30,height=30,shape_cells=100,num_colors=8,
                             num_markers=32,target_color=7)
        self.assertEqual(sum(v==5 for row in p['input'] for v in row),100)
        self.assertEqual(sum(v==7 for row in p['output'] for v in row),100)
        self.assertEqual(p['output'],grid(call(solver('6df30ad6'),p['input'])))
        midline=importlib.import_module('tasks.task_66ac4c3b')
        with self.assertRaises(ValueError):
            midline.generate(period=2.5)

    def test_large_equal_area_shapes_and_panel_device_controls(self):
        comparison=importlib.import_module('tasks.task_6165ea8f')
        random.seed(30000)
        p=comparison.generate(height=30,width=30,n=7,num_classes=3,shape_cells=25)
        counts=Counter(v for row in p['input'] for v in row if v!=0)
        self.assertEqual(set(counts.values()),{26})  # Shape plus legend pixel.
        self.assertEqual(p['output'],grid(call(solver('6165ea8f'),p['input'])))
        with self.assertRaises(ValueError):
            comparison.generate(shape_cells=2)
        panels=importlib.import_module('tasks.task_6350f1f4')
        # Requested counts force size two; sampling size six first used to fail.
        for seed in range(10):
            random.seed(seed)
            p=panels.generate(rows=10,cols=10)
            self.assertEqual((len(p['input']),len(p['input'][0])),(29,29))
            self.assertEqual(p['output'],grid(call(solver('6350f1f4'),p['input'])))
        device=importlib.import_module('tasks.task_64efde09')
        for seed in range(20):
            random.seed(seed)
            far,near=device._sample_templates(4,None,[1]*4)
            device._check_templates(far,near)
            self.assertFalse(device._doubled_end(far))
        random.seed(30080)
        p=device.generate(width=30,height=30,near=[1]*4,num_devices=4,num_markers=2)
        self.assertEqual(p['output'],grid(call(solver('64efde09'),p['input'])))
        motif=importlib.import_module('tasks.task_65b59efc')
        with self.assertRaises(ValueError):
            motif.generate(k=3,trailing=2)
        with self.assertRaises(ValueError):
            motif._check_mask([[1.0,0,0],[0,0,0],[0,0,0]],3,'motif')

    def test_panel_frame_mirror_and_exact_tiling_controls(self):
        panel=importlib.import_module('tasks.task_5a719d11')
        with self.assertRaises(ValueError):
            panel.generate(panel_width=7.5)
        frame=importlib.import_module('tasks.task_5adee1b2')
        with self.assertRaisesRegex(ValueError,'disjoint'):
            frame.generate(height=20,width=20,legend=[(2,3)],
                shapes=[(3,3,2,['##','##']),(3,5,2,['##','##'])])
        mirror=importlib.import_module('tasks.task_5b692c0f')
        with self.assertRaisesRegex(ValueError,'intact side'):
            mirror.generate(height=12,width=12,shapes=[
                dict(top=2,left=2,vertical=True,axis=4,side=-1,
                     rows=['11411','11414','11411'])])
        tiling=importlib.import_module('tasks.task_5dbc8537')
        with self.assertRaises(ValueError):
            tiling.generate(num_pieces=2)
        random.seed(30000)
        observed=[]
        sample=tiling._sample_scene
        def capture(*args,**kwargs):
            scene=sample(*args,**kwargs)
            if scene is not None:observed.append(scene)
            return scene
        with patch.object(tiling,'_sample_scene',side_effect=capture):
            p=tiling.generate(width=30,height=30,side='right',extent=9,
                              background=0,frame=8,num_pieces=12)
        self.assertEqual(len(observed[-1][-1]),12)
        self.assertEqual((len(p['output']),len(p['output'][0])),(30,9))
        self.assertEqual(p['output'],grid(call(solver('5dbc8537'),p['input'])))
        # Identical geometric tiles with different paint admit two answers.
        self.assertFalse(tiling._unique_fill({(0,0),(0,1)},[[[2]],[[3]]]))
        self.assertTrue(tiling._unique_fill({(0,0),(0,1)},[[[2]],[[2]]]))

    def test_motif_counting_glyph_and_beam_controls(self):
        motif=importlib.import_module('tasks.task_5833af48')
        with self.assertRaises(ValueError):
            motif.generate(scale=1.5)
        counter=importlib.import_module('tasks.task_58490d8a')
        with self.assertRaises(ValueError):
            counter._sprite([[1,0,0],[0,0,1]])
        glyph=importlib.import_module('tasks.task_58f5dbd5')
        with self.assertRaises(ValueError):
            glyph._parse('111/.z./111')
        cases=[
            ('5833af48',dict(height=30,width=30,color=7,scale=3)),
            ('58490d8a',dict(height=30,width=30,background=7,legend=[2,4],
                             counts=[8,1],num_distractors=1,sprite_mode='procedural')),
            ('58f5dbd5',dict(height=30,width=30,bg=8,rows=3,cols=2,
                             num_distractors=2,side='bottom')),
            ('5961cc34',dict(height=30,width=30,n_hits=4,n_distractors=2,direction='left')),
        ]
        for tid,kwargs in cases:
            random.seed(30000)
            module=importlib.import_module('tasks.task_'+tid)
            p=call(module.generate,seconds=20,**kwargs)
            self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
            self.assertEqual(p['output'],grid(call(solver(tid),p['input'])),tid)
            if tid=='58f5dbd5':
                self.assertEqual((len(p['output']),len(p['output'][0])),(19,13))

    def test_long_walk_large_mover_and_marker_line_controls(self):
        walk=importlib.import_module('tasks.task_5545f144')
        arrow=[(0,0),(-1,-1),(-1,1)]
        random.seed(30000)
        # Choose the downward quadrant, which has room for this long lattice.
        with patch.object(walk.random,'choice',return_value=1):
            path=walk._lattice_path(30,30,arrow,(3,3),(0,1),20)
        self.assertEqual(len(path),20)
        self.assertEqual(walk._walk((3,3),(0,1),path,30,30),(path,set()))
        p=walk.generate(height=30,width=14,num_panels=2,num_eats=12)
        self.assertEqual((len(p['input'][0]),len(p['output'][0])),(29,14))
        self.assertEqual(p['output'],grid(call(solver('5545f144'),p['input'])))
        push=importlib.import_module('tasks.task_5623160b')
        random.seed(30000)
        p=push.generate(width=30,height=30,num_anchors=1,num_movers=2,num_distractors=0,mover_size=19)
        counts=Counter(v for row in p['input'] for v in row if v not in (7,9))
        self.assertEqual(sorted(counts.values()),[19,19])
        self.assertEqual(p['output'],grid(call(solver('5623160b'),p['input'])))
        marker=importlib.import_module('tasks.task_581f7754')
        with self.assertRaisesRegex(ValueError,'exactly one border'):
            marker.generate(width=10,height=10,background=0,markers=[(0,0,2)],shapes=[(3,3,['12'])])
        corner=importlib.import_module('tasks.task_54dc2872')
        with self.assertRaisesRegex(ValueError,'overlap or touch'):
            corner.generate(width=10,height=10,shapes=[(3,3,1,1,3,3,2,4,(3,4))])

    def test_episode_labels_preserve_approved_correction_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=b.OUT;b.OUT=Path(directory);(b.OUT/'pools').mkdir()
            try:
                tid='581f7754';module=importlib.import_module('tasks.task_'+tid);rows=[]
                for seed_ in range(30):
                    random.seed(seed_);p=module.generate(width=30,height=24)
                    rows.append(dict(task_id=tid,**p,seed=seed_,parameters='{}',generator_mode='standalone_constructor',input_hash=b.digest(p['input']),canonical_input_hash=b.canonical_input(p['input']),split='train',stratum=b.stratum(p)))
                pq.write_table(b.pa.Table.from_pylist(rows),b.OUT/'pools'/f'{tid}.parquet')
                report=b.make_episodes((tid,{'train':{rows[0]['stratum']:2}}))
                self.assertEqual(report['splits']['train']['fresh_episodes'],2)
                saved=pq.read_table(b.OUT/'data'/'train'/f'{tid}.parquet').to_pylist()
                self.assertTrue(saved)
                for row in saved:
                    self.assertEqual(row['fixture_basis'],'teaching_fixture')
                    self.assertTrue(row['corrected_teaching_fixture'])
                    self.assertEqual(row['correction_source'],fixture_basis(tid)['source'])
                    self.assertNotIn('corrected_teaching_fixture',row['prompt'])
            finally:b.OUT=previous

    def test_corrected_teaching_fixture_requires_exact_approved_versions(self):
        import copy
        packet=reference('581f7754')
        basis=fixture_basis('581f7754',packet)
        self.assertEqual(basis['fixture'],'teaching_fixture')
        differences=[]
        for split in ('train','test'):
            for i,(a,b_) in enumerate(zip(packet['canonical'][split],packet['teaching_fixture'][split])):
                for field in ('input','output'):
                    for y,(ra,rb) in enumerate(zip(a[field],b_[field])):
                        for x,(va,vb) in enumerate(zip(ra,rb)):
                            if va!=vb:differences.append(dict(split=split,pair=i,field=field,row=y,col=x,canonical=va,teaching=vb))
        self.assertEqual(differences,basis['changed_cells'])
        scores=check_reference('581f7754')
        self.assertEqual(scores['canonical']['correct'],4)
        self.assertEqual(scores['teaching_fixture']['correct'],5)
        changed=copy.deepcopy(packet);changed['teaching_fixture']['train'][1]['output'][3][8]=2
        with self.assertRaisesRegex(ValueError,'hashes changed'):
            fixture_basis('581f7754',changed)
        self.assertEqual(fixture_basis('unapproved',changed)['fixture'],'canonical')

    def test_panel_style_clean_line_recovery_and_periodic_strip_controls(self):
        panels=importlib.import_module('tasks.task_4e45f183')
        with patch.object(panels,'_motif_patterns',return_value=None):
            with self.assertRaisesRegex(ValueError,'motif patterns'):
                panels.generate(panel_size=4,style='motif')
        with self.assertRaisesRegex(ValueError,'dot and hash'):
            panels._parse(['#...','....','....','...x'],4)
        plaid=importlib.import_module('tasks.task_4ff4c9da')
        for seed in range(30060,30065):
            random.seed(seed)
            p=plaid.generate(size=30,num_templates=2,palette=[0,4,7],recovery='clean')
            mask={(y,x) for y,row in enumerate(p['input']) for x,c in enumerate(row) if c==8}
            self.assertTrue(any((x,y) in mask for y,x in mask))
            self.assertEqual(len(plaid._components(p['input'],8)),2)
            self.assertEqual(p['output'],grid(call(solver('4ff4c9da'),p['input'])))
        template=importlib.import_module('tasks.task_50f325b5')
        random.seed(30000)
        p=template.generate(width=30,height=30,num_copies=3,num_distractors=2)
        cells={(y,x) for y,row in enumerate(p['input']) for x,c in enumerate(row) if c==8}
        matches=template._all_placements(p['input'],template._variants(cells))
        self.assertEqual(len(matches),3)
        union=set().union(*matches)
        self.assertTrue(all(z==(8 if (y,x) in union else p['input'][y][x])
                            for y,row in enumerate(p['output']) for x,z in enumerate(row)))
        strips=importlib.import_module('tasks.task_53fb4810')
        bad=strips._obj(3,3,3,3,'right',True,[[2]])
        with self.assertRaisesRegex(ValueError,'reach the border'):
            strips.generate(height=12,width=12,objects=[bad])
        bad=strips._obj(3,3,3,4,'up',False,[[2]])
        with self.assertRaisesRegex(ValueError,'outermost blob edge'):
            strips.generate(height=12,width=12,objects=[bad])
        random.seed(31000)
        a,z=strips._band_scene(24,30,4)
        self.assertEqual(z,grid(call(solver('53fb4810'),a)))

    def test_empty_votes_corner_template_and_connector_partial_matches(self):
        votes=importlib.import_module('tasks.task_4b6b68e5')
        random.seed(30000)
        p=votes.generate(width=30,height=30,num_shapes=1,num_closed=1,
                         num_empty_closed=1,palette=[2,5])
        # No votes: the closed interior must not acquire any new colour.
        self.assertTrue(all(z==0 or z==a for ar,zr in zip(p['input'],p['output']) for a,z in zip(ar,zr)))
        self.assertNotEqual(p['input'],p['output'])  # Exterior dots are erased.
        self.assertEqual(p['output'],grid(call(solver('4b6b68e5'),p['input'])))
        with self.assertRaisesRegex(ValueError,'empty closed count'):
            votes.generate(num_shapes=2,num_closed=1,num_empty_closed=2)
        corners=importlib.import_module('tasks.task_4c416de3')
        with self.assertRaisesRegex(ValueError,'decorated template'):
            corners.generate(width=20,height=20,background=8,frames=[(3,3,14,14)],
                             template=[(0,0),(1,1),(1,0)],marks=[(3,3,2)],decorated=[])
        random.seed(30001)
        p=corners.generate(width=13,height=13,background=8,num_frames=1,depth=3)
        self.assertEqual(p['output'],grid(call(solver('4c416de3'),p['input'])))
        assembly=importlib.import_module('tasks.task_4e34c42c')
        ring=[[1,1,1],[1,2,1],[1,1,1]]
        # Inferior partial overlaps of the ring's repeated border are valid
        # distractions; the full intended overlap must win.
        self.assertTrue(assembly._unique([ring,ring],[(0,0,3,3),(0,0,3,3)],0,3,3))
        repeated=[row+([1,1] if y==1 else [0,0])+row for y,row in enumerate(ring)]
        self.assertFalse(assembly._unique([repeated,ring],[(0,0,3,8),(0,0,3,3)],0,3,8))
        for layout,seed in [('tree',30000),('strip',30060)]:
            random.seed(seed)
            p=assembly.generate(width=30,height=30,bg=8,num_motifs=5,num_branches=2,
                                duplicate=True,transpose=False,layout=layout)
            self.assertGreater(len(p['output']),3)
            self.assertGreater(len(p['output'][0]),3)
            self.assertEqual(p['output'],grid(call(solver('4e34c42c'),p['input'])))

    def test_legend_bounds_pointer_precedence_marker_palette_and_connected_shape(self):
        legend=importlib.import_module('tasks.task_3e6067c3')
        random.seed(30000)
        p=legend.generate(width=30,height=30,bg=8,frame=1,size=6,core=2)
        self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
        self.assertEqual(p['input'][-2],p['output'][-2])
        self.assertTrue(all(x==y or x==8 for a,z in zip(p['input'],p['output']) for x,y in zip(a,z)))
        with self.assertRaisesRegex(ValueError,'cannot fit'):
            legend.generate(width=8,height=8,size=6,core=2)
        with self.assertRaisesRegex(ValueError,'require explicit'):
            legend.generate(rows=[1,8])
        pointer=importlib.import_module('tasks.task_409aa875')
        shapes=[(8,3,0,1),(3,8,1,0)]
        p=pointer.generate(shapes=shapes,width=16,height=16,color=6)
        self.assertEqual(p['output'][8][8],1)
        p=pointer.generate(shapes=shapes+[(8,8,-1,0)],width=16,height=16,color=6)
        # A shared target on a shape triggers whole-shape recolouring, not 1.
        self.assertEqual([p['output'][r][c] for r,c in [(8,8),(9,7),(9,9)]],[9,9,9])
        p=pointer.generate(shapes=[(1,5,-1,0)],width=16,height=16,color=6)
        self.assertEqual(p['input'],p['output'])
        jigsaw=importlib.import_module('tasks.task_446ef5d2')
        for seed in range(30000,30010):
            random.seed(seed)
            p=jigsaw.generate(height=30,width=30,marker=4,corner='br')
            counts=Counter(c for row in p['input'] for c in row)
            self.assertEqual(counts[4],3)
            self.assertNotEqual(counts.most_common(1)[0][0],4)
            self.assertNotIn(4,{c for row in p['output'] for c in row})
            self.assertEqual(p['output'],grid(call(solver('446ef5d2'),p['input'])))
        corners=importlib.import_module('tasks.task_4a21e3da')
        with self.assertRaisesRegex(ValueError,'4-connected'):
            corners.generate(height=12,width=12,shape=['#..','...','..#'],
                             top=3,left=3,vmarker=('top',3))
        with self.assertRaisesRegex(ValueError,'reach the crossing'):
            corners.generate(height=12,width=12,shape=['##...','.####','....#'],
                             top=3,left=3,vmarker=('top',3),hmarker=('left',5))

    def test_template_controls_dead_end_rooms_nearest_key_and_arch_cups(self):
        template=importlib.import_module('tasks.task_3a25b0d8')
        with self.assertRaisesRegex(ValueError,'Both sprites'):
            template.generate(template_sprite=['1'])
        with self.assertRaisesRegex(ValueError,'supplied together'):
            template.generate(t_heights=[2,2])
        with self.assertRaisesRegex(ValueError,'both positions'):
            template.generate(tpos=(0,0),width=30,height=30)
        random.seed(30000)
        p=template.generate(width=30,height=30,counts=[2,2,1],colors=[1,2,None,3,1],bg=7,line=8,symmetric=False)
        self.assertEqual(set(v for row in p['output'] for v in row),{1,2,3,7,8})
        self.assertEqual(p['output'],grid(call(solver('3a25b0d8'),p['input'])))
        rooms=importlib.import_module('tasks.task_3ad05f52')
        random.seed(30000)
        h,w,col,structures,path,doors,extra=rooms._sample_scene(4,30,24,'double',True)
        self.assertTrue(extra)
        p=rooms.generate(height=h,width=w,colour=col,structures=structures,path=path,doors=doors,extra_doors=extra)
        self.assertTrue(all(p['input'][r][c]==p['output'][r][c]==0 for r,c in extra))
        self.assertEqual(p['output'],grid(call(solver('3ad05f52'),p['input'])))
        with patch.object(rooms,'_sample_double',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'requested room path'):
                rooms.generate(layout_mode='double')
        key=importlib.import_module('tasks.task_3d588dc9')
        p=key.generate(height=20,width=25,triangles=[(8,0,3,3,'L',5)],keys=[(8,6,3,3,'U'),(8,17,3,3,'D')])
        self.assertEqual(p['output'][6][7],7)
        self.assertEqual([row[6] for row in p['output'][8:11]],[6,6,6])
        self.assertEqual([row[17:20] for row in p['output'][8:13]],[row[17:20] for row in p['input'][8:13]])
        cups=importlib.import_module('tasks.task_3dc255db')
        random.seed(30001)
        h,w,containers,distractors=cups._sample_scene(24,30,3,'arch',5)
        self.assertEqual(len(containers),3)
        p=cups.generate(height=h,width=w,containers=containers,distractors=distractors)
        for c in containers:
            self.assertEqual(len(c['markers']),5)
            self.assertTrue(all(p['output'][r][col]==0 for r,col in c['markers']))
            self.assertTrue(all(p['output'][r][col]==c['colour'] for r,col in c['cells']))
        self.assertEqual(p['output'],grid(call(solver('3dc255db'),p['input'])))
        with self.assertRaisesRegex(ValueError,'require containers'):
            cups.generate(distractors=[])

    def test_stream_clusters_rectangular_panels_and_diagonal_contact(self):
        stream=importlib.import_module('tasks.task_36a08778')
        random.seed(30001)
        p=stream.generate(width=30,height=24,sources=[(2,2),(10,2),(18,2),(27,2)],obstacle_mode='clustered')
        self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
        self.assertEqual(p['output'],grid(call(solver('36a08778'),p['input'])))
        self.assertEqual([[v==2 for v in row] for row in p['input']],[[v==2 for v in row] for row in p['output']])
        with patch.object(stream,'_random_scene',return_value=(10,10,[(4,1)],[])):
            with self.assertRaisesRegex(RuntimeError,'two wrap events'):
                stream.generate(width=10,height=10)
        with self.assertRaisesRegex(ValueError,'overwrite sources'):
            stream.generate(width=10,height=10,sources=[(4,2)],segments=[(1,3,1,6)])
        panels=importlib.import_module('tasks.task_38007db0')
        random.seed(30001)
        p=panels.generate(motif_height=11,motif_width=6,rows=2,cols=3,frame=9,background=7,ink=3,odd_cols=[2,0])
        self.assertEqual((len(p['input']),len(p['input'][0])),(29,28))
        self.assertEqual((len(p['output']),len(p['output'][0])),(29,10))
        self.assertEqual([row[1:-1] for row in p['output'][1:14]],[row[19:27] for row in p['input'][1:14]])
        self.assertEqual([row[1:-1] for row in p['output'][15:28]],[row[1:9] for row in p['input'][15:28]])
        with self.assertRaisesRegex(ValueError,'distinct'):
            panels.generate(frame=3,ink=3)
        diagonal=importlib.import_module('tasks.task_396d80d7')
        pixels=[(2,2,1),(2,4,1),(4,2,1),(4,4,1),(3,3,9)]
        p=diagonal.generate(width=7,height=7,pixels=pixels,inner_color=9)
        self.assertEqual(p['output'][1][1],9)  # diagonal contact only
        self.assertEqual(p['output'][1][2],7)  # orthogonal contact blocks painting
        self.assertEqual(p['output'][3][3],9)  # original inner cell unchanged
        with self.assertRaisesRegex(ValueError,'smallest bounding box'):
            diagonal.generate(width=7,height=7,pixels=pixels,inner_color=1)
        polygons=importlib.import_module('tasks.task_35ab12c3')
        random.seed(30000)
        p=polygons.generate(width=30,height=24,num_shapes=4,num_companions=2)
        counts=Counter(v for row in p['input'] for v in row if v)
        self.assertEqual(sum(n>=2 for n in counts.values()),4)
        self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
        with self.assertRaisesRegex(ValueError,'require explicit shapes'):
            polygons.generate(companions=[])

    def test_sliding_block_geometry_and_requested_shape_sequence_sizes(self):
        block=importlib.import_module('tasks.task_332f06d7')
        with self.assertRaisesRegex(ValueError,'size >= 2'):
            block.generate(size=1,reachable=False)
        with self.assertRaisesRegex(ValueError,'positions require layout'):
            block.generate(start=(1,1))
        with self.assertRaisesRegex(ValueError,'fit fully'):
            block.generate(size=2,layout=['..####','..####','####..','####..'],start=(0,1),goal=(2,4))
        for reachable in (True,False):
            random.seed(30001)
            p=block.generate(size=3,width=30,height=24,topology='rooms',reachable=reachable)
            self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
            self.assertEqual(p['output'],grid(call(solver('332f06d7'),p['input'])))
            self.assertEqual(sum(v==0 for row in p['output'] for v in row),9)
        swap=importlib.import_module('tasks.task_3391f8c0')
        random.seed(30001)
        p=swap.generate(width=30,height=24,shape_height=5,shape_width=5,num_copies=8,packing='tight',rep_color=3,odd_color=8)
        before=Counter(v for row in p['input'] for v in row);after=Counter(v for row in p['output'] for v in row)
        self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
        self.assertEqual(after[8],8*before[8]);self.assertEqual(8*after[3],before[3])
        with self.assertRaisesRegex(ValueError,'supplied together'):
            swap.generate(odd_pos=(1,1))
        sequence=importlib.import_module('tasks.task_351d6448')
        for family in ('bar','slide','stair'):
            random.seed(30000)
            p=sequence.generate(family=family,height=9,width=30,num_panels=3,step=2)
            self.assertEqual((len(p['input']),len(p['input'][0])),(29,30))
            self.assertEqual(len(p['output']),9)
            self.assertEqual(p['output'],grid(call(solver('351d6448'),p['input'])))
        with self.assertRaisesRegex(ValueError,'within 30'):
            sequence.generate(height=9,num_panels=4)
        with self.assertRaisesRegex(ValueError,'matching explicit family'):
            sequence.generate(family='bar',tile=[[1,0]]*3)
        with self.assertRaisesRegex(ValueError,'Unknown sequence'):
            sequence.generate(family='typo')

    def test_ray_components_bar_extents_and_open_shape_labels(self):
        ray=importlib.import_module('tasks.task_2f767503')
        # Ray hits one cell; the whole blob disappears, but its diagonal neighbor survives.
        pattern=['.'*10 for _ in range(10)]
        pattern[4]='....44....';pattern[3]='......4...'
        p=ray.generate(center=(8,4),vertical=False,side=1,pattern=pattern)
        self.assertEqual(p['output'][4][4:6],[7,7])
        self.assertEqual(p['output'][3][6],4)
        bars=importlib.import_module('tasks.task_31f7f899')
        kwargs=dict(width=12,height=11,line_row=5,bars=[(1,1,2,1,9),(4,2,3,4,6),(8,1,4,3,7)])
        p=bars.generate(**kwargs,vertical=False)
        self.assertEqual(p['input'][5],p['output'][5])
        self.assertEqual([sum(row[c]==colour for row in p['output']) for c,colour in [(1,2),(4,3),(8,4)]],[3,5,9])
        self.assertEqual(bars.generate(**kwargs,vertical=True)['output'],bars._transpose(p['output']))
        with self.assertRaisesRegex(ValueError,'Equal-length'):
            bars.generate(width=12,height=11,line_row=5,bars=[(1,1,2,2,6),(4,1,3,3,7)])
        shapes=importlib.import_module('tasks.task_320afe60')
        closed=['111','1.1','111'];opened=['1.1','1.1','111']
        p=shapes.generate(width=12,height=10,objects=[(1,4,closed,'left'),(6,4,opened,'right')])
        self.assertEqual(p['output'][1][:3],[2,2,2])
        self.assertEqual(p['output'][6][-3:],[3,4,3])
        self.assertEqual(sum(v==1 for row in p['input'] for v in row),sum(v in (2,3) for row in p['output'] for v in row))
        with self.assertRaisesRegex(ValueError,'side must match'):
            shapes.generate(width=12,height=10,objects=[(1,4,closed,'right')])

    def test_wall_outputs_count_actual_background_regions(self):
        module=importlib.import_module('tasks.task_e872b94a')
        for seed in range(50000,50100):
            random.seed(seed)
            pair=call(module.generate,seconds=3)
            remaining={(r,c) for r,row in enumerate(pair['input']) for c,v in enumerate(row) if v==0}
            regions=0
            while remaining:
                regions+=1;stack=[remaining.pop()]
                while stack:
                    r,c=stack.pop()
                    for neighbor in [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]:
                        if neighbor in remaining:
                            remaining.remove(neighbor);stack.append(neighbor)
            self.assertEqual(pair['output'],[[0] for _ in range(regions)],seed)
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
    def test_new_generators_honor_overrides_and_hole_connectivity(self):
        figures=importlib.import_module('tasks.task_c7f57c3e')
        bars=importlib.import_module('tasks.task_b0039139')
        holes=importlib.import_module('tasks.task_8698868d')
        for seed in range(10):
            random.seed(seed)
            pair=call(lambda:figures.generate(width=28,height=24,background=8,shape='plus'),seconds=3)
            self.assertEqual((len(pair['input']),len(pair['input'][0])),(24,28))
            self.assertEqual(Counter(v for row in pair['input'] for v in row).most_common(1)[0][0],8)
            pair=call(lambda:bars.generate(color_a=7),seconds=3)
            self.assertIn(7,{v for row in pair['output'] for v in row})
            pair=call(lambda:bars.generate(color_b=9),seconds=3)
            self.assertIn(9,{v for row in pair['output'] for v in row})
        with self.assertRaisesRegex(ValueError,'complete latent'):
            figures.generate(figures=[(1,1,1,True)])
        with self.assertRaisesRegex(ValueError,'explicit motif'):
            bars.generate(len2=5)
        with self.assertRaisesRegex(ValueError,'explicit shapes'):
            holes.generate(origin=(0,0))
        diagonal=False
        for seed in range(100):
            random.seed(seed)
            cells=holes._make_panel_holes(7,5)
            self.assertEqual(len(cells),5)
            self.assertTrue(all(abs(r-y)+abs(c-x)>1 for i,(r,c) in enumerate(cells) for y,x in cells[i+1:]))
            diagonal |= any(abs(r-y)==abs(c-x)==1 for i,(r,c) in enumerate(cells) for y,x in cells[i+1:])
        self.assertTrue(diagonal,'native examples must include diagonally touching holes')

    def test_extended_canvas_sizes_and_analogy_identifiability(self):
        lines=importlib.import_module('tasks.task_e376de54')
        glyphs=importlib.import_module('tasks.task_136b0064')
        beams=importlib.import_module('tasks.task_e87109e9')
        templates=importlib.import_module('tasks.task_edb79dae')
        analogy=importlib.import_module('tasks.task_4c7dc4dd')
        for size in (10,16,30):
            for seed in range(5):
                random.seed(seed)
                p=call(lambda:lines.generate(size=size,background=9),seconds=3)
                self.assertEqual((len(p['input']),len(p['input'][0])),(size,size))
                self.assertEqual(p['output'],grid(call(solver('e376de54'),p['input'])))
        for width in (7,14,22):
            for rows in (2,7):
                random.seed(width+rows)
                p=glyphs.generate(canvas_width=width,rows=rows,start=width-1)
                self.assertEqual((len(p['input']),len(p['input'][0])),(4*rows-1,width+8))
                self.assertEqual(len(p['output'][0]),width)
                self.assertEqual(p['output'],grid(call(solver('136b0064'),p['input'])))
        for height in (14,24):
            random.seed(height)
            p=call(lambda:beams.generate(height=height,bg=9),seconds=3)
            self.assertEqual(len(p['input']),height+6)
            self.assertEqual(len(p['output']),height)
        random.seed(0)
        p=call(lambda:templates.generate(width=28,height=30,k=3,bg=8),seconds=3)
        self.assertEqual((len(p['input']),len(p['input'][0])),(30,28))
        # Both mirror and gap-filling preserve this example; it cannot identify a rule.
        same=[[1]*4 for _ in range(4)]
        self.assertIsNone(analogy._example_rule(same,same,2))
        with self.assertRaisesRegex(ValueError,'cannot fit'):
            analogy.generate(width=10,height=10)

    def test_object_batch_boundaries_and_pattern_precedence(self):
        for tid,kwargs in [
            ('14754a24',dict(width=30,height=24)),
            ('17829a00',dict(width=30,height=24)),
            ('18419cfa',dict(width=18,height=24)),
            ('1acc24af',dict(width=30,height=24)),
            ('1ae2feb7',dict(width=30,height=24,pattern_side='right')),
            ('1b59e163',dict(width=30,height=24))]:
            module=importlib.import_module('tasks.task_'+tid)
            for seed in range(5):
                random.seed(seed)
                p=call(lambda:module.generate(**kwargs),seconds=3)
                self.assertEqual((len(p['input']),len(p['input'][0])),(kwargs['height'],kwargs['width']),tid)
                self.assertEqual(p['output'],grid(call(solver(tid),p['input'])),tid)
                if tid=='1acc24af':
                    self.assertEqual({v for row in p['output'] for v in row},{0,1,2,5})
        pattern=importlib.import_module('tasks.task_1ae2feb7')
        p=pattern.generate(15,5,5,4,5,'left',[(2,0,[(2,2),(3,3)])])
        self.assertEqual(p['output'][2][6:],[2,0,2,3,2,0,2,0,2])
        frames=importlib.import_module('tasks.task_18419cfa')
        with patch.object(frames,'_place',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'requested canvas'):
                frames.generate(width=18,height=24)
        stamp=importlib.import_module('tasks.task_1b59e163')
        with self.assertRaisesRegex(ValueError,'background 4'):
            stamp.generate(background=1)

    def test_symmetry_recovery_and_region_construction_constraints(self):
        symmetry=importlib.import_module('tasks.task_0934a4d8')
        for size in range(4,9):
            for seed in range(5):
                random.seed(seed)
                p=symmetry.generate(block_size=size,layout='interior')
                self.assertEqual((len(p['input']),len(p['input'][0])),(4*size-2,4*size-2))
                self.assertEqual(p['output'],grid(call(solver('0934a4d8'),p['input'])))
        with self.assertRaisesRegex(ValueError,'edge layout'):
            symmetry.generate(block_size=4,layout='edge')
        with self.assertRaisesRegex(ValueError,'mask colour'):
            symmetry.generate(palette=[1,2,8])
        for tid in ['09c534e7','13e47133','184a9768']:
            module=importlib.import_module('tasks.task_'+tid)
            for seed in range(5):
                random.seed(seed)
                p=call(lambda:module.generate(width=24,height=30),seconds=3)
                self.assertEqual((len(p['input']),len(p['input'][0])),(30,24))
                self.assertEqual(p['output'],grid(call(solver(tid),p['input'])),tid)
        blocks=importlib.import_module('tasks.task_09c534e7')
        with patch.object(blocks,'_random_structures',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'requested structures'):
                blocks.generate(width=24,height=30,num_structures=3)
        with self.assertRaisesRegex(ValueError,'colors length'):
            blocks.generate(num_structures=3,colors=[2,3])
        rings=importlib.import_module('tasks.task_13e47133')
        p=rings.generate(height=12,width=14,background=0,divider=8,
                         segments=[(0,6,11,6)],chains=[(0,0,1,1,[0,2,3])])
        self.assertEqual([p['output'][i][i] for i in range(3)],[0,2,3])
        self.assertTrue(all(row[6]==8 and row[7:]==[0]*7 for row in p['output']))
        with self.assertRaisesRegex(ValueError,'must differ'):
            rings.generate(background=2,divider=2)
        jigsaw=importlib.import_module('tasks.task_184a9768')
        # Identical shapes of different colours can swap holes: reject that ambiguity.
        holes={(0,0),(0,3)}
        self.assertTrue(jigsaw._ambiguous(holes,[(2,1,1),(3,1,1)]))
        self.assertFalse(jigsaw._ambiguous(holes,[(2,1,1),(2,1,1)]))

    def test_ray_bounces_legend_positions_and_piece_conservation(self):
        rays=importlib.import_module('tasks.task_142ca369')
        p=rays.generate(height=18,width=18,emitters=[(7,7,-1,-1,2)],
                        bars=[(4,4,'h',3,4),(8,0,'v',3,6),(14,8,'v',3,5)])
        for r,c,colour in [(6,6,2),(5,5,4),(6,4,4),(9,1,6),
                            (10,2,6),(15,7,5),(16,6,5),(17,5,5)]:
            self.assertEqual(p['output'][r][c],colour,(r,c))
        for seed in range(5):
            random.seed(seed)
            p=rays.generate(width=30,height=24,mode='parallel')
            self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
            self.assertEqual(p['output'],grid(call(solver('142ca369'),p['input'])))
        legend=importlib.import_module('tasks.task_1da012fc')
        self.assertEqual(legend._axis(5,3,allow_border=True),[0,2,4])
        join=importlib.import_module('tasks.task_20270e3b')
        damaged=importlib.import_module('tasks.task_2037f2c7')
        for seed in range(5):
            random.seed(seed)
            p=legend.generate(width=30,height=24,num_shapes=5,shape_color=8)
            self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
            self.assertEqual(p['output'],grid(call(solver('1da012fc'),p['input'])))
            p=join.generate(width=30,height=24,fill=0,transpose=True)
            self.assertEqual(sum(row.count(4) for row in p['input']),sum(row.count(4) for row in p['output']))
            self.assertFalse(any(7 in row for row in p['output']))
            self.assertEqual(p['output'],grid(call(solver('20270e3b'),p['input'])))
            p=call(lambda:damaged.generate(width=30,height=30,fig_width=8,fig_height=20),seconds=3)
            self.assertEqual(len(p['output'][0]),8)
            self.assertEqual(p['output'],grid(call(solver('2037f2c7'),p['input'])))
        with self.assertRaisesRegex(ValueError,'both explicit pieces'):
            join.generate(piece_a=(0,0,['#m']))
        with self.assertRaisesRegex(ValueError,'both copy positions'):
            damaged.generate(intact_pos=(0,0))

    def test_irregular_regions_stacking_and_overlap_precedence(self):
        regions=importlib.import_module('tasks.task_21897d95')
        canvas=[[2]*6+[3]*6 for _ in range(8)]
        p=regions.generate(canvas=canvas,markers=[(2,4,'R',1),(5,7,'L',1)])
        self.assertEqual(p['output'],[[3]*6+[2]*6 for _ in range(8)])
        for seed in [0,1,2,20085,20388]:
            random.seed(seed)
            canvas,markers,lshape=regions._random_scene(24,30,6,4,False,True)
            _,groups=regions._components(canvas)
            self.assertEqual(len(groups),6)
            self.assertEqual(len(markers),4)
            self.assertTrue(any(len(c)!=(max(y for y,x in c)-min(y for y,x in c)+1)*
                                (max(x for y,x in c)-min(x for y,x in c)+1) for c in groups))
            p=regions.generate(canvas=canvas,markers=markers,lshape=lshape)
            self.assertEqual(p['output'],grid(call(solver('21897d95'),p['input'])))
        stack=importlib.import_module('tasks.task_25c199f5')
        for size,count in [(4,3),(5,3),(9,3),(6,4),(14,2)]:
            random.seed(size+count)
            p=stack.generate(size=size,num_panels=count)
            self.assertEqual((len(p['input']),len(p['input'][0])),(size,count*size+count-1))
            self.assertEqual((len(p['output']),len(p['output'][0])),(size,size))
            self.assertEqual(p['output'],grid(call(solver('25c199f5'),p['input'])))
        with self.assertRaisesRegex(ValueError,'30 columns'):
            stack.generate(size=9,num_panels=4)
        stamps=importlib.import_module('tasks.task_247ef758')
        # Canonical overlap at (5,9) must keep the higher legend's colour 4.
        p=stamps.validate()['train'][0]
        self.assertEqual(p['output'][5][9],4)
        random.seed(0)
        p=stamps.generate(height=30,legend_width=5,frame_width=24)
        self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
        self.assertEqual(p['output'],grid(call(solver('247ef758'),p['input'])))
        ladder=importlib.import_module('tasks.task_221dfab4')
        for side in ['top','bottom','left','right']:
            random.seed(0)
            p=ladder.generate(width=30,height=24,color=2,side=side)
            self.assertEqual(p['output'],grid(call(solver('221dfab4'),p['input'])))

    def test_registered_standalone_sources_and_fixtures(self):
        # Validate the registered files, not only the older research registry.
        for tid in NEW_TASK_IDS:
            module=importlib.import_module('tasks.task_'+tid)
            source=Path(module.__file__).read_bytes()
            report=json.loads((BASE/'reports'/'standalone'/f'{tid}.json').read_text())
            self.assertEqual(hashlib.sha256(source).hexdigest(),report['stress_test']['sha256'],tid)
            self.assertTrue(report['stress_test']['ready'],tid)
            actual=call(module.validate,seconds=30)
            expected=reference(tid)[fixture_basis(tid)['fixture']]
            key=lambda p:json.dumps(p,sort_keys=True)
            for split in ['train','test']:
                self.assertEqual(sorted(map(key,actual[split])),sorted(map(key,expected[split])),(tid,split))
            from .runtime import verification_solver
            solve=verification_solver(tid)
            for seed in range(10000,10020):
                random.seed(seed)
                from .contextual import CONTEXTUAL_TASK_IDS, verify_shared_picture_episode
                if tid in CONTEXTUAL_TASK_IDS:
                    episode=call(module.generate_episode,seconds=3)
                    self.assertTrue(call(verify_shared_picture_episode,episode,seconds=3),(tid,seed))
                else:
                    pair=call(module.generate,seconds=3)
                    self.assertEqual(grid(pair['output']),grid(call(solve,grid(pair['input']),seconds=3)),(tid,seed))
    def test_box_motion_and_lane_reading_preserve_mechanisms(self):
        boxes=importlib.import_module('tasks.task_271d71e2')
        lanes=importlib.import_module('tasks.task_291dc1e1')
        for direction in ('up','down','left','right'):
            for already in (0,5,6):
                p=boxes.generate(30,30,[(12,12,2,3,direction,3,already)])
                before=Counter(v for row in p['input'] for v in row)
                after=Counter(v for row in p['output'] for v in row)
                travel=min(6-already,4)
                self.assertEqual(before[5]-after[5],travel)
                self.assertEqual(after[7]-before[7],travel)
                self.assertEqual(before[0],after[0])
                self.assertEqual(p['output'],grid(call(solver('271d71e2'),p['input'])))
        for seed in range(5):
            random.seed(seed)
            p=call(lambda:boxes.generate(width=30,height=24,num_boxes=4),seconds=3)
            self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
            self.assertEqual(p['output'],grid(call(solver('271d71e2'),p['input'])))
        latent=[[[[3,4],[5,6]],[[9,9,9,9],[9,9,1,2]]],
                [[[7,7],[7,7]],[[6,6,6,6],[6,6,6,6]]],
                [[[4,3],[6,5]],[[3,3,3,3],[3,3,3,3]]]]
        expected=None
        for vertical in (False,True):
            for one_top in (False,True):
                for two_left in (False,True):
                    p=lanes.generate(vertical,one_top,two_left,latent,width=20,num_lanes=3)
                    if expected is None:expected=p['output']
                    self.assertEqual(p['output'],expected)
                    self.assertEqual(p['output'],grid(call(solver('291dc1e1'),p['input'])))
        for n in (2,3,4,5):
            random.seed(n)
            p=call(lambda:lanes.generate(vertical=False,width=30,num_lanes=n),seconds=3)
            self.assertEqual((len(p['input']),len(p['input'][0])),(3*n+2,30))
            self.assertLessEqual(len(p['output']),30)
            self.assertEqual(p['output'],grid(call(solver('291dc1e1'),p['input'])))
        with self.assertRaisesRegex(ValueError,'dimensions'):
            boxes.generate(width=9)
        with self.assertRaisesRegex(ValueError,'outside grid'):
            boxes.generate(10,10,[(8,8,2,2,'right',1,0)])
        with self.assertRaisesRegex(ValueError,'do not fit'):
            lanes.generate(lanes=[[lanes._solid(3,8),lanes._solid(4,8)]]*2,width=11)

    def test_water_conservation_and_jigsaw_translation(self):
        water=importlib.import_module('tasks.task_28a6681f')
        jigsaw=importlib.import_module('tasks.task_16b78196')
        # Both nearest drops are one cell away: local tie-break must go left.
        terrain=[[0]*5 for _ in range(4)];terrain[2][2]=5
        p=water.generate(terrain=terrain,water=[(1,2)])
        self.assertEqual(p['output'][3][1],1)
        self.assertEqual(sum(v==1 for row in p['output'] for v in row),1)
        for ramp in (False,True):
            for style in ('blob','columns'):
                random.seed(30000+int(ramp))
                p=call(lambda:water.generate(width=30,height=24,ramp=ramp,water_style=style,water_count=40),seconds=3)
                self.assertEqual((len(p['input']),len(p['input'][0])),(24,30))
                for field in ('input','output'):
                    self.assertEqual(sum(v==1 for row in p[field] for v in row),40)
                erase=lambda g:[[0 if v==1 else v for v in row] for row in g]
                self.assertEqual(erase(p['input']),erase(p['output']))
                self.assertEqual(p['output'],grid(call(solver('28a6681f'),p['input'])))
        for vertical in (False,True):
            random.seed(30001)
            p=call(lambda:jigsaw.generate(width=24,height=30,wall_color=8,vertical=vertical),seconds=3)
            self.assertEqual((len(p['input']),len(p['input'][0])),(24,30) if vertical else (30,24))
            counts=lambda g:Counter(v for row in g for v in row)
            self.assertEqual(counts(p['input']),counts(p['output']))
            self.assertEqual([[v==8 for v in row] for row in p['input']],[[v==8 for v in row] for row in p['output']])
            self.assertEqual(p['output'],grid(call(solver('16b78196'),p['input'])))
            if not vertical:native=p
            else:
                for field in ('input','output'):
                    self.assertEqual(p[field],[list(row) for row in zip(*native[field])])
        with self.assertRaisesRegex(ValueError,'explicit terrain'):
            water.generate(water=[(0,0)])
        with self.assertRaisesRegex(ValueError,'Duplicate water'):
            water.generate(terrain=terrain,water=[(0,0),(0,0)])
        with self.assertRaisesRegex(ValueError,'empty cells'):
            water.generate(terrain=terrain,water=[(2,2)])
        with self.assertRaisesRegex(ValueError,'explicit chains'):
            jigsaw.generate(wall_top=10)
        with self.assertRaisesRegex(ValueError,'position required'):
            jigsaw.generate(width=30,height=30,wall_color=8,wall_top=14,wall_thickness=5,
                            top_notches={5:1},chains=[('top',4,[[2,2,2]],[2])],positions=[])

    def test_sequence_windows_ladder_markers_and_hub_docking(self):
        sequence=importlib.import_module('tasks.task_20a9e565')
        ladder=importlib.import_module('tasks.task_2b83f449')
        hub=importlib.import_module('tasks.task_2c181942')
        for family in ('comb','ladder','mirror','stair'):
            random.seed(30000)
            p=call(lambda:sequence.generate(family=family,width=30,height=30),seconds=3)
            self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
            marks=[(r,c) for r,row in enumerate(p['input']) for c,v in enumerate(row) if v==5]
            self.assertEqual((len(p['output']),len(p['output'][0])),
                             (max(r for r,c in marks)-min(r for r,c in marks)+1,
                              max(c for r,c in marks)-min(c for r,c in marks)+1))
            self.assertEqual(p['output'],grid(call(solver('20a9e565'),p['input'])))
        for seed in range(5):
            random.seed(seed)
            p=ladder.generate(width=30,tracks=15)
            self.assertEqual(sum(v==3 for row in p['input'] for v in row),28)
            self.assertEqual(sum(v==3 for row in p['output'] for v in row),28)
            self.assertEqual(p['output'],grid(call(solver('2b83f449'),p['input'])))
        # One asymmetric matching piece per side, plus an erased distractor.
        mask=['1111','1.11','.11.']
        for i,side in enumerate(hub.SIDES):
            p=hub.generate(width=30,height=30,hub_row=14,hub_col=14,colors=[1,2,3,4],
                           shapes=[(i+1,mask,1,1,1),(9,['11','11'],0,24,24)])
            self.assertNotIn(9,{v for row in p['output'] for v in row})
            self.assertEqual(p['output'],grid(call(solver('2c181942'),p['input'])))
        with self.assertRaisesRegex(ValueError,'explicit gaps'):
            ladder.generate(rungs=[[]]*3,tracks=4)
        with self.assertRaisesRegex(ValueError,'distinct hub colours'):
            hub.generate(colors=[1,1,2,3])
        with self.assertRaisesRegex(ValueError,'explicit shapes'):
            hub.generate(hub_row=10)
        with self.assertRaisesRegex(ValueError,'match family'):
            sequence.generate(family='mirror',params=sequence._FIXTURES['train'][0])

    def test_path_phase_panel_period_and_containment_controls(self):
        paths=importlib.import_module('tasks.task_195c6913')
        panels=importlib.import_module('tasks.task_2ccd9fef')
        trees=importlib.import_module('tasks.task_2d0172a1')
        terrain=[[8]*12 for _ in range(10)]
        cells=[(7,c) for c in range(4)]+[(r,3) for r in (6,5,4,3)]+[(3,c) for c in range(4,12)]
        for r,c in cells:terrain[r][c]=0
        p=paths.generate(terrain=terrain,pattern=[1,1,2],marker_color=9,
                         marker_pos=(8,9),seed_rows=[7],legend_row=0)
        for i,(r,c) in enumerate(cells):self.assertEqual(p['output'][r][c],[1,1,2][i%3])
        self.assertEqual(p['output'][7][4],9)
        self.assertEqual(p['output'][2][3],9)
        self.assertEqual(p['output'][8][9],8)
        for axis in (0,1):
            for q in (1,2):
                n=3 if q==1 else 5
                ph,pw=(30//n,30) if axis==0 else (30,30//n)
                random.seed(30000+axis+q)
                p=call(lambda:panels.generate(axis=axis,num_panels=n,panel_height=ph,panel_width=pw,sequence_period=q),seconds=3)
                self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
                self.assertEqual((len(p['output']),len(p['output'][0])),(ph,pw))
                self.assertEqual(p['output'],grid(call(solver('2ccd9fef'),p['input'])))
        for style in trees._STYLES:
            random.seed(30000)
            p=call(lambda:trees.generate(bg=8,fg=3,style=style,outside=2,width=30,height=30),seconds=3)
            self.assertEqual((len(p['input']),len(p['input'][0])),(30,30))
            _,_,roots=trees._parse(p['input'])
            self.assertEqual(sum(not n['kids'] for n in roots),2)
            self.assertEqual(sum(bool(n['kids']) for n in roots),2 if style=='pair' else 1)
            self.assertEqual(p['output'],grid(call(solver('2d0172a1'),p['input'])))
        with self.assertRaisesRegex(ValueError,'distinct'):
            paths.generate(background=1,path_color=1)
        with self.assertRaisesRegex(ValueError,'explicit terrain'):
            paths.generate(seed_rows=[4])
        with self.assertRaisesRegex(ValueError,'both template and objects'):
            panels.generate(template=[[0]*5 for _ in range(5)])
        with self.assertRaisesRegex(ValueError,'five panels'):
            panels.generate(num_panels=3,sequence_period=2)
        with self.assertRaisesRegex(ValueError,'Unknown containment'):
            trees.generate(style='typo')
        with self.assertRaisesRegex(ValueError,'outside must'):
            trees.generate(outside=3)

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
        with patch.dict(b.POLICY['planned_dataset'],bulk_builder_expansion_pending=True):
            with self.assertRaisesRegex(RuntimeError,'eight-variant'):
                b.require_build_ready(all_ready)
        with self.assertRaisesRegex(RuntimeError,'reviewed standalone'):
            b.require_build_ready(all_ready)
    def test_exhaustive_symmetry_deduplication_includes_answers(self):
        # Symmetric inputs do not imply symmetric outputs.
        pairs=[{'input':[[0]],'output':[[1,2],[3,4]]},
               {'input':[[5]],'output':[[0,6],[7,8]]}]
        variants=exhaustive_variants(pairs)
        self.assertEqual(len(variants),8)
        self.assertEqual({v['d4_transform'] for v in variants},set(range(8)))
        self.assertEqual(variants[1]['pairs'][-1]['output'],[[7,0],[8,6]])
        for v in variants:
            self.assertEqual(v['pairs'],apply_episode(pairs,v['d4_transform'],list(range(10))))
        # Here all eight really are identical; retain one with full provenance.
        symmetric=[{'input':[[0]],'output':[[1]]},
                   {'input':[[2,2],[2,2]],'output':[[3]]}]
        unique=exhaustive_variants(symmetric)
        self.assertEqual(len(unique),1)
        self.assertEqual(unique[0]['equivalent_d4'],list(range(8)))
        # A reflection permuting demonstrations is also the same puzzle.
        swap=[{'input':[[1,2]],'output':[[3,4]]},
              {'input':[[2,1]],'output':[[4,3]]},
              {'input':[[5]],'output':[[6]]}]
        self.assertEqual(len(exhaustive_variants(swap)),2)
    def test_default_augmentation_preserves_native_colours(self):
        rng=random.Random(42);seen=set()
        for _ in range(1000):
            d,p=settings(rng,'example',b.POLICY);seen.add(d)
            self.assertEqual(p,list(range(10)))
        self.assertEqual(seen,set(range(8)))
    def test_original_and_independent_construction(self):
        for tid in GENERATORS:
            self.assertTrue(check_reference(tid)[fixture_basis(tid)['fixture']]['all_exact'],tid)
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
        rs=[{'task_id':'rich','train_canonical':2000,'train_strata':{'15|same_shape':2000}}]
        alloc,stats=b.allocate(rs,'train',2000,{'15|same_shape':1})
        self.assertEqual(sum(alloc['rich'].values()),1000)
        self.assertEqual(stats['allocated'],1000)
    def test_reviewed_constructors_replace_drafts_and_invalidate_old_pools(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'pools').mkdir();(root/'pool_reports').mkdir()
            tid='e872b94a';file=root/'pools'/f'{tid}.parquet'
            file.write_bytes(b'obsolete cached pool')
            (root/'pool_reports'/f'{tid}.json').write_text(json.dumps({'complete':True,'seed':b.SEED}))
            with patch.object(b,'OUT',root),patch.object(b,'POOL_SIZE',8),patch.object(b,'FAMILY_SECONDS',30):
                with patch.object(b,'generate',side_effect=AssertionError('archived draft selected')) as draft:
                    report=b.make_pool(tid)
                    draft.assert_not_called()
                self.assertEqual(report['modes'],{'standalone_constructor':8})
                self.assertEqual(report['pairs'],8)
                self.assertTrue(report['source_signature'])
                module=importlib.import_module('tasks.task_'+tid)
                with patch.object(module,'generate',side_effect=AssertionError('valid pool should be cached')) as constructor:
                    self.assertEqual(b.make_pool(tid),report)
                    constructor.assert_not_called()
                # A tampered source signature forces regeneration even at the same seed.
                stored={**report,'source_signature':'old-source'}
                (root/'pool_reports'/f'{tid}.json').write_text(json.dumps(stored))
                refreshed=b.make_pool(tid)
                self.assertEqual(refreshed['source_signature'],report['source_signature'])
                self.assertEqual(refreshed['modes'],{'standalone_constructor':8})

    def test_sliding_rows_and_two_stage_defects(self):
        slide=importlib.import_module('tasks.task_6e453dd6')
        # Diagonal connections belong to one object; gaps without divider
        # contact must not be painted.
        pair=slide.generate(width=12,height=12,divider=7,shapes=[
            (0,0,['X.X.','.X..','..X.','...X']),
            (6,0,['XXX','X.X','XXX'])])
        self.assertEqual(pair['output'][0][8:], [6]*4)
        self.assertEqual(pair['output'][7][8:], [2]*4)
        self.assertEqual(pair['output'],grid(call(solver('6e453dd6'),pair['input'])))
        with self.assertRaises(ValueError):
            slide.generate(width=12,height=12,divider=7,shapes=[(0,0,['X.X'])])
        with self.assertRaises(ValueError):
            slide.generate(width=8,height=4,divider=5,
                           shapes=[(0,0,['XX','X.','X.','XX'])])
        defects=importlib.import_module('tasks.task_71e489b6')
        pair=defects.generate(width=12,height=12,background=0,
                             rects=[(2,2,9,9,1)],
                             holes=[(4,5),(5,4),(5,6)],specks=[(1,3)])
        self.assertEqual(pair['input'][5][5],1)
        self.assertEqual(pair['output'][5][5],7)
        self.assertEqual(pair['output'][1][3],0)
        self.assertEqual(pair['output'],grid(call(solver('71e489b6'),pair['input'])))
        with self.assertRaises(ValueError):
            defects.generate(width=10,height=10,background=1,rects=[],
                             holes=[(5,5)],specks=[(5,5)])
        for seed in range(4):
            random.seed(30000+seed)
            pair=defects.generate(width=30,height=30,num_holes=8,num_specks=10,
                                  num_attached_specks=3,bridge_holes=True)
            self.assertEqual(pair['output'],grid(call(solver('71e489b6'),pair['input'])))

    def test_docking_priority_and_legend_full_cycles(self):
        dock=importlib.import_module('tasks.task_6e4f6532')
        captured={}
        original=dock._render
        def capture(*args):
            captured['ships']=args[-1]
            return original(*args)
        random.seed(30000)
        with patch.object(dock,'_render',side_effect=capture):
            pair=dock.generate(width=30,height=30,num_ships=6,
                               thickness=1,divider=True)
        multi=0
        for pattern,_,t,target in captured['ships']:
            cells=dock._place(dock._parse(pattern),t,target)
            for (y,x),c in cells.items():
                if c not in (8,9):
                    multi += sum(cells.get((y+dy,x+dx)) in (8,9)
                                 for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)))>1
        self.assertGreater(multi,0)
        self.assertEqual(pair['output'],grid(call(solver('6e4f6532'),pair['input'])))
        with self.assertRaises(ValueError):
            dock.generate(width=15,height=15,thickness=2,divider=True)
        rotate=importlib.import_module('tasks.task_6ffbe589')
        random.seed(41000)
        pair=rotate.generate(size=30,box_size=20,colors=[1,2,3,4],
                             legend_sizes={1:4,2:8},top=0,left=0)
        self.assertEqual(pair['output'],[row[:20] for row in pair['input'][:20]])
        self.assertEqual(pair['output'],grid(call(solver('6ffbe589'),pair['input'])))
        with self.assertRaises(ValueError):
            rotate.generate(size=20,box_size=24)
        with self.assertRaises(ValueError):
            rotate.generate(size=20,figure=['110','010','011'],top=2,left=6,
                            legend=[(1,[(-1,1)])])

    def test_routing_pockets_and_nonadjacent_bands(self):
        route=importlib.import_module('tasks.task_7491f3cf')
        with self.assertRaises(ValueError):
            route.generate(frame=1,background=0,line_color=4,color2=2,color3=3,
                           panel_size=5,line=[(0,2),(1,2),(2,2),(2,1),(2,0)],
                           dot=(0,0),pattern2=['##...','##...','.....','.....','.....'],
                           pattern3=['...##','...##','.....','...##','...##'])
        random.seed(41000)
        pair=route.generate(panel_size=4,pattern2=['####','#..#','#..#','####'])
        self.assertEqual(pair['output'],grid(call(solver('7491f3cf'),pair['input'])))
        pockets=importlib.import_module('tasks.task_753ea09b')
        random.seed(30000)
        with patch.object(pockets,'_replay',side_effect=AssertionError('replay used')):
            pair=pockets.generate(width=30,height=30,outward_stubs=3,
                                  bg=0,wall=9,stick=5)
        self.assertEqual(pair['output'],grid(call(solver('753ea09b'),pair['input'])))
        band=importlib.import_module('tasks.task_7666fa5d')
        pair=band.generate(width=16,height=16,color=4,mechanism='notch',
                           segments=[(12,-12,-6),(12,4,8),(17,-9,11)])
        self.assertEqual(pair['output'][7][7],8)
        self.assertEqual(pair['output'][3][11],2)
        pair=band.generate(width=16,height=16,color=3,mechanism='crossing',
                           segments=[(8,-8,0),(12,8,10),(16,-8,8)])
        self.assertEqual(pair['output'][4][6],2)
        self.assertEqual(pair['output'],grid(call(solver('7666fa5d'),pair['input'])))
        for seed in (20036,20874):
            random.seed(seed)
            pair=band.generate(width=16,height=16,num_segments=3,mechanism='notch')
            self.assertEqual(pair['output'],grid(call(solver('7666fa5d'),pair['input'])))
        with self.assertRaises(ValueError):
            band.generate(segments=[(12,4.9,8)])

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
                    families=defaultdict(list)
                    for r in saved:
                        self.assertEqual(len(r['train']),3);self.assertEqual(len(r['test']),1)
                        self.assertEqual(set(r['test'][0]),{'input'})
                        self.assertEqual(json.loads(r['completion']),{'outputs':r['solutions']})
                        self.assertEqual(json.loads(r['prompt'].split('\n',1)[1]),{'train':r['train'],'test':r['test']})
                        self.assertEqual(len(set(r['canonical_input_hashes'])),4)
                        used[split].update(r['canonical_input_hashes'])
                        families[r['base_episode_id']].append(r)
                    stats=report['splits'][split]
                    self.assertEqual(stats['fresh_episodes'],len(families))
                    self.assertEqual(stats['episodes'],len(saved))
                    self.assertEqual(stats['symmetric_variants_removed'],8*len(families)-len(saved))
                    originals={r['input_hash']:r for r in rows}
                    for group in families.values():
                        covered=[d for row in group for d in row['equivalent_d4']]
                        self.assertEqual(sorted(covered),list(range(8)))
                        for row in group:
                            base=[originals[h] for h in row['base_input_hashes']]
                            wanted=apply_episode(base,row['d4_transform'],row['color_permutation'])
                            self.assertEqual(row['train'],wanted[:3])
                            self.assertEqual(row['test'],[{'input':wanted[-1]['input']}])
                            self.assertEqual(row['solutions'],[wanted[-1]['output']])
                    self.assertLessEqual(stats['max_query_reuse_in_fresh_episodes'],4)
                    self.assertLessEqual(stats['max_pair_reuse_in_fresh_episodes'],32)
                self.assertFalse(used['train'] & used['validation'])
            finally:b.OUT=previous
    def test_clipped_motif_decoys_and_cup_capacity_controls(self):
        motif=importlib.import_module('tasks.task_79369cc6')
        cups=importlib.import_module('tasks.task_7acdf6d3')
        random.seed(32000)
        p=motif.generate(width=30,height=30,motif=[[6,6,4],[6,4,4],[4,4,4]],
                         motif_row=5,motif_col=5,copies=[(28,28,0,False)],
                         clip=True,num_decoys=2)
        self.assertEqual(p['output'],grid(call(solver('79369cc6'),p['input'])))
        self.assertEqual(p['output'][29][29],4)
        self.assertEqual(sum(a!=b for r,s in zip(p['input'],p['output']) for a,b in zip(r,s)),1)
        for options in ({'clip':'yes'},{'num_decoys':1.5},{'num_copies':True}):
            with self.assertRaises(ValueError):motif.generate(**options)
        for options in ({'num_cups':2.5},{'cup_color':True},
                        {'width':8,'height':8,'cups':[('V',0,0,1,0),('V',0,3,1,0)],
                         'fill':[(5,0),(5,2),(5,4),(5,6)]},
                        {'width':8,'height':8,'cups':[('V',0,0,2,0)],
                         'fill':[(0,2),(6,0),(6,3),(6,6)]}):
            with self.assertRaises(ValueError):cups.generate(**options)
        for cup,fill in ((2,9),(9,2),(0,8)):
            random.seed(30000)
            p=cups.generate(width=30,height=12,num_cups=4,cup_color=cup,fill_color=fill)
            self.assertEqual(p['output'],grid(call(solver('7acdf6d3'),p['input'])))
            self.assertEqual(sum(r.count(fill) for r in p['input']),
                             sum(r.count(fill) for r in p['output']))

    def test_graph_route_ambiguity_is_rejected(self):
        m=importlib.import_module('tasks.task_7b0280bc')
        # Two equal endpoint routes through opposite sides of the diamond.
        kwargs=dict(width=12,height=12,background=0,line_color=1,node_color=2,end_color=4,
                    blocks=[[0,5,2],[5,0,2],[5,10,2],[10,5,2],[0,0,2]],ends=[0,3],
                    strokes=[[[2,4],[3,3],[4,2]],[[2,7],[3,8],[4,9]],
                             [[7,2],[8,3],[9,4]],[[7,9],[8,8],[9,7]],[[2,0],[3,0]]])
        with self.assertRaisesRegex(ValueError,'unique shortest'):m.generate(**kwargs)
        for options in ({'background':True},{'width':20.0},{'thickness':True}):
            with self.assertRaises(ValueError):m.generate(**options)
        random.seed(50000)
        pair=m.generate(width=30,height=30,block_size=3,thickness=2,extra_links=2)
        self.assertEqual(pair['output'],grid(call(solver('7b0280bc'),pair['input'])))

    def test_path_order_and_strict_controls(self):
        m=importlib.import_module('tasks.task_7b5033c1')
        pair=m.generate(width=16,height=16,background=2,start=[2,1],
                        moves='RRRDDRDDDLDDDRRRDDRRRUUR',
                        runs=[(1,5),(3,3),(8,6),(4,6),(1,3),(3,2)])
        self.assertEqual(pair['output'],[[v] for v,n in [(1,5),(3,3),(8,6),(4,6),(1,3),(3,2)] for _ in range(n)])
        self.assertEqual(pair['output'],grid(call(solver('7b5033c1'),pair['input'])))
        for options in ({'width':True},{'runs':[(1.9,3)]},{'start':[1.5,2]},
                        {'consistent_ends':'yes'},{'moves':['R'],'start':[0,0]}):
            with self.assertRaises(ValueError):m.generate(**options)
        random.seed(50000)
        pair=m.generate(width=8,height=8,length=30)
        self.assertEqual(len(pair['output']),30)
        self.assertEqual(pair['output'],grid(call(solver('7b5033c1'),pair['input'])))

    def test_assembly_large_output_and_impossible_controls(self):
        m=importlib.import_module('tasks.task_7b3084d4')
        for options in ({'width':5,'height':5},{'colors':{1,2,3}},{'square':[1,2,3,4]}):
            with self.assertRaises(ValueError):m.generate(**options)
        random.seed(50000)
        pair=m.generate(size=14,width=20,height=20)
        self.assertEqual((len(pair['input']),len(pair['input'][0])),(20,20))
        self.assertEqual((len(pair['output']),len(pair['output'][0])),(14,14))
        self.assertEqual(pair['output'],grid(call(solver('7b3084d4'),pair['input'])))
        pair=m.generate(size=5,width=30,height=12,colors=[9,1,2])
        self.assertEqual([pair['output'][0][-1],pair['output'][-1][0],pair['output'][-1][-1]],[9,1,2])

    def test_rectangle_blob_decoys_and_packing_bound(self):
        m=importlib.import_module('tasks.task_7bb29440')
        with self.assertRaises(ValueError):m.generate(width=10,height=10,num_rects=5)
        with self.assertRaises(ValueError):m.generate(width=12,height=12,num_rects=2.0,rects=[])
        with self.assertRaises(ValueError):m.generate(width=12,height=12,rects=[5,6])
        for seed in range(12):
            random.seed(seed)
            for mode,count in [('sep',3),('run3',4)]:
                cells=set(m._place_specials(6,6,count,mode))
                remaining=set(cells);components=0
                while remaining:
                    components+=1;todo=[remaining.pop()]
                    for r,c in todo:
                        for dr in [-1,0,1]:
                            for dc in [-1,0,1]:
                                q=(r+dr,c+dc)
                                if q in remaining:remaining.remove(q);todo.append(q)
                self.assertEqual(components,count if mode=='sep' else count-2)
        random.seed(60000)
        pair=m.generate(width=30,height=30,num_rects=7)
        self.assertEqual(pair['output'],grid(call(solver('7bb29440'),pair['input'])))

    def test_one_shape_three_band_nest_and_stamp_collisions(self):
        m=importlib.import_module('tasks.task_7c66cb00')
        for height in [18,19]:
            with self.assertRaises(ValueError):m.generate(height=height,num_bands=3,num_shapes=1)
        for height in [20,30]:
            random.seed(60000)
            pair=m.generate(width=24,height=height,num_bands=3,num_shapes=1)
            self.assertEqual(pair['output'],grid(call(solver('7c66cb00'),pair['input'])))
        with self.assertRaisesRegex(ValueError,'overlap'):
            m.generate(width=12,height=20,background=0,bands=[(8,3,2,5),(13,3,3,6)],
                       shapes=[(0,1,['22']),(3,1,['22']),(0,6,['33'])])
        with self.assertRaises(ValueError):m.generate(background=True)

    def test_mirror_occlusion_preserves_occupied_input(self):
        m=importlib.import_module('tasks.task_7ed72f31')
        pair=m.generate(width=15,height=14,background=0,objects=[
            {'mirror':['v',5,4,8],'color':3,'cells':[[6,1],[6,2],[6,3],[6,4]]},
            {'mirror':['p',6,10],'color':4,'cells':[[6,9],[7,9]]}])
        self.assertEqual(pair['output'],grid(call(solver('7ed72f31'),pair['input'])))
        self.assertEqual(pair['output'][6][6:10],[3,3,3,4])
        self.assertEqual(pair['output'][5][11],4)
        self.assertEqual(pair['output'][6][11],4)
        with self.assertRaises(ValueError):
            m.generate(width=3,height=3,background=0,objects=[{'mirror':['p',1,1],
                       'color':4,'cells':[[0,0],[0,1],[0,2],[1,0],[1,2]]}])
        with self.assertRaises(ValueError):m.generate(background=True)

    def test_row_relocation_uses_anchor_without_left_run(self):
        m=importlib.import_module('tasks.task_984d8a3e')
        pair=m.generate(width=9,colors=[8,0,2],rows=[(0,3),(4,6),(2,7),(1,6),(2,5)])
        self.assertEqual(pair['output'],[[0,0,0,2,2,2,2,2,2],
            [8,0,0,8,8,8,2,2,2],[0,0,0,0,0,8,8,2,2],
            [0,0,0,0,0,8,2,2,2],[0,0,0,8,8,2,2,2,2]])
        self.assertEqual(pair['output'],grid(call(solver('984d8a3e'),pair['input'])))
        for options in ({'colors':5},{'width':6,'rows':[5]},
                        {'width':6,'rows':5},{'width':6,'rows':[]}):
            with self.assertRaises(ValueError):m.generate(**options)

    def test_row_relocation_scales_features_and_preserves_minimum(self):
        m=importlib.import_module('tasks.task_984d8a3e')
        long_run=False;wide_edge=False
        for seed in range(40):
            random.seed(seed)
            pair=m.generate(width=30,height=30,colors=[0,1,2])
            self.assertEqual(pair['output'],grid(call(solver('984d8a3e'),pair['input'])))
            starts=[]
            for row in pair['input']:
                left=next(i for i,c in enumerate(row) if c!=0)
                long_run|=left>9
                if 2 in row:starts.append(row.index(2))
            wide_edge|=max(starts)-min(starts)>7
        self.assertTrue(long_run);self.assertTrue(wide_edge)
        for w,h in [(4,2),(5,3),(30,2),(4,30)]:
            pair=m.generate(width=w,height=h)
            self.assertEqual((len(pair['input']),len(pair['input'][0])),(h,w))
            self.assertEqual(pair['output'],grid(call(solver('984d8a3e'),pair['input'])))

    def test_marked_stacks_partial_width_and_offset(self):
        m=importlib.import_module('tasks.task_9aaea919')
        for seed in range(20):
            random.seed(seed)
            for kw in ({'width':11,'height':30},{'width':30,'left':19,'height':30}):
                p=m.generate(**kw)
                self.assertEqual(len(p['input'][0]),kw['width'])
                self.assertEqual(p['output'],grid(call(solver('9aaea919'),p['input'])))
        for kw in ({'colors':5},{'heights':5},{'markers':5},{'colors':[None,1]},
                   {'heights':[1,None]},{'width':10},{'width':30,'left':20}):
            with self.assertRaises(ValueError):m.generate(**kw)

    def test_marked_stacks_total_applies_to_each_target(self):
        m=importlib.import_module('tasks.task_9aaea919')
        p=m.generate(width=30,height=30,bg=4,colors=[2,3,6,8],
                     heights=[2,2,1,2],markers=[2,2,3,3])
        self.assertEqual(sum(row.count(5) for row in p['output']),44)
        self.assertEqual(sum(row.count(6) for row in p['output']),55)
        self.assertEqual(sum(row.count(8) for row in p['output']),66)
        self.assertEqual(p['output'][-1],[4]*30)
        self.assertEqual(p['output'],grid(call(solver('9aaea919'),p['input'])))
        p=m.generate(height=30,heights=[6,1,7],markers=[2,3,None])
        self.assertEqual(p['output'],grid(call(solver('9aaea919'),p['input'])))

if __name__=='__main__':unittest.main()
