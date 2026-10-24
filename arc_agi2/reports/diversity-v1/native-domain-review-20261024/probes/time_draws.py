"""Batch-2 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: time_draws.py TASK_ID N SECONDS_PER_DRAW [SEED]. Times native generate() draws with a per-draw alarm (used for 54db823b).
"""
import sys, time, signal, importlib, random
sys.path.insert(0,'.')
tid=sys.argv[1]; n=int(sys.argv[2]); lim=float(sys.argv[3])
m=importlib.import_module(f'tasks.task_{tid}')
class TO(Exception): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM,h)
ok=to=err=0; ts=[]; shapes=set()
random.seed(int(sys.argv[4]) if len(sys.argv)>4 else 0)
for i in range(n):
    t=time.time(); signal.setitimer(signal.ITIMER_REAL,lim)
    try:
        g=m.generate(); ok+=1; ts.append(time.time()-t); shapes.add((len(g['input']),len(g['input'][0])))
    except TO: to+=1
    except Exception as e: err+=1; print('ERR',type(e).__name__,e)
    finally: signal.setitimer(signal.ITIMER_REAL,0)
print(tid,'ok',ok,'timeout',to,'err',err,'median_s',sorted(ts)[len(ts)//2] if ts else None,'max_s',max(ts) if ts else None,'shapes',sorted(shapes))
