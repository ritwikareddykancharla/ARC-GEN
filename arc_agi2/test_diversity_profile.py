"""Regressions for broadened construction, target certification and split identity."""
import importlib
import json
import random

import numpy as np

from .augmentation import transformed
from .diversity.prepare import REPAIRED, input_orbit
from .diversity.sampler import eligible, sample_checked
from .program_targets import compile_target
from .runtime import BASE, call, grid, reference, solver, verification_solver


def test_modified_constructors_retain_every_original_pair_and_target_admission():
    for tid in REPAIRED:
        replay = importlib.import_module('tasks.task_' + tid).validate()
        canonical = reference(tid)['canonical']
        for split in ('train', 'test'):
            assert sorted(json.dumps(p, sort_keys=True) for p in replay[split]) == sorted(
                json.dumps(p, sort_keys=True) for p in canonical[split])
        for d4 in range(8):
            source, basis = compile_target(tid, d4, [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])
            assert basis == 'reviewed_direct_coordinate_rewrite'
            assert 'def solve(' in source


def test_rectangular_self_tiling_matches_kronecker_product():
    from tasks.task_007bbfb7 import generate
    for h, w in ((2, 5), (5, 2), (4, 5)):
        for seed in range(12):
            random.seed(seed)
            p = generate(height=h, width=w)
            inp = np.array(p['input'])
            assert inp.shape == (h, w)
            assert p['output'] == np.kron(inp != 0, inp).tolist()
            assert grid(verification_solver('007bbfb7')(p['input'])) == p['output']


def test_short_wide_gravity_is_bounded_and_preserves_columns():
    from tasks.task_1e0a9b12 import generate
    for seed in range(20):
        random.seed(seed)
        p = call(generate, height=4, width=30, seconds=1)
        assert (len(p['input']), len(p['input'][0])) == (4, 30)
        for c in range(30):
            cells = [row[c] for row in p['input'] if row[c] != 0]
            assert [row[c] for row in p['output']] == [0] * (4-len(cells)) + cells


def test_dense_counting_witness_disproves_modal_background():
    p = json.loads((BASE / 'reports/diversity-v1/aaecdb9a-dense-counterexample.json').read_text())
    assert grid(solver('aaecdb9a')(p['input'])) != p['output']
    assert grid(verification_solver('aaecdb9a')(p['input'])) == p['output']


def test_broader_sampler_is_deterministic_and_does_not_consume_caller_rng():
    tid = '0962bcdd'
    assert eligible(tid)
    random.seed(654)
    before = random.getstate()
    first, metadata = sample_checked(tid, 456)
    assert random.getstate() == before
    second, _ = sample_checked(tid, 456)
    assert first == second
    assert metadata['verifiers_checked'] == 2


def test_orbit_identity_matches_existing_global_split_and_augmentations():
    from .build_million import canonical_input
    g = [[0, 1, 2, 0], [3, 3, 0, 1]]
    assert input_orbit(g) == canonical_input(g)
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
    for d4 in range(8):
        assert input_orbit(transformed(g, d4, palette)) == input_orbit(g)
