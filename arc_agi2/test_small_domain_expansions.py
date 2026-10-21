"""Dimension changes retain the native count rule under every augmentation."""
import itertools
import random
from .augmentation import transformed
from .program_targets import audit_target
from .direct_factories.task_794b24be import build_program
from tasks.task_794b24be import generate, validate


def test_count_target_original_fixtures_all_d4():
    fixture = validate()
    for palette in (list(range(10)), [9,3,7,0,5,1,8,2,6,4]):
        for d4 in range(8):
            scope = {}
            exec(build_program(d4, palette), scope)
            for pair in fixture['train'] + fixture['test']:
                assert scope['solve']([], transformed(pair['input'], d4, palette)) == transformed(pair['output'], d4, palette)


def test_count_target_exhaustive_small_domains_all_d4():
    palettes=[list(range(10)),[9,3,7,0,5,1,8,2,6,4]]
    for palette in palettes:
        solvers=[]
        for d4 in range(8):
            source=build_program(d4,palette)
            audit_target('794b24be',source)
            scope={};exec(source,scope);solvers.append(scope['solve'])
        for size in (3,4):
            for count in range(1,5):
                for positions in itertools.combinations(range(size*size),count):
                    p=generate(rows=[x//size for x in positions],cols=[x%size for x in positions],size=size)
                    for d4,solve in enumerate(solvers):
                        assert solve([],transformed(p['input'],d4,palette))==transformed(p['output'],d4,palette)


def test_count_target_larger_canvas_regression():
    rng=random.Random(123)
    for size in (5,12,30):
        for count in range(1,5):
            positions=rng.sample(range(size*size),count)
            p=generate(rows=[x//size for x in positions],cols=[x%size for x in positions],size=size)
            for d4 in range(8):
                source=build_program(d4,list(range(10)))
                scope={};exec(source,scope)
                assert scope['solve']([],transformed(p['input'],d4,list(range(10))))==transformed(p['output'],d4,list(range(10)))
