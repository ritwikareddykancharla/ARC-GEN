"""Distinguish coloured-cell counting from distinct-colour counting in context."""


def require_strip_count_evidence(demonstrations, queries, palette):
    from .colour_evidence import MissingColourEvidence

    background = palette[0]

    def counts(grid):
        cells = [c for row in grid for c in row if c != background]
        return len(cells), len(set(cells))

    if not any(counts(q['input'])[0] != counts(q['input'])[1] for q in queries):
        return
    for demo in demonstrations:
        n, distinct = counts(demo['input'])
        width = max(len(demo['input']), len(demo['input'][0]))
        out = demo['output']
        if n > distinct and len(out) == width * n and all(len(r) == width * n for r in out):
            return
    raise MissingColourEvidence(
        'feca6190: repeated-colour query needs a demonstration distinguishing '
        'coloured-cell count from distinct-colour count')
