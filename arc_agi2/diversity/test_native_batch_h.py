import json
import random
import pytest
from tasks.task_6d1d5c90 import generate, validate
from arc_agi2.runtime import reference, verification_solver, grid
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import require_colour_evidence, MissingColourEvidence
from arc_agi2.direct_factories.task_6d1d5c90 import build_program
from arc_agi2.program_targets import verify
from arc_agi2.diversity.recertify import episode


def test_unchanged_fixtures():
    f=reference('6d1d5c90')['canonical']
    for split in ('train','test'):
        assert sorted(map(json.dumps,validate()[split]))==sorted(map(json.dumps,f[split]))


@pytest.mark.parametrize('h,w',[(2,1),(2,29),(30,1),(30,29),(6,6),(3,8),(8,3)])
@pytest.mark.parametrize('style',['bars','blocks','pixels'])
def test_expanded_corners(h,w,style):
    pairs=[]
    for i in range(4):
        random.seed(i)
        p=generate(height=h,width=w,style=style,marker_row=i%h)
        assert len(p['input'])==h and len(p['input'][0])==w+1
        assert grid(verification_solver('6d1d5c90')(p['input']))==p['output']
        pairs.append(p)
    palette=[3,9,0,7,2,8,1,6,4,5]
    for d4 in range(8):
        verify(build_program(d4,palette),episode(pairs,d4,palette))


@pytest.mark.parametrize('n',range(1,9))
def test_requested_colours_really_used(n):
    p=generate(height=6,width=6,num_colors=n)
    assert len({v for row in p['input'] for v in row[1:]})==n
    assert len({v for row in p['input'] for v in row})==n+2


@pytest.mark.parametrize('kwargs',[{'height':1},{'width':30},{'height':True},{'marker_row':30},{'num_colors':9},{'style':'unknown'}])
def test_invalid_arguments(kwargs):
    with pytest.raises(ValueError):generate(**kwargs)


def informative(p):
    return generate(colors=sum(([2 if r==p else 6]+[r,(r+1)%6,(r+3)%6] for r in range(6)),[]),height=6,width=3)


@pytest.mark.parametrize('d4',range(8))
def test_constant_shift_ambiguity_and_resolution(d4):
    pal=[3,9,0,7,2,8,1,6,4,5]
    tr=lambda p:{k:transformed(g,d4,pal) for k,g in p.items()}
    demos=[tr(informative(0)) for _ in range(3)]
    q=tr(informative(1))['input']
    with pytest.raises(MissingColourEvidence):require_colour_evidence('6d1d5c90',demos,[{'input':q}],pal,d4)
    demos=[tr(informative(p)) for p in (0,2,3)]
    require_colour_evidence('6d1d5c90',demos,[{'input':q}],pal,d4)


@pytest.mark.parametrize('d4',range(8))
def test_canonical_context(d4):
    pal=[3,9,0,7,2,8,1,6,4,5]
    f=reference('6d1d5c90')['canonical']
    demos=[{k:transformed(g,d4,pal) for k,g in p.items()} for p in f['train']]
    queries=[{'input':transformed(p['input'],d4,pal)} for p in f['test']]
    require_colour_evidence('6d1d5c90',demos,queries,pal,d4)
