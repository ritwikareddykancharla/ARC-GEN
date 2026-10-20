"""Independently replay border-started beams under demonstrated endpoint rules."""
from .colour_evidence import MissingColourEvidence

RULES=('side','either','target','target_axis')


def beam_predictions(grid,palette):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):raise ValueError('Invalid grid')
    H,W=len(grid),len(grid[0]);beam,mirror,glass=palette[1:4]
    board={(r,c):v for r,row in enumerate(grid) for c,v in enumerate(row)}
    walls={p for p,v in board.items() if v in (mirror,glass)}
    horizontal=any((r,c+1) in walls for r,c in walls)
    vertical=any((r+1,c) in walls for r,c in walls)
    if horizontal==vertical:raise ValueError('Ambiguous wall axis')
    axis=1 if horizontal else 0
    prefix=sorted((p for p,v in board.items() if v==beam),key=lambda p:p[axis])
    if len(prefix)<3:raise ValueError('At least three visible beam cells required')
    if any(abs(p[0]-q[0])!=1 or abs(p[1]-q[1])!=1 for p,q in zip(prefix,prefix[1:])):raise ValueError('Beam is not monotone diagonal chain')
    def behind(seq):return (2*seq[0][0]-seq[1][0],2*seq[0][1]-seq[1][1]) not in board
    forward,reverse=behind(prefix),behind(prefix[::-1])
    if forward==reverse:raise ValueError('No unique border tail')
    if reverse:prefix.reverse()
    start=prefix[0];initial=(prefix[1][0]-start[0],prefix[1][1]-start[1])
    predictions=[]
    for rule in RULES:
        p=start;dr,dc=initial;path=[p];seen={(p,dr,dc)}
        for _ in range(4*H*W+16):
            r,c=p;next_position=None
            if rule in ('side','either'):
                side=(r+dr,c) if horizontal else (r,c+dc)
                if side not in board:break
                contact=board.get(side)==mirror
                if rule=='either':contact|=board.get((r+dr,c+dc))==mirror
                if contact:
                    if horizontal:dr=-dr
                    else:dc=-dc
                next_position=(r+dr,c+dc)
                if next_position not in board:break
            else:
                for reflection in range(4):
                    target=(r+dr,c+dc)
                    if target not in board:break
                    if board[target]!=mirror:next_position=target;break
                    if rule=='target_axis':
                        if horizontal:dr=-dr
                        else:dc=-dc
                    elif board.get((r+dr,c))==mirror:dr=-dr
                    elif board.get((r,c+dc))==mirror:dc=-dc
                    else:dr,dc=-dr,-dc
                if next_position is None:break
            state=(next_position,dr,dc)
            if state in seen:break
            seen.add(state);path.append(next_position);p=next_position
        if path[:len(prefix)]!=prefix:predictions.append(None);continue
        painted=set(path)
        predictions.append(tuple(tuple(beam if (r,c) in painted else board[r,c] for c in range(W)) for r in range(H)))
    return predictions


def surviving_endpoint_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('7e2bad24: demonstrations required')
    alive=set(range(len(RULES)))
    for pair in demonstrations:
        try:predictions=beam_predictions(pair['input'],palette)
        except ValueError as exc:raise MissingColourEvidence('7e2bad24: invalid demonstrated beam') from exc
        target=tuple(tuple(row) for row in pair['output'])
        alive &= {i for i,p in enumerate(predictions) if p==target}
    if not alive:raise MissingColourEvidence('7e2bad24: no demonstrated endpoint rule')
    return alive


def require_endpoint_evidence(demonstrations,queries,palette):
    alive=surviving_endpoint_rules(demonstrations,palette)
    for query in queries:
        try:predictions=beam_predictions(query['input'],palette)
        except ValueError as exc:raise MissingColourEvidence('7e2bad24: invalid query beam') from exc
        # A visible prefix bend is additional input evidence and can eliminate a rule.
        answers={predictions[i] for i in alive if predictions[i] is not None}
        if len(answers)!=1:raise MissingColourEvidence('7e2bad24: unresolved mirror-end convention')
