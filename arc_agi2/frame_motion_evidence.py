"""Identify demonstrated signed motion versus dot-majority motion.

The gate compares complete rendered predictions. Query outputs are never read.
Axis signs are hypotheses fitted to demonstrations, never D4 metadata defaults.
"""
import itertools
import numpy as np
from .colour_evidence import MissingColourEvidence

RULES=tuple(itertools.product((0,1),(-1,1),(-1,1)))


def motion_prediction(grid,palette,rule):
    a=np.asarray(grid,dtype=int)
    if a.ndim!=2 or not a.size:raise ValueError('Invalid grid')
    mask=a==palette[2];dots=np.argwhere(a==palette[3]);frame=np.argwhere(mask)
    if not len(frame) or len(dots)<2:raise ValueError('Missing frame or dots')
    lo,hi=frame.min(axis=0),frame.max(axis=0)
    if not np.array_equal(hi-lo,[2,2]):raise ValueError('Invalid frame bounds')
    center=lo+1;expected=np.zeros_like(mask);expected[lo[0]:hi[0]+1,lo[1]:hi[1]+1]=True;expected[tuple(center)]=False
    if not np.array_equal(mask,expected):raise ValueError('Invalid frame mask')
    if np.all(dots[:,0]==center[0]):axis=1
    elif np.all(dots[:,1]==center[1]):axis=0
    else:raise ValueError('Invalid dot axis')
    positions=np.sort(dots[:,axis]);origin=center[axis]
    if origin not in positions or not np.all(np.diff(positions)==2):raise ValueError('Invalid dot spacing')
    if not np.isin(a,[palette[0],palette[2],palette[3]]).all():raise ValueError('Unknown colour')
    majority=int(np.sign(np.count_nonzero(positions>origin)-np.count_nonzero(positions<origin)))
    mode,v,h=rule;sign=majority if mode and majority else (v,h)[axis]
    translated=frame.copy();translated[:,axis]+=2*sign
    if np.any(translated<0) or np.any(translated[:,0]>=a.shape[0]) or np.any(translated[:,1]>=a.shape[1]):raise ValueError('Out of bounds')
    out=a.copy();out[mask]=palette[0];out[translated[:,0],translated[:,1]]=palette[2]
    return out.tolist()


def surviving_motion_rules(demonstrations,palette):
    if not demonstrations:raise MissingColourEvidence('5168d44c: demonstrations required')
    observed={}
    for p in demonstrations:
        try:
            a,b=np.asarray(p['input']),np.asarray(p['output'])
            if a.shape!=b.shape:raise ValueError('Shape changed')
            fa,fb=np.argwhere(a==palette[2]),np.argwhere(b==palette[2])
            delta=fb.min(axis=0)-fa.min(axis=0)
            axes=np.flatnonzero(delta)
            if len(axes)!=1 or abs(int(delta[axes[0]]))!=2:raise ValueError('Invalid displacement')
            axis=int(axes[0]);sign=int(delta[axis])//2
            if axis in observed and observed[axis]!=sign:raise ValueError('Conflicting default directions')
            observed[axis]=sign
        except (ValueError,IndexError,TypeError) as e:raise MissingColourEvidence('5168d44c: invalid demonstrated motion') from e
    alive=[]
    for rule in RULES:
        if any(rule[1+a]!=s for a,s in observed.items()):continue
        try:
            if all(motion_prediction(p['input'],palette,rule)==p['output'] for p in demonstrations):alive.append(rule)
        except (ValueError,IndexError,TypeError):pass
    if not alive:raise MissingColourEvidence('5168d44c: no demonstrated motion rule')
    return alive


def require_frame_motion_evidence(demonstrations,queries,palette):
    alive=surviving_motion_rules(demonstrations,palette)
    for q in queries:
        try:predictions=[motion_prediction(q['input'],palette,r) for r in alive]
        except (ValueError,IndexError,TypeError) as e:raise MissingColourEvidence('5168d44c: unresolved boundary direction') from e
        if any(p!=predictions[0] for p in predictions[1:]):raise MissingColourEvidence('5168d44c: unresolved motion direction')
