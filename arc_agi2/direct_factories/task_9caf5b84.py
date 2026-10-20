def build_program(d4, palette):
    fill = int(palette[7])
    src = '''import numpy as np
from collections import Counter

FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    cnt = Counter(g.flatten().tolist())
    # Rank by count, descending. The constructor guarantees that the 2nd and 3rd
    # counts differ, so the top two set is unambiguous. A tie between 1st and 2nd
    # is harmless because both are kept.
    ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    keep = [c for c, _ in ranked[:2]]
    out = g.copy()
    out[~np.isin(g, keep)] = FILL
    return out.tolist()
''' % fill
    return src
