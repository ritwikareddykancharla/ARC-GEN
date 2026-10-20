"""Compare axis orientation and equal-score tie conventions from pixels."""
from collections import Counter
from .colour_evidence import MissingColourEvidence, _require_rule_agreement


def symmetry_variants(g):
    counts = Counter(v for row in g for v in row)
    common = counts.most_common()
    if len(common) > 1 and common[0][1] == common[1][1]:
        raise MissingColourEvidence('8e5c0c38: background is not uniquely most frequent')
    bg = common[0][0]
    groups = []
    for ink in counts:
        if ink == bg: continue
        cells = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == ink}
        options = []
        for coordinate in (0,1):
            values = [p[coordinate] for p in cells]
            candidates = []
            for axis in range(2*min(values),2*max(values)+1):
                def mirror(p):
                    return (axis-p[0],p[1]) if coordinate == 0 else (p[0],axis-p[1])
                candidates.append({p for p in cells if mirror(p) in cells})
            best = max(map(len,candidates))
            winners = [kept for kept in candidates if len(kept) == best]
            options.append((winners[0],winners[-1]))
        groups.append((cells,options))
    outputs = []
    # Rows only, columns only, or best orientation with either orientation
    # preferred on an equal score. Each axis has an independent low/high tie.
    # The hypothesis set is closed under all rotations/reflections.
    for policy in range(4):
        for row_tie in range(2):
            for col_tie in range(2):
                out = [row[:] for row in g]
                for cells,options in groups:
                    row_keep,col_keep = options[0][row_tie],options[1][col_tie]
                    if policy < 2:
                        keep = (row_keep,col_keep)[policy]
                    elif len(row_keep) == len(col_keep):
                        keep = (row_keep,col_keep)[policy-2]
                    else:
                        keep = max((row_keep,col_keep),key=len)
                    for r,c in cells-keep: out[r][c] = bg
                outputs.append(out)
    return outputs


def require_symmetry_selection_evidence(demonstrations,queries):
    _require_rule_agreement('8e5c0c38',demonstrations,queries,symmetry_variants)
