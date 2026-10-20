"""Reversible, episode-wide geometry and optional simultaneous colour mapping.

An episode transformation T produces the conjugated rule T f T^-1. It need
not preserve the native rule (e.g. move-left becomes move-up after rotation).
Validate in native coordinates; never reject using f(T(x)) != T(f(x)).
"""
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
