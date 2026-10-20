"""Demonstrations teach a spiral's initial heading and turn sense."""
from itertools import product

from .colour_evidence import MissingColourEvidence,_require_rule_agreement

DIRECTIONS = ((-1,0),(0,1),(1,0),(0,-1))


def spiral_variants(g,palette):
    h,w=len(g),len(g[0])
    starts=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==palette[3]]
    if len(starts)!=1:
        raise MissingColourEvidence('e5c44e8f: expected exactly one spiral seed')
    variants=[]
    for heading,turn in product(range(4),(1,-1)):
        out=[row[:] for row in g]
        r,c=starts[0]
        blocked=False
        # Two segments at each even length. After h+w+1 segment pairs all later
        # segment lines are outside the finite canvas; the walk can leave and
        # re-enter earlier, so do not stop at the first out-of-bounds step.
        for span in range(1,h+w+2):
            for _ in range(2):
                dr,dc=DIRECTIONS[heading]
                for _ in range(2*span):
                    r,c=r+dr,c+dc
                    if 0<=r<h and 0<=c<w:
                        if g[r][c]==palette[2]:
                            blocked=True
                            break
                        out[r][c]=palette[3]
                if blocked:break
                heading=(heading+turn)%4
            if blocked:break
        variants.append(out)
    return variants


def require_spiral_evidence(demonstrations,queries,palette):
    _require_rule_agreement('e5c44e8f',demonstrations,queries,
                            lambda g:spiral_variants(g,palette))
