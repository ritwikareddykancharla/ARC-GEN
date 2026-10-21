"""Portable input-only and ambiguity-regression tests for 1b8318e3."""
import json
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch
from . import pixel_docking_evidence as evidence
from .augmentation import transformed
from .colour_evidence import MissingColourEvidence
from .direct_factories.task_1b8318e3 import build_program

class QueryInputOnly(Mapping):
    def __init__(self, grid): self.grid = grid
    def __getitem__(self, key):
        if key != 'input': raise AssertionError('query-label access: '+str(key))
        return self.grid
    def __iter__(self): raise AssertionError('query iteration may expose labels')
    def __len__(self): raise AssertionError('query enumeration is forbidden')

class PixelDockingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = json.loads((Path(__file__).parent/'references/1b8318e3.json').read_text())['canonical']
        cls.palette = list(range(10))
    def test_canonical_all_d4_palettes_query_output_trap(self):
        for pal in (self.palette, [3,9,0,7,2,8,1,6,4,5]):
            for d4 in range(8):
                demos = [{k:transformed(p[k], d4, pal) for k in ('input','output')} for p in self.task['train']]
                query = transformed(self.task['test'][0]['input'],d4,pal)
                got=evidence.assess_evidence(demos,[QueryInputOnly(query)],pal)
                self.assertEqual(got['surviving_rules'],['king'])
                evidence.require_evidence(demos,[{'input':query,'output':'POISON','solutions':object()}],pal)
                ns={};exec(build_program(d4,pal),ns)
                self.assertEqual(ns['solve'](demos,query),transformed(self.task['test'][0]['output'],d4,pal))
    def test_context_shortfall_keeps_native_unique_query(self):
        query=self.task['train'][0]['input']
        evidence.require_native_input(query)
        with self.assertRaises(evidence.DockingContextAmbiguity):
            evidence.require_evidence(self.task['train'][1:],[QueryInputOnly(query)])
        evidence.require_evidence(self.task['train'],[QueryInputOnly(query)])
    def test_intrinsic_hidden_order_twin(self):
        from tasks.task_1b8318e3 import generate
        fixed=dict(size=15,brows=[1,2,5,12,12],bcols=[10,1,11,3,12])
        a=dict(prows=[4,2,2,3,3,4,6,7,7,7,7,11,12,12,12,12,14],pcols=[6,9,14,5,7,13,1,2,3,4,6,14,1,7,9,14,2],pcolors=[1,7,2,3,4,6,2,3,9,8,9,8,4,9,9,9,8])
        b=dict(prows=[7,2,2,3,3,4,4,6,7,7,7,11,12,12,12,12,14],pcols=[3,9,14,5,7,6,13,1,2,4,6,14,1,7,9,14,2],pcolors=[9,7,2,3,4,1,6,2,3,8,9,8,4,9,9,9,8])
        x,y=generate(**fixed,**a),generate(**fixed,**b)
        self.assertEqual(x['input'],y['input']);self.assertNotEqual(x['output'],y['output'])
        with self.assertRaises(evidence.DockingContextAmbiguity):
            evidence.require_evidence([x],[QueryInputOnly(self.task['test'][0]['input'])])
        # An ambiguous query takes precedence over an ambiguous demonstration.
        with self.assertRaises(evidence.IntrinsicDockingAmbiguity):
            evidence.require_evidence([x],[QueryInputOnly(x['input'])])
        for pal in (self.palette,[3,9,0,7,2,8,1,6,4,5]):
            for d4 in range(8):
                query=transformed(x['input'],d4,pal)
                with self.assertRaises(evidence.IntrinsicDockingAmbiguity):evidence.require_native_input(query,pal)
        with self.assertRaises(evidence.IntrinsicDockingAmbiguity):
            evidence.require_evidence(self.task['train'],[QueryInputOnly(x['input'])])
    def test_no_labels_in_query_enumeration(self):
        original=evidence.enumerate_outputs;query_args=evidence.scene(self.task['test'][0]['input']);calls=[]
        def spy(args,*a,**kw):
            if args==query_args:calls.append(kw.get('check_label'))
            return original(args,*a,**kw)
        with patch.object(evidence,'enumerate_outputs',spy):
            evidence.require_evidence(self.task['train'],[QueryInputOnly(self.task['test'][0]['input'])])
        self.assertTrue(calls);self.assertTrue(all(x is None for x in calls))
    def test_budget_never_admits_partial_uniqueness(self):
        with patch.object(evidence,'enumerate_outputs',side_effect=evidence.Budget):
            with self.assertRaises(evidence.DockingSearchBudget):
                evidence.require_evidence(self.task['train'],[QueryInputOnly(self.task['test'][0]['input'])])
    def test_invalid_demos_and_geometry_rejected(self):
        q=QueryInputOnly(self.task['test'][0]['input'])
        with self.assertRaises(MissingColourEvidence):evidence.require_evidence([], [q])
        with self.assertRaises(MissingColourEvidence):evidence.require_evidence([{'input':self.task['train'][0]['input'],'output':[[0]]}],[q])
        with self.assertRaises(MissingColourEvidence):evidence.require_native_input([[5,5,0],[5,0,1],[0,0,0]])
        with self.assertRaises(MissingColourEvidence):evidence.require_native_input(self.task['test'][0]['input'],[0]*10)
    def test_factory_has_no_hidden_d4_selector(self):
        self.assertEqual(build_program(0,self.palette),build_program(7,self.palette))

if __name__=='__main__':unittest.main()
