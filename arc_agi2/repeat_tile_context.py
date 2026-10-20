"""Preserve both native repeat-tile labels under an episode-shared convention.

A4x4input repeating both ways can have either2x4or4x2as its native label.
Independent per-pair latent axes cannot be inferred from demonstrations. We
choose one convention before sampling the episode and use native explicit
constructors to realize it. Original generate()/validate() remain unchanged.
"""
import json
import random
import numpy as np
from .colour_evidence import MissingColourEvidence, _require_rule_agreement


def repeat_variants(grid):
    g=np.asarray(grid)
    if g.ndim!=2:
        raise MissingColourEvidence('7b7f7511: expected rectangular grid')
    candidates=[]
    for axis in (0,1):
        shape=list(g.shape)
        if shape[axis]%2:continue
        shape[axis]//=2
        if not all(2<=n<=4 for n in shape):continue
        a,b=np.split(g,2,axis=axis)
        if np.array_equal(a,b):candidates.append(a.tolist())
    if not candidates:
        raise MissingColourEvidence('7b7f7511: no repeated2..4tile interpretation')
    return candidates*2 if len(candidates)==1 else candidates


def require_repeat_evidence(demonstrations,queries):
    _require_rule_agreement('7b7f7511',demonstrations,queries,repeat_variants)


def _pair(rng,axis,force_ambiguous=False):
    from tasks import task_7b7f7511 as native
    colours=rng.sample(range(1,10),rng.randint(3,4))
    if force_ambiguous:
        block=[rng.choice(colours) for _ in range(4)]
        width,height,vert=2,4,0
        pixels=block+block
    else:
        width,height=rng.randint(2,4),rng.randint(2,4)
        vert=rng.randrange(2)
        pixels=[rng.choice(colours) for _ in range(width*height)]
    pair=native.generate(width=width,height=height,vert=vert,colors=pixels)
    g=pair['input']
    # This is the entire native collision domain. Keep the input, realize
    # the preselected episode convention with the native explicit constructor.
    ambiguous=(len(g)==len(g[0])==4 and g[:2]==g[2:]
               and all(row[:2]==row[2:] for row in g))
    if ambiguous:
        width,height,vert=(4,2,1) if axis==0 else (2,4,0)
        pixels=[v for row in g[:height] for v in row[:width]]
        pair=native.generate(width=width,height=height,vert=vert,colors=pixels)
        assert pair['input']==g
    parameters=dict(width=width,height=height,vert=vert,colors=pixels)
    return pair,parameters,ambiguous


def generate_episode(sample_seed,canonical_input,digest,force_ambiguous_query=False):
    """Three demos and fixed query, with deterministic input-class split.

Policy is selected before query generation, never from a query answer. Demo
selection depends on input equivalence/split and visible query ambiguity only.
Every saved pair contains exact native constructor parameters for replay.
"""
    rng=random.Random(sample_seed);axis=rng.randrange(2)
    query,parameters,ambiguous=_pair(rng,axis,force_ambiguous_query)
    query_class=canonical_input(query['input'])
    split='validation' if int(query_class[:8],16)%20==0 else 'train'
    seen={query_class};demos=[];draws=0
    def row(pair,params,index):
        return dict(task_id='7b7f7511',**pair,seed=sample_seed,
                    parameters=json.dumps(dict(native_parameters=params,episode_seed=sample_seed,
                                              episode_tie_axis=axis,pair_index=index),sort_keys=True),
                    generator_mode='episode_shared_repeat_axis',input_hash=digest(pair['input']),
                    canonical_input_hash=canonical_input(pair['input']),split=split)
    while len(demos)<3 and draws<1000:
        draws+=1
        # A matching pair from a different input-equivalence class teaches the
        # tie; its expected output follows the policy chosen before the query.
        pair,params,_=_pair(rng,axis,force_ambiguous=ambiguous and not demos)
        identity=canonical_input(pair['input'])
        pair_split='validation' if int(identity[:8],16)%20==0 else 'train'
        if identity in seen or pair_split!=split:continue
        demos.append(row(pair,params,len(demos)));seen.add(identity)
    if len(demos)!=3:raise ValueError('No three-demo repeat-tile context in the input split')
    q=row(query,parameters,3)
    require_repeat_evidence(demos,[{'input':q['input']}])
    context_id=digest(dict(seed=sample_seed,axis=axis,query=query_class))
    return demos+[q],context_id
