"""Independent contextual check for episode-shared picture completion.

Unlike the archived 269e22fb solver, this reads the picture from a supplied
demonstration OUTPUT, never from the query answer or the generator's latent
state. Implemented with string matching, independently of the constructor's
NumPy window matcher. No other family is silently switched to this verifier.
"""
from .runtime import grid

CONTEXTUAL_TASK_IDS = frozenset({'269e22fb'})


def _pictures(picture):
    a = picture
    for _ in range(4):
        yield a
        yield [row[::-1] for row in a]
        a = [list(row) for row in zip(*a)][::-1]


def solve_shared_picture(demonstrations, query):
    if not demonstrations:
        raise ValueError('A supplied demonstration is required')
    picture = grid(demonstrations[0]['output'])
    query = grid(query)
    pc = sorted({c for row in picture for c in row})
    qc = sorted({c for row in query for c in row})
    if len(pc) != 2 or len(qc) != 2:
        raise ValueError('Shared-picture completion requires two colours')
    binary = [[int(c == pc[0]) for c in row] for row in picture]
    target = [''.join(str(int(c == qc[0])) for c in row) for row in query]
    h, w = len(query), len(query[0])
    matches = []
    for a in _pictures(binary):
        H, W = len(a), len(a[0])
        if h > H or w > W:
            continue
        for reverse in (False, True):
            bits = [[1-v if reverse else v for v in row] for row in a]
            rows = [''.join(map(str, row)) for row in bits]
            for y in range(H-h+1):
                x = rows[y].find(target[0])
                while x != -1:
                    if all(rows[y+dy][x:x+w] == target[dy] for dy in range(1, h)):
                        matches.append([[qc[0] if v else qc[1] for v in row] for row in bits])
                        if len(matches) > 1:
                            raise ValueError('Fragment placement or colour interpretation is ambiguous')
                    x = rows[y].find(target[0], x+1)
    if len(matches) != 1:
        raise ValueError('Fragment has no placement in the demonstrated picture')
    return matches[0]


def verify_shared_picture_episode(episode):
    """Verify every pair using only the first demonstration as context."""
    if not episode.get('train') or not episode.get('test'):
        raise ValueError('An episode needs demonstration and query pairs')
    demos = episode['train']
    for split in ('train', 'test'):
        for pair in episode[split]:
            if solve_shared_picture(demos, pair['input']) != grid(pair['output']):
                raise ValueError('Shared-picture contextual reference disagreement')
    return True
