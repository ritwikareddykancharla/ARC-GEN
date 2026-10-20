"""Reversible, episode-wide geometry and optional simultaneous colour mapping.

An episode transformation T produces the conjugated rule T f T^-1. It need
not preserve the native rule (e.g. move-left becomes move-up after rotation).
Validate in native coordinates; never reject using f(T(x)) != T(f(x)).
"""
import json

def transformed(g, d4, palette):
    if d4 not in range(8) or sorted(palette) != list(range(10)):
        raise ValueError('Expected D4 index and bijective ten-colour mapping')
    a = [r[:] for r in g]
    if d4 >= 4:
        a = [r[::-1] for r in a]
    for _ in range(d4 % 4):
        a = [list(r) for r in zip(*a[::-1])]
    # Index the original colour once. In-place substitution would cascade.
    return [[palette[c] for c in row] for row in a]

def settings(rng, task_id, policy):
    cfg = policy['augmentation']
    if rng.random() < cfg['native_fraction']:
        return 0, list(range(10))
    d4 = rng.randrange(1, 8)
    palette = list(range(10))
    if cfg['colour_permutation_default'] or task_id in cfg['colour_permutation_task_ids']:
        rng.shuffle(palette)
    return d4, palette

def apply_episode(pairs, d4, palette):
    return [{k: transformed(p[k], d4, palette) for k in ('input', 'output')} for p in pairs]

def exhaustive_variants(pairs, palette=None):
    """All D4 variants of demonstrations followed by one query.

    Equality includes the query answer and the unordered set of complete demo
    pairs. Thus a symmetry that just permutes demonstrations does not create an
    additional puzzle. ``equivalent_d4`` records every represented transform.
    Colour mapping is simultaneous and shared, never independently sampled.
    """
    if len(pairs) < 2:
        raise ValueError('Expected demonstrations followed by a query')
    palette = list(range(10)) if palette is None else list(palette)
    variants = {}
    for d4 in range(8):
        result = apply_episode(pairs, d4, palette)
        encode = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'))
        signature = encode([sorted(encode(p) for p in result[:-1]), result[-1]])
        if signature in variants:
            variants[signature]['equivalent_d4'].append(d4)
        else:
            variants[signature] = {
                'pairs': result, 'd4_transform': d4, 'equivalent_d4': [d4],
                'color_permutation': palette[:],
            }
    return list(variants.values())


def demonstrations_disambiguate(variants):
    """Reject conflicting answers to the same visible augmented puzzle.

    A transform index is generation metadata, not information given to the
    student. Symmetric demonstrations sometimes fail to reveal which direction
    a rule uses. Query answers must therefore be unique given only the complete
    demonstrations and query input. Demo ordering is not a directional clue.
    """
    encode = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'))
    answers = {}
    for variant in variants:
        pairs = variant['pairs']
        prompt = encode([sorted(encode(p) for p in pairs[:-1]),
                         pairs[-1]['input']])
        answer = encode(pairs[-1]['output'])
        if prompt in answers and answers[prompt] != answer:
            return False
        answers[prompt] = answer
    return True
