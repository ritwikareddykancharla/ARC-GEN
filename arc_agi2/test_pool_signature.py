"""Resuming pools must respect changed acceptance policies and target programs."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import build_million as builder

class PoolSignature(unittest.TestCase):
    def test_target_and_evidence_changes_invalidate_cached_pool(self):
        tid='01234567'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);base=root/'arc_agi2';base.mkdir();(base/'build_million.py').write_text('builder')
            for name in ['runtime.py','verified_rules.py','joint_fragments.py','contextual.py','motif_context.py','repeat_tile_context.py','program_targets.py','direct_programs.py','fixture_policy.py','helpers.py','training_policy.json','task_registry.py','colour_evidence.py','other_rule_evidence.py','references/'+tid+'.json','direct_factories/task_'+tid+'.py','direct_factories/'+tid+'.json','reports/direct-certificates/'+tid+'.json','generators/example.py']:
                p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('initial')
            (root/'common.py').write_text('initial');(root/'tasks').mkdir();(root/'tasks'/('task_'+tid+'.py')).write_text('initial')
            with patch.object(builder,'BASE',base),patch.object(builder,'__file__',str(base/'build_million.py')),patch.object(builder,'OUTPUT_FORMAT','program-grid-png'):
                original=builder.pool_signature(tid,[])
                for name in ['colour_evidence.py','other_rule_evidence.py','direct_factories/task_'+tid+'.py','direct_factories/'+tid+'.json','reports/direct-certificates/'+tid+'.json']:
                    p=base/name;p.write_text('changed')
                    self.assertNotEqual(builder.pool_signature(tid,[]),original,name)
                    p.write_text('initial')
                    self.assertEqual(builder.pool_signature(tid,[]),original)
                with patch.object(builder,'OUTPUT_FORMAT','legacy-grid-parquet'):
                    self.assertNotEqual(builder.pool_signature(tid,[]),original)
                self.assertNotEqual(builder.pool_signature(tid,[{'parameters':{'size':25}}]),original)
if __name__=='__main__':unittest.main()
