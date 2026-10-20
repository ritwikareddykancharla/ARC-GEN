import hashlib,importlib,json,random,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import pyarrow.parquet as pq
from . import build_million as b
from .generators.registry import GENERATORS,generate
from .runtime import BASE,reference,solver,call,grid,check_reference
from .task_registry import NEW_TASK_IDS
from .augmentation import apply_episode,settings

class GeneratorTests(unittest.TestCase):
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
        with self.assertRaisesRegex(RuntimeError,'eight-variant'):
            b.require_build_ready(all_ready)
        with patch.dict(b.POLICY['planned_dataset'],bulk_builder_expansion_pending=False):
            with self.assertRaisesRegex(RuntimeError,'reviewed standalone'):
                b.require_build_ready(all_ready)
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
                    for r in saved:
                        self.assertEqual(len(r['train']),3);self.assertEqual(len(r['test']),1)
                        self.assertEqual(set(r['test'][0]),{'input'})
                        self.assertEqual(json.loads(r['completion']),{'outputs':r['solutions']})
                        self.assertEqual(json.loads(r['prompt'].split('\n',1)[1]),{'train':r['train'],'test':r['test']})
                        self.assertEqual(len(set(r['canonical_input_hashes'])),4)
                        used[split].update(r['canonical_input_hashes'])
                self.assertFalse(used['train'] & used['validation'])
            finally:b.OUT=previous
if __name__=='__main__':unittest.main()
