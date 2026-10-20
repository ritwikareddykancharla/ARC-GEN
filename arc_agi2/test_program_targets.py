import copy
import unittest
from .augmentation import transformed
from .runtime import reference
from .program_targets import compile_target, audit_target, verify, make_record, TargetError

class ProgramTargets(unittest.TestCase):
    def episode(self, tid, d4=0, palette=None):
        palette = palette or list(range(10))
        task=reference(tid)['teaching_fixture']
        return dict(task_id=tid,episode_id='unit-'+tid,d4_transform=d4,color_permutation=palette,
            train=[{k:transformed(p[k],d4,palette) for k in ('input','output')} for p in task['train']],
            test=[{'input':transformed(p['input'],d4,palette)} for p in task['test']],
            solutions=[transformed(p['output'],d4,palette) for p in task['test']])

    def test_standalone_and_all_augmentations(self):
        for tid in ('0692e18c','00dbd492','00576224','f18ec8cc'):
            for d4 in range(8):
                palette=[3,9,0,7,2,8,1,6,4,5]
                ep=self.episode(tid,d4,palette)
                source,_=compile_target(tid,d4,palette)
                audit_target(tid,source)
                self.assertTrue(verify(source,ep)['all_exact'],(tid,d4))
                self.assertNotIn('arc_agi2',source)

    def test_query_labels_do_not_construct_program(self):
        ep=self.episode('0692e18c')
        source,_=compile_target(ep['task_id'],ep['d4_transform'],ep['color_permutation'])
        record=make_record(ep)
        altered=copy.deepcopy(ep)
        altered['solutions'][0][0][0]=(altered['solutions'][0][0][0]+1)%10
        source2,_=compile_target(altered['task_id'],altered['d4_transform'],altered['color_permutation'])
        self.assertEqual(source,source2)
        with self.assertRaisesRegex(TargetError,'not exact'):
            make_record(altered)
        self.assertEqual(record['program'],source)
        self.assertIn('```python',record['completion'])
        self.assertIn('```json',record['completion'])
        self.assertEqual(record['episode_id'],ep['episode_id'])
        self.assertEqual(record['mode'],'PROGRAM_AND_GRID')
        self.assertNotIn('solutions',record['prompt'])

    def test_contextual_programs_are_self_contained(self):
        for tid in ('269e22fb','98c475bf'):
            ep=self.episode(tid)
            source,_=compile_target(tid)
            audit_target(tid,source)
            self.assertTrue(verify(source,ep)['all_exact'])

    def test_original_grid_lookup_is_rejected(self):
        tid='0692e18c';a=reference(tid)['canonical']['test'][0]['output']
        with self.assertRaisesRegex(TargetError,'Literal original grid'):
            audit_target(tid,'def solve(demos, grid):\n    return '+repr(a))

    def test_unreviewed_augmentation_cannot_fall_back_to_wrapper(self):
        with self.assertRaisesRegex(TargetError, 'rewrite required'):
            compile_target('e12f9a14',1)

    def test_no_state_retained_between_pairs(self):
        ep=self.episode('0692e18c')
        source,_=compile_target('0692e18c')
        source+='\n_original_solve=solve\n_calls=0\ndef solve(demos, query):\n    global _calls\n    _calls+=1\n    if _calls!=1: raise RuntimeError("state leaked")\n    return _original_solve(demos,query)\n'
        self.assertTrue(verify(source,ep)['all_exact'])

if __name__=='__main__':unittest.main()
