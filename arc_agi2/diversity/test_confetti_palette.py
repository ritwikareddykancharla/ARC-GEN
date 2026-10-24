import random
import pytest
from tasks.task_f0df5ff0 import generate,validate
from arc_agi2.runtime import reference,grid,verification_solver
from arc_agi2.diversity.recertify import episode
from arc_agi2.direct_factories.task_f0df5ff0 import build_program
from arc_agi2.program_targets import verify


def test_original_labels():
    assert validate() == reference('f0df5ff0')['canonical']
    assert max(len({c for row in p['input'] for c in row}-{0,1}) for p in validate()['train']) >= 7


@pytest.mark.parametrize('n',range(1,9))
def test_palette_actual_count_and_labels(n):
    random.seed(100+n)
    pairs=[generate(width=15,height=15,num_boxes=4,num_confetti_colors=n) for _ in range(4)]
    for p in pairs:
        assert len({c for row in p['input'] for c in row}-{0,1})==n
        assert grid(verification_solver('f0df5ff0')(p['input']))==p['output']
    palette=[3,9,0,7,2,8,1,6,4,5]
    for d4 in range(8): verify(build_program(d4,palette),episode(pairs,d4,palette))


@pytest.mark.parametrize('kwargs',[dict(num_confetti_colors=True),dict(num_confetti_colors=0),
    dict(num_confetti_colors=9),dict(width=3,height=3,num_boxes=1,num_confetti_colors=7),
    dict(colors=[0]*225,num_confetti_colors=2)])
def test_invalid_palette_requests(kwargs):
    with pytest.raises(ValueError):generate(**kwargs)


def test_default_reaches_all_palette_counts():
    random.seed(2026102507)
    values={len({c for row in generate()['input'] for c in row}-{0,1}) for _ in range(300)}
    assert values==set(range(1,9))
