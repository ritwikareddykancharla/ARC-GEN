"""Infer a common zigzag frame from demonstrations and query pixels."""
from .colour_evidence import MissingColourEvidence


def frame_predictions(g,palette):
    h,w=len(g),len(g[0]);bg,line,fill=(palette[i] for i in (0,2,4))
    predictions=[]
    for long_axis in (0,1):
        length,cross=(h,w) if long_axis==0 else (w,h)
        for long_sign in (1,-1):
            for cross_sign in (1,-1):
                if cross!=3:
                    predictions.append(None);continue
                def position(t,s):
                    t=t if long_sign>0 else length-1-t
                    s=s if cross_sign>0 else 2-s
                    return (t,s) if long_axis==0 else (s,t)
                original=[[bg]*w for _ in range(h)]
                for t in range(length):
                    r,c=position(t,(0,1,2,1)[t%4]);original[r][c]=line
                if original!=g:
                    predictions.append(None);continue
                out=[row[:] for row in g]
                for k,t in enumerate(range(0,length+1,6)):
                    side=2 if k%2==0 else 0
                    for a,b in [(t-1,side),(t,side),(t+1,side),(t,1)]:
                        if 0<=a<length:
                            r,c=position(a,b)
                            if out[r][c]==bg:out[r][c]=fill
                predictions.append(out)
    return predictions


def require_zigzag_evidence(demonstrations,queries,palette):
    alive=set(range(8))
    for demo in demonstrations:
        alive&={i for i,v in enumerate(frame_predictions(demo['input'],palette)) if v==demo['output']}
    options=[frame_predictions(q['input'],palette) for q in queries]
    alive={i for i in alive if all(v[i] is not None for v in options)}
    if not alive:raise MissingColourEvidence('7447852a: no common visible zigzag frame')
    for variants in options:
        if len({tuple(map(tuple,variants[i])) for i in alive})!=1:
            raise MissingColourEvidence('7447852a: demonstrations leave pocket phase ambiguous')
