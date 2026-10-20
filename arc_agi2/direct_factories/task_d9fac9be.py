TEMPLATE = '''import numpy as np

BG = __BG__


def _answer(grid):
    g = np.asarray(grid, dtype=int)
    if g.ndim != 2 or min(g.shape) < 3:
        raise ValueError('Expected grid with a framed cell')
    centre = g[1:-1, 1:-1]
    ring = g[:-2, :-2]
    valid = (centre != BG) & (ring != BG) & (centre != ring)
    for dr, dc in ((0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)):
        valid &= g[dr:dr+centre.shape[0], dc:dc+centre.shape[1]] == ring
    answers = np.unique(centre[valid])
    if len(answers) != 1:
        raise ValueError('No unique framed-centre colour')
    return [[int(answers[0])]]


def solve(demonstrations, grid):
    if not demonstrations:
        raise ValueError('Demonstrations required')
    for demo in demonstrations:
        if _answer(demo['input']) != demo['output']:
            raise ValueError('Demonstrations disagree with framed-centre extraction')
    return _answer(grid)
'''


def build_program(d4, palette):
    return TEMPLATE.replace('__BG__', str(int(palette[0])))
