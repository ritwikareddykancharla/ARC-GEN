TEMPLATE = '''
def _variants(grid):
    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    if h < 2 or w < 2 or h % 2 or w % 2 or any(len(row) != w for row in g):
        raise ValueError('Expected an even rectangular grid with a central four-cell block')
    variants = []
    for r0 in (h//2-1, h//2):
        for c0 in (w//2-1, w//2):
            colour = g[r0][c0]
            for axis in (0, 1):
                out = [row[:] for row in g]
                for r in range(h):
                    for c in range(w):
                        if g[r][c] == colour:
                            rr, cc = (h-1-r, c) if axis == 0 else (r, w-1-c)
                            out[rr][cc] = colour
                variants.append(out)
    return variants


def solve(demonstrations, grid):
    if not demonstrations:
        raise ValueError('Demonstrations are required to identify the central colour and mirror axis')
    surviving = set(range(8))
    for pair in demonstrations:
        predictions = _variants(pair['input'])
        surviving &= {i for i, out in enumerate(predictions) if out == pair['output']}
    if not surviving:
        raise ValueError('No central-colour mirror rule matches every demonstration')
    predictions = _variants(grid)
    outputs = [predictions[i] for i in sorted(surviving)]
    if any(out != outputs[0] for out in outputs[1:]):
        raise ValueError('Demonstrations do not resolve the query mirror rule')
    return outputs[0]
'''


def build_program(d4, palette):
    # Axis and central-cell role are learned from visible demonstration pairs.
    # No hidden native anchor, palette role or inverse transform is embedded.
    return TEMPLATE
