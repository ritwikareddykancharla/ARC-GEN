"""Execute every admitted task's declared fixture under D4 and two palettes."""
import concurrent.futures as cf,hashlib,json,sys,time
from pathlib import Path
FORK=Path(__file__).resolve().parents[3];sys.path.insert(0,str(FORK))
from arc_agi2.program_targets import compile_target,audit_target,verify
from arc_agi2.runtime import reference
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.augmentation import transformed
BASE=Path(__file__).resolve().parent
def one(tid):
 start=time.monotonic();basis=fixture_basis(tid);task=reference(tid)[basis['fixture']];count=0;hashes=[]
 try:
  for pal in [list(range(10)),[3,9,0,7,2,8,1,6,4,5]]:
   for d4 in range(8):
    source,_=compile_target(tid,d4,pal);audit_target(tid,source)
    ep={'train':[{k:transformed(p[k],d4,pal) for k in ['input','output']} for p in task['train']], 'test':[{'input':transformed(p['input'],d4,pal)} for p in task['test']], 'solutions':[transformed(p['output'],d4,pal) for p in task['test']]}
    assert verify(source,ep)['all_exact'];count+=1;hashes.append(hashlib.sha256(source.encode()).hexdigest())
  return dict(task_id=tid,passed=True,variants=count,fixture_basis=basis,program_hashes=hashes,seconds=time.monotonic()-start)
 except Exception as exc:return dict(task_id=tid,passed=False,variants=count,error=repr(exc),fixture_basis=basis,seconds=time.monotonic()-start)
def main():
 start=time.monotonic();d=json.loads((BASE/'current-summary.json').read_text());ids=sorted(set(d['ready']+d['missing']));results=[]
 with cf.ProcessPoolExecutor(max_workers=8) as pool:
  futures={pool.submit(one,t):t for t in ids}
  for f in cf.as_completed(futures):
   try:results.append(f.result())
   except Exception as exc:results.append(dict(task_id=futures[f],passed=False,error=repr(exc)))
   if len(results)%100==0:print(json.dumps(dict(completed=len(results),failed=sum(not r['passed'] for r in results))),flush=True)
 report=dict(scope='All1120 declared fixtures, original or hash-pinned teaching context, each D4 and two palettes. Does not establish native-generator equivalence or unrestricted synthetic correctness.',tasks=len(ids),passed_tasks=sum(r['passed'] for r in results),variants=sum(r.get('variants',0) for r in results),seconds=time.monotonic()-start,results=sorted(results,key=lambda r:r['task_id']))
 out=BASE/'final-coverage-replay.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));raise SystemExit(0 if report['passed_tasks']==len(ids) else 1)
if __name__=='__main__':main()
