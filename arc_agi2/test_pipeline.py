import hashlib,importlib,json,random,tempfile,unittest
from collections import Counter,defaultdict
from pathlib import Path
from unittest.mock import patch
import pyarrow.parquet as pq
from . import build_million as b
from .generators.registry import GENERATORS,generate
from .runtime import BASE,reference,solver,call,grid,check_reference
from .task_registry import NEW_TASK_IDS
from .augmentation import apply_episode,settings,exhaustive_variants

class GeneratorTests(unittest.TestCase):
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
            expected=reference(tid)['canonical']
            key=lambda p:json.dumps(p,sort_keys=True)
            for split in ['train','test']:
                self.assertEqual(sorted(map(key,actual[split])),sorted(map(key,expected[split])),(tid,split))
            solve=solver(tid)
            for seed in range(10000,10020):
                random.seed(seed)
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
            self.assertTrue(check_reference(tid)['canonical']['all_exact'],tid)
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
if __name__=='__main__':unittest.main()
