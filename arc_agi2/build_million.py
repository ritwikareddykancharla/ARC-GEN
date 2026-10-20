# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2,<3", "pyarrow>=19,<26", "huggingface-hub>=1,<2"]
# ///
"""Two-stage adaptive episode builder. Run as python -m arc_agi2.build_million.

No language-model calls. Persist pools and reports as workers complete, then
allocate one million training episodes by query size and output-shape relation.
Shortfalls are reported explicitly, never padded with duplicate episodes.
"""
import argparse,concurrent.futures as cf,hashlib,importlib,json,math,os,random,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi,CommitOperationAdd
from .runtime import BASE,reference,solver,call,grid
from .generators.extended import GENERATORS,generate
from .audit import relation

SEED=20261021
REPO='ritwika96/arc-agi2-arcgen-1m-episodes'
OUT=Path(os.environ.get('ARCGEN_BUILD_ROOT','/tmp/arcgen-million'))
WORKERS=int(os.environ.get('ARCGEN_WORKERS','32'))
POOL_SIZE=int(os.environ.get('ARCGEN_POOL_SIZE','1200'))
FAMILY_SECONDS=int(os.environ.get('ARCGEN_FAMILY_SECONDS','900'))
TARGET=int(os.environ.get('ARCGEN_TARGET_EPISODES','1000000'))
VAL_TARGET=int(os.environ.get('ARCGEN_VALIDATION_EPISODES','20000'))

def compact(x):return json.dumps(x,separators=(',',':'),sort_keys=True)
def digest(x):return hashlib.sha256(compact(x).encode()).hexdigest()
def seed(*parts):return int(digest([SEED,*parts])[:15],16)
def dump(path,x):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(path)
def transformed(g,d4,palette):
    a=[r[:] for r in g]
    if d4>=4:a=[r[::-1] for r in a]
    for _ in range(d4%4):a=[list(r) for r in zip(*a[::-1])]
    return [[palette[c] for c in row] for row in a]
def canonical_input(g):
    # Group all palette permutations / D4 variants in the SAME data split.
    versions=[]
    for d in range(8):
        a=transformed(g,d,list(range(10)));lookup={};flat=[]
        for row in a:
            for c in row:
                if c not in lookup:lookup[c]=len(lookup)
                flat.append(lookup[c])
        versions.append(bytes([len(a),len(a[0]),*flat]))
    return hashlib.sha256(min(versions)).hexdigest()
def stratum(p):return str(max(len(p['input']),len(p['input'][0])))+'|'+relation(p)
def counts(rows,split):return dict(Counter(r['stratum'] for r in rows if r['split']==split))
def input_stats(g):
    c=Counter(v for row in g for v in row)
    return {'height':len(g),'width':len(g[0]),'colours':len(c),'dominant_fraction':max(c.values())/sum(c.values())}

def make_pool(tid):
    start=time.monotonic();rng=random.Random(seed(tid,'pool'));r=reference(tid)
    assert not r['held_out']
    report_path=OUT/'pool_reports'/f'{tid}.json';file=OUT/'pools'/f'{tid}.parquet'
    if file.exists() and report_path.exists():
        old=json.loads(report_path.read_text())
        if old.get('complete') and old.get('seed')==SEED:return old
    existing=(BASE.parent/'tasks'/f'task_{tid}.py').exists()
    native=importlib.import_module('tasks.task_'+tid).generate if existing else None
    refs=solver(tid) if tid in GENERATORS else None
    configs=json.loads((BASE/'reports/parameter-validation.json').read_text()).get(tid,{}).get('approved',[])
    if configs and refs is None:refs=solver(tid)
    rows=[];seen={};canonical=set();reject=Counter();stale=0;trials=0
    while len(rows)<POOL_SIZE and time.monotonic()-start<FAMILY_SECONDS and trials<POOL_SIZE*40:
        trials+=1;s=seed(tid,'pair',trials);random.seed(s);kw={};mode='default'
        if tid in GENERATORS and (native is None or rng.random()<.6):mode='extension'
        elif configs and rng.random()<.6:kw=rng.choice(configs)['parameters'];mode='parameter_override'
        try:
            p=call(generate,tid,s,seconds=2) if mode=='extension' else call(native,seconds=2,**kw)
            p={k:grid(p[k]) for k in ['input','output']}
            if mode!='default' and grid(call(refs,p['input'],seconds=2))!=p['output']:
                reject['reference_disagreement']+=1;continue
        except Exception as e:reject[type(e).__name__]+=1;continue
        ih,oh=digest(p['input']),digest(p['output'])
        if ih in seen:
            reject['duplicate_input' if seen[ih]==oh else 'conflicting_label']+=1;stale+=1
            if stale>=max(200,len(rows)*3):break
            continue
        stale=0;seen[ih]=oh;c=canonical_input(p['input']);canonical.add(c)
        # Split assignment depends only on input equivalence class, not family/seed/output.
        split='validation' if int(c[:8],16)%20==0 else 'train'
        rows.append(dict(task_id=tid,input=p['input'],output=p['output'],seed=s,parameters=compact(kw),
            generator_mode=mode,input_hash=ih,canonical_input_hash=c,split=split,stratum=stratum(p)))
    if not rows:return {'task_id':tid,'complete':False,'pairs':0,'reason':'no valid unique pairs','rejections':dict(reject)}
    file.parent.mkdir(parents=True,exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows),file,compression='zstd')
    assert pq.read_table(file).to_pylist()==rows
    report={'task_id':tid,'seed':SEED,'complete':True,'pairs':len(rows),'distinct_canonical_inputs':len(canonical),
       'train_strata':counts(rows,'train'),'validation_strata':counts(rows,'validation'),
       'train_canonical':len({r['canonical_input_hash'] for r in rows if r['split']=='train'}),
       'validation_canonical':len({r['canonical_input_hash'] for r in rows if r['split']=='validation'}),
       'modes':dict(Counter(r['generator_mode'] for r in rows)),'rejections':dict(reject),'seconds':time.monotonic()-start,
       'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    dump(report_path,report);return report

def allocate(reports,split,target,desired):
    # Max 2 episodes per genuinely distinct canonical input; no blind 2,000/family quota.
    capacity={r['task_id']:min(5000,2*r[split+'_canonical']) for r in reports if r[split+'_canonical']>=4}
    support={r['task_id']:r[split+'_strata'] for r in reports if r['task_id'] in capacity}
    budgets={};keys=sorted(desired);total=sum(desired.values())
    for k in keys:budgets[k]=int(target*desired[k]/total)
    for k in sorted(keys,key=lambda k:target*desired[k]/total-budgets[k],reverse=True)[:target-sum(budgets.values())]:budgets[k]+=1
    allocation={tid:Counter() for tid in capacity};used=Counter();missing={}
    # Scarce strata first. Per-stratum caps also limit reusing a small query pool.
    order=sorted(keys,key=lambda k:sum(min(capacity[t],2*support[t].get(k,0)) for t in capacity)/max(1,budgets[k]))
    for k in order:
        remaining=budgets[k]
        available={t:min(capacity[t]-used[t],2*support[t].get(k,0)) for t in capacity}
        while remaining:
            ts=[t for t,c in available.items() if c>0]
            if not ts:break
            share=max(1,remaining//len(ts))
            for t in sorted(ts,key=lambda t:(used[t],seed(t,k))):
                n=min(share,available[t],remaining);allocation[t][k]+=n;used[t]+=n;available[t]-=n;remaining-=n
                if not remaining:break
        if remaining:missing[k]=remaining
    return {t:dict(v) for t,v in allocation.items() if v},{'requested':target,'allocated':sum(used.values()),'shortfall_by_stratum':missing,'desired':budgets}

def make_episodes(arg):
    tid,allocs=arg;pool=pq.read_table(OUT/'pools'/f'{tid}.parquet').to_pylist();result={};all_hashes=set()
    for split,quota in allocs.items():
        rows=[r for r in pool if r['split']==split];bins=defaultdict(list)
        for p in rows:bins[p['stratum']].append(p)
        canonical_total=len({p['canonical_input_hash'] for p in rows})
        if len(rows)<4 or canonical_total<4:continue
        rng=random.Random(seed(tid,split,'episodes'));out=[];query_uses=Counter();pair_uses=Counter();failures=Counter()
        hist={which:{axis:Counter() for axis in ['height','width','longest','shapes']} for which in ['input','output']};relations=Counter()
        for k,n in quota.items():
            candidates=bins[k][:];rng.shuffle(candidates)
            for j in range(n):
                accepted=False
                for retry in range(50):
                    q=candidates[(j+retry)%len(candidates)]
                    if query_uses[q['input_hash']]>=4:continue
                    ds=[p for p in rows if p['input_hash']!=q['input_hash'] and pair_uses[p['input_hash']]<32]
                    if len(ds)<3:break
                    demos=rng.sample(ds,3);four=demos+[q]
                    if len({p['canonical_input_hash'] for p in four})<4:continue
                    if all(p['input']==p['output'] for p in four):continue
                    # Identical full episode hash ignores demo order and augmentation.
                    basehash=digest([sorted(p['input_hash'] for p in demos),q['input_hash']])
                    if basehash in all_hashes:continue
                    d4=rng.randrange(8) if rng.random()<.5 else 0;palette=list(range(10))
                    if d4 or rng.random()<.5:rng.shuffle(palette)
                    transformed_pairs=[{z:transformed(p[z],d4,palette) for z in ['input','output']} for p in four]
                    train=transformed_pairs[:3];query=transformed_pairs[-1]
                    challenge={'train':train,'test':[{'input':query['input']}]}
                    prompt='Infer the shared transformation from the demonstrations. Return only JSON with key outputs and one grid per test input.\n'+compact(challenge)
                    row={'episode_id':f'arcgen-1m-{tid}-{split}-{len(out):05d}','task_id':tid,'split':split,
                      'variant':'native' if d4==0 and palette==list(range(10)) else 'augmented',
                      'train':train,'test':challenge['test'],'solutions':[query['output']],
                      'prompt':prompt,'completion':compact({'outputs':[query['output']]}),
                      'pair_seeds':[p['seed'] for p in four],'pair_parameters':[p['parameters'] for p in four],
                      'pair_generator_modes':[p['generator_mode'] for p in four],
                      'base_input_hashes':[p['input_hash'] for p in four],
                      'canonical_input_hashes':[p['canonical_input_hash'] for p in four],
                      'base_episode_sha256':basehash,'d4_transform':d4,'color_permutation':palette,
                      'query_input_height':len(query['input']),'query_input_width':len(query['input'][0]),
                      'query_output_height':len(query['output']),'query_output_width':len(query['output'][0]),
                      'query_relation':relation(query),'source_commit':os.environ.get('ARCGEN_SOURCE_COMMIT','local')}
                    assert json.loads(row['completion'])=={'outputs':row['solutions']}
                    out.append(row);all_hashes.add(basehash);query_uses[q['input_hash']]+=1
                    for p in four:pair_uses[p['input_hash']]+=1
                    for which in hist:
                        a=query[which];h,w=len(a),len(a[0]);hist[which]['height'][h]+=1;hist[which]['width'][w]+=1;hist[which]['longest'][max(h,w)]+=1;hist[which]['shapes'][f'{h}x{w}']+=1
                    relations[relation(query)]+=1;accepted=True;break
                if not accepted:failures['episode_constraints_exhausted']+=1
        path=OUT/'data'/split/f'{tid}.parquet';path.parent.mkdir(parents=True,exist_ok=True)
        if out:
            pq.write_table(pa.Table.from_pylist(out),path,compression='zstd')
            assert pq.read_metadata(path).num_rows==len(out)
        result[split]={'episodes':len(out),'requested':sum(quota.values()),'query_histograms':hist,
            'relations':dict(relations),'failures':dict(failures),'max_query_reuse':max(query_uses.values(),default=0),
            'max_pair_reuse':max(pair_uses.values(),default=0),'distinct_inputs_used':len(pair_uses)}
    report={'task_id':tid,'splits':result};dump(OUT/'episode_reports'/f'{tid}.json',report);return report

def card(m):
    n=m.get('train_episodes',0);v=m.get('validation_episodes',0)
    return f'''---
license: apache-2.0
task_categories:
- text-generation
language:
- en
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train/*.parquet
  - split: validation
    path: data/validation/*.parquet
---
# ARC-AGI-2 · Adaptive one-million-episode target

**Status: {m['status']} · {n:,} training episodes · {v:,} validation episodes published.**

Three demonstration pairs and one query per episode, with generator-produced output targets. No reasoning or Python code in the SFT targets. This is a one-million target, not a claim that one million valid episodes already exist.

[Visual size and coverage audit](https://ritwika96-arc-episode-gallery.static.hf.space/coverage/index.html) · [Generator fork](https://github.com/ritwikareddykancharla/ARC-GEN/tree/arc2-diversity-and-reference-generators/arc_agi2) · [Original 100K baseline](https://huggingface.co/datasets/ritwika96/arc-agi2-arcgen-100k-episodes)

## What changes

- All fixture-verified ARC-GEN generators whose task IDs occur in ARC-AGI-2, plus independently constructed, tested extensions.
- Adaptive quotas: at most two episodes per unique canonical input in the pair pool, with a 5,000-episode family ceiling. Families with little variation receive fewer examples.
- Target query longest-side distribution at each integer size 1–30 jointly with output expansion/shrinkage/same-shape, measured on all 1,120 public tasks. Exact height, width and rectangular-shape histograms are reported separately. Unsupported targets become explicit shortfalls; difficulty is not proven equal by dimensions.
- Size overrides require original replay and differential seed checks. Every overridden/extended pair is checked against its saved teacher solver. Default upstream generators have fixture checks, not full semantic proofs.
- Fresh input pool, no duplicated full native episodes, no identical inputs inside an episode. Palette and D4 changes are shared across each episode and stored.
- Input equivalence classes under palette renaming and D4 are assigned to one split before episode construction, including across families. Existing 20 held-out task families are excluded entirely. Validation is within-generator generalization; the original held-out tasks measure unseen families.

## Audit and reproducibility

[Manifest](manifest.json), [pool reports](pool_reports), [episode reports](episode_reports), [allocation targets](allocation.json). Master seed {SEED}. Published partial shards are complete episodes; failed families and shortfalls remain visible. No model training or LLM calls occur in this job.

The reference packets include saved Opus/Fable solutions; they guide input construction and validation but are not exposed in episode prompts. Public evaluation tasks used in generation are training data for subsequent models, not independent evaluation. The held-out list is in the manifest.

ARC-GEN upstream code is Copyright Google LLC, Apache-2.0. This is an independent derivative. Original benchmark grids remain unchanged.
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--local',action='store_true');ap.add_argument('--tasks',nargs='*');args=ap.parse_args()
    for d in ['pools','pool_reports','episode_reports','data/train','data/validation']: (OUT/d).mkdir(parents=True,exist_ok=True)
    inv=json.loads((BASE/'reports/inventory.json').read_text());pv=json.loads((BASE/'reports/parameter-validation.json').read_text())
    eligible=[r['task_id'] for r in inv['tasks'] if not r['held_out'] and r['status'] in ['upstream_fixture_verified','extension_validated']]
    if args.tasks:
        assert set(args.tasks)<=set(eligible);eligible=args.tasks
    api=None if args.local else HfApi()
    if api:assert api.whoami()['name']=='ritwika96'
    m={'status':'generating_pair_pools','target_train_episodes':TARGET,'target_validation_episodes':VAL_TARGET,
       'source_commit':os.environ.get('ARCGEN_SOURCE_COMMIT','local'),'seed':SEED,'workers':WORKERS,
       'task_ids':eligible,'excluded_holdout_ids':inv['summary']['holdouts'],'holdout_overlap':[],
       'completed_pools':0,'train_episodes':0,'validation_episodes':0,'errors':[],'model_training_launched':False}
    assert not set(eligible)&set(m['excluded_holdout_ids'])
    def publish(files=()):
        dump(OUT/'manifest.json',m);(OUT/'README.md').write_text(card(m))
        if api:
            ops=[CommitOperationAdd(path_in_repo=f,path_or_fileobj=str(OUT/f)) for f in ['manifest.json','README.md',*files] if (OUT/f).exists()]
            for retry in range(5):
                try:api.create_commit(REPO,repo_type='dataset',operations=ops,commit_message=f"{m['status']}: {m['train_episodes']:,} training episodes");break
                except Exception:
                    if retry==4:raise
                    time.sleep(2**retry)
    publish();reports=[];last=time.monotonic();files=[]
    with cf.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futures={pool.submit(make_pool,t):t for t in eligible}
        for f in cf.as_completed(futures):
            tid=futures[f]
            try:
                r=f.result()
                if r.get('complete'):reports.append(r);files.extend([f'pools/{tid}.parquet',f'pool_reports/{tid}.json'])
                else:m['errors'].append(r)
            except Exception as e:m['errors'].append({'task_id':tid,'error':repr(e)})
            m['completed_pools']=len(reports)
            print(compact({'stage':'pool','task_id':tid,'completed':len(reports),'pairs':sum(r['pairs'] for r in reports)}),flush=True)
            if len(files)>=32 or time.monotonic()-last>60:publish(files);files=[];last=time.monotonic()
    publish(files)
    desired=Counter()
    for r in inv['tasks']:
        for p in r['canonical']['test']:desired[stratum(p)]+=1
    alloc_train,stats_train=allocate(reports,'train',TARGET,desired)
    alloc_val,stats_val=allocate(reports,'validation',VAL_TARGET,desired)
    dump(OUT/'allocation.json',{'train':stats_train,'validation':stats_val,'train_by_family':alloc_train,'validation_by_family':alloc_val,
        'target_scope':'All 1,120 public canonical tasks, query-input longest side jointly with output-shape relation.'})
    m['status']='constructing_episodes';publish(['allocation.json']);files=[];last=time.monotonic()
    combined={tid:{s:a[tid] for s,a in [('train',alloc_train),('validation',alloc_val)] if tid in a} for tid in sorted(set(alloc_train)|set(alloc_val))}
    episode_reports=[]
    with cf.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futures={pool.submit(make_episodes,item):item[0] for item in combined.items()}
        for f in cf.as_completed(futures):
            tid=futures[f]
            try:
                r=f.result();episode_reports.append(r);files.append(f'episode_reports/{tid}.json')
                for split,x in r['splits'].items():
                    m[split+'_episodes']+=x['episodes']
                    if x['episodes']:files.append(f'data/{split}/{tid}.parquet')
            except Exception as e:m['errors'].append({'task_id':tid,'stage':'episodes','error':repr(e)})
            print(compact({'stage':'episodes','task_id':tid,'train':m['train_episodes'],'validation':m['validation_episodes']}),flush=True)
            if len(files)>=24 or time.monotonic()-last>60:publish(files);files=[];last=time.monotonic()
    # Aggregate every size, input/output shape and relation for downstream histogram UI.
    audit={}
    for split in ['train','validation']:
        hist={g:{axis:Counter() for axis in ['height','width','longest','shapes']} for g in ['input','output']};rel=Counter()
        for r in episode_reports:
            if split not in r['splits']:continue
            x=r['splits'][split];rel.update(x['relations'])
            for g in hist:
                for axis in hist[g]:hist[g][axis].update(x['query_histograms'][g][axis])
        audit[split]={'pairs':m[split+'_episodes'],'input':hist['input'],'output':hist['output'],'relations':dict(rel)}
    dump(OUT/'size-audit.json',audit);files.append('size-audit.json')
    m.update(status='complete' if m['train_episodes']==TARGET and not m['errors'] else 'complete_with_shortfall',
       train_shortfall=TARGET-m['train_episodes'],validation_shortfall=VAL_TARGET-m['validation_episodes'],
       represented_train_families=sum(r['splits'].get('train',{}).get('episodes',0)>0 for r in episode_reports))
    publish(files);print(compact(m),flush=True)
if __name__=='__main__':main()
