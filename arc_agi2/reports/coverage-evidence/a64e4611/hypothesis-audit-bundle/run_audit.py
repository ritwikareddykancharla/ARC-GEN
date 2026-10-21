import sys,json,random,hashlib,time,concurrent.futures,gzip,os
from pathlib import Path
import hypothesis_core as target
import hypothesis_evidence as independent
import hypothesis_factory as factory
import proposed_constructor as constructor
import native
D=Path(__file__).resolve().parent;PAL=list(range(10))
def transform(g,d,pal):
 g=[row[:] for row in g]
 if d>=4:g=[row[::-1] for row in g]
 for _ in range(d%4):g=[list(row) for row in zip(*g[::-1])]
 return [[pal[v] for v in row] for row in g]
def episode(pairs,d,pal):
 return {'train':[{k:transform(p[k],d,pal) for k in ['input','output']} for p in pairs[:3]],'test':[{'input':transform(pairs[3]['input'],d,pal)}],'solutions':[transform(pairs[3]['output'],d,pal)]}
def draw(seed):
 random.seed(seed);old=native.generate();random.seed(seed);p=constructor.generate();assert old['input']==p['input'];return p,old['output']!=p['output']
def checks(ep,source):
 ns={};exec(source,ns)
 for p in ep['train']:assert ns['solve'](ep['train'],p['input'])==p['output']
 assert ns['solve'](ep['train'],ep['test'][0]['input'])==ep['solutions'][0]
def one(job):
 kind,index=job;started=time.time()
 if kind=='fixture':
  t=json.loads((D/'canonical.json').read_text());pal=PAL if index<8 else [3,9,0,7,2,8,1,6,4,5];d=index%8
  ep=episode(t['train']+t['test'],d,pal);checks(ep,factory.build_program(d,pal));independent.require_corridor_evidence(ep['train'],ep['test'],pal)
  return dict(kind=kind,index=index,passed=True,seconds=time.time()-started)
 seed=864611000+index*10000;query,changed=draw(seed);draws=1;changes=int(changed);retry=[]
 for attempt in range(100):
  demos=[]
  for j in range(3):
   p,ch=draw(seed+1+3*attempt+j);draws+=1;changes+=ch;demos.append(p)
  candidates=target.fit(demos);g=target._freeze(query['input']);predictions={target._prediction(g,r,k) for r,k in candidates}
  if len(predictions)==1:break
  retry.append(dict(attempt=attempt,parameter_count=len(candidates),query_outputs=len(predictions),demos=demos))
 else:raise RuntimeError('Query context failed to disambiguate after100 attempts: '+str(index))
 c2,ys=independent.query_predictions(demos,query['input'],PAL)
 assert candidates==c2 and len(ys)==1
 ep0={'train':demos,'test':[{'input':query['input']}],'solutions':[query['output']]}
 independent.require_corridor_evidence(demos,ep0['test'],PAL)
 pal=PAL[:];random.Random(seed+9999).shuffle(pal);pairs=demos+[query]
 for d in range(8):checks(episode(pairs,d,pal),factory.build_program(d,pal))
 return dict(kind=kind,index=index,passed=True,draws=draws,synthetic_label_changes=changes,context_retries=len(retry),params=candidates,episode=ep0,retained_retry_contexts=retry,seconds=time.time()-started)
def main():
 started=time.time();out=[];jobs=[('fixture',i) for i in range(16)]+[('fresh',i) for i in range(250)];errors=[]
 with gzip.open(D/'audited-episodes.jsonl.gz','wt') as stream,concurrent.futures.ProcessPoolExecutor(max_workers=int(os.getenv('AUDIT_WORKERS','32'))) as pool:
  futures={pool.submit(one,j):j for j in jobs}
  for f in concurrent.futures.as_completed(futures):
   try:r=f.result();stream.write(json.dumps(r)+'\n');stream.flush();out.append(r)
   except Exception as exc:errors.append(dict(job=futures[f],error=repr(exc)))
   if len(out)%20==0:print('completed',len(out),'of',len(jobs),'errors',len(errors),flush=True)
 fresh=[r for r in out if r['kind']=='fresh'];fixtures=[r for r in out if r['kind']=='fixture'];unique=set()
 for r in fresh:
  for p in r['episode']['train']+r['episode']['test']:unique.add(json.dumps(p['input']))
 report=dict(task_id='a64e4611',scope='PROPOSED versioned visible-clearance convention12/3 synthetic labels; full930-parameter demo-selected target; native unchanged',passed=not errors and len(out)==266,fixture_variants_checked=len(fixtures),fresh_pairs_checked=4*len(fresh),augmented_pair_checks=32*len(fresh),independent_episode_gate_checks=len(fresh),unique_base_inputs=len(unique),sampler_draws=sum(r['draws'] for r in fresh),input_changes=0,intrinsic_rejections=0,context_retries=sum(r['context_retries'] for r in fresh),max_context_retries=max((r['context_retries'] for r in fresh),default=0),synthetic_label_changes_including_context_draws=sum(r['synthetic_label_changes'] for r in fresh),errors=errors,seconds=time.time()-started,hardware='192 CPU H200 host;32 CPU worker processes; no GPU use',source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*.py')})
 (D/'hypothesis-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
