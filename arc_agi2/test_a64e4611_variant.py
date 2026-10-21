"""Integration checks for the declared a64 visible-clearance synthetic variant."""
import ast
import copy
import hashlib
import importlib.util
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .runtime import reference
from .augmentation import transformed
from .colour_evidence import require_colour_evidence, MissingColourEvidence
from .direct_factories import task_a64e4611 as factory
from .synthetic_variants import variant_provenance
from tasks import task_a64e4611 as constructor

BASE = Path(__file__).resolve().parent
CANONICAL = reference('a64e4611')['canonical']
PAL = list(range(10))

class VariantTests(unittest.TestCase):
    def test_constructor_ast_identical_to_audited_except_metadata(self):
        actual = ast.parse(Path(constructor.__file__).read_text())
        actual.body = [x for x in actual.body if not (isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SYNTHETIC_VARIANT' for t in x.targets))]
        audited = ast.parse((BASE/'reports/coverage-evidence/a64e4611/hypothesis-audit-bundle/proposed_constructor.py').read_text())
        self.assertEqual(ast.dump(actual), ast.dump(audited))
        archive = BASE/'archives/task_a64e4611_native_06ef672f.py'
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), constructor.SYNTHETIC_VARIANT['original_native_sha256'])
        native_fixture = constructor.validate()
        for split in ('train', 'test'):
            self.assertEqual(sorted(json.dumps(p, sort_keys=True) for p in native_fixture[split]),
                             sorted(json.dumps(p, sort_keys=True) for p in CANONICAL[split]))

    def test_installed_canonical_and_gate_16_variants(self):
        for pal in (PAL, [3,9,0,7,2,8,1,6,4,5]):
            for d4 in range(8):
                demos = [{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in CANONICAL['train']]
                queries = [{'input':transformed(p['input'],d4,pal)} for p in CANONICAL['test']]
                require_colour_evidence('a64e4611',demos,queries,pal,d4)
                ns = {}; exec(factory.build_program(d4,pal),ns)
                for p in CANONICAL['train']+CANONICAL['test']:
                    self.assertEqual(ns['solve'](demos,transformed(p['input'],d4,pal)),transformed(p['output'],d4,pal))

    def test_generation_uses_only_declared_variant(self):
        from . import build_million as builder
        with tempfile.TemporaryDirectory() as directory, patch.object(builder,'OUT',Path(directory)), patch.object(builder,'POOL_SIZE',8):
            report=builder.make_pool('a64e4611')
            self.assertEqual(report['pairs'],8)
            self.assertEqual(report['modes'],{'default':8})
            rows=builder.pq.read_table(Path(directory)/'pools/a64e4611.parquet').to_pylist()
            for p in rows:
                random.seed(p['seed'])
                expected=constructor.generate()
                self.assertEqual(p['input'],expected['input'])
                self.assertEqual(p['output'],expected['output'])

    def test_record_carries_variant_provenance(self):
        from . import program_targets as targets
        episode={'task_id':'a64e4611','episode_id':'a64-variant-test','train':CANONICAL['train'],'test':[{'input':p['input']} for p in CANONICAL['test']],'solutions':[p['output'] for p in CANONICAL['test']]}
        source=factory.build_program(0,PAL)
        with patch.object(targets,'compile_target',return_value=(source,'pre-admission test factory')):
            record=targets.make_record(episode)
        meta=record['synthetic_variant']
        self.assertFalse(meta['native_equivalent'])
        self.assertFalse(meta['canonical_fixture_labels_changed'])
        self.assertEqual(meta['id'],'a64e4611-visible-clearance-v1')
        self.assertTrue(record['verification']['all_exact'])
        self.assertNotIn('native_equivalent',record['prompt'])
        self.assertEqual(meta['constructor_sha256'],hashlib.sha256(Path(constructor.__file__).read_bytes()).hexdigest())
        copied=variant_provenance('a64e4611');copied['constructor_parameters']['minimum_safe_run']=1
        self.assertEqual(variant_provenance('a64e4611')['constructor_parameters']['minimum_safe_run'],12)

if __name__ == '__main__': unittest.main()
