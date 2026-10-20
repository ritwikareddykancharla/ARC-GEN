"""Check which central colour and mirror axis are taught by demonstrations.

The unchanged c35c1b4c constructor grows a foreground blob from (4,4),
then completes its left/right mirror. Noise excludes the foreground colour.
Foreground need not be the most frequent colour. We deliberately do not
supply the constructor's anchor or axis to a visible episode: retain every
central-anchor/axis hypothesis matching the demonstrations and require their
query predictions to agree. This is an eight-rule evidence check, not a claim
of identifiability over all possible ARC rules.
"""
import numpy as np
from .colour_evidence import MissingColourEvidence, _require_rule_agreement


def central_mirror_variants(grid):
    g = np.asarray(grid)
    if g.ndim != 2 or min(g.shape) < 2 or any(n % 2 for n in g.shape):
        raise MissingColourEvidence('c35c1b4c: expected even rectangular grid')
    h,w = g.shape
    variants = []
    for r in (h//2-1,h//2):
        for c in (w//2-1,w//2):
            colour = g[r,c]
            mask = g == colour
            for axis in (0,1):
                out = g.copy()
                out[np.flip(mask,axis=axis)] = colour
                variants.append(out.tolist())
    return variants


def require_central_mirror_evidence(demonstrations,queries):
    _require_rule_agreement('c35c1b4c',demonstrations,queries,central_mirror_variants)
