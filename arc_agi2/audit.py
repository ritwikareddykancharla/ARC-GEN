"""Reproducible corpus inventory, exact size histograms, and bounded generator tests."""
import argparse,concurrent.futures as cf,csv,hashlib,importlib,json,random,sys,time
from collections import Counter
from pathlib import Path
from .runtime import BASE,reference,solver,check_reference,call,grid,pairs
from .generators.registry import GENERATORS,generate
from .fixture_policy import fixture_basis
ROOT=BASE.parent
UPSTREAM_IDS=set(json.loads((BASE/'upstream_task_ids.json').read_text()))

def key(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def fixture_check(tid):
    try:
        mod=importlib.import_module('tasks.task_'+tid)
        got=call(mod.validate,seconds=10);r=reference(tid)
        a={key(p) for p in pairs(got)};b={key(p) for p in pairs(r['canonical'])}
        return {'task_id':tid,'matches_pair_set':a==b,'canonical_pairs_missing':len(b-a),'extra_pairs':len(a-b)}
    except Exception as e:return {'task_id':tid,'matches_pair_set':False,'error':repr(e)}
def extension_check(tid):
    f=solver(tid);shapes=Counter();errors=[];n=300
    standalone=(ROOT/'tasks'/f'task_{tid}.py').exists() and tid not in UPSTREAM_IDS
    constructor=importlib.import_module('tasks.task_'+tid).generate if standalone else None
    for seed in range(n):
        try:
            random.seed(seed)
            p=call(constructor,seconds=3) if standalone else generate(tid,seed)
            grid(p['input']);grid(p['output'])
            assert grid(call(f,p['input']))==p['output'],'reference mismatch'
            shapes[f"{len(p['input'])}x{len(p['input'][0])}->{len(p['output'])}x{len(p['output'][0])}"]+=1
        except Exception as e:errors.append({'seed':seed,'error':str(e)})
    orig=check_reference(tid);basis=fixture_basis(tid)
    return {'task_id':tid,'sampled':n,'passed':n-len(errors),'errors':errors,'shapes':dict(shapes),'original_replay':orig,
        'ready':not errors and orig[basis['fixture']]['all_exact'], 'fixture_basis':basis,
        'scope':'Independent constructor vs saved solver and original fixtures; agreement does not prove semantic completeness.'}

def summarise(ps):
    out={'pairs':len(ps),'input':{},'output':{},'relations':dict(Counter(relation(p) for p in ps))}
    for which in ['input','output']:
        shapes=Counter((len(p[which]),len(p[which][0])) for p in ps)
        out[which]={'height':{str(i):sum(n for (h,w),n in shapes.items() if h==i) for i in range(1,31)},
                    'width':{str(i):sum(n for (h,w),n in shapes.items() if w==i) for i in range(1,31)},
                    'longest':{str(i):sum(n for (h,w),n in shapes.items() if max(h,w)==i) for i in range(1,31)},
                    'shapes':{f'{h}x{w}':n for (h,w),n in sorted(shapes.items())},
                    'cells':dict(Counter(len(p[which])*len(p[which][0]) for p in ps))}
    return out

def relation(p):
    a,b=p['input'],p['output'];sa=(len(a),len(a[0]));sb=(len(b),len(b[0]))
    if sa==sb:return 'same_shape'
    return 'expand' if sb[0]*sb[1]>sa[0]*sa[1] else 'shrink' if sb[0]*sb[1]<sa[0]*sa[1] else 'reshape'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);ap.add_argument('--generated-dir');args=ap.parse_args()
    report=BASE/'reports';report.mkdir(exist_ok=True)
    index=json.loads((BASE/'reference_index.json').read_text());rs=[reference(r['task_id']) for r in index['tasks']]
    source_ids={p.stem[5:] for p in (ROOT/'tasks').glob('task_*.py')}
    present=sorted(source_ids & {r['task_id'] for r in rs})
    extensions=sorted(set(GENERATORS)|(set(present)-UPSTREAM_IDS))
    with cf.ProcessPoolExecutor(max_workers=args.workers) as pool:
        fixtures=list(pool.map(fixture_check,present));exts=list(pool.map(extension_check,extensions))
    fj={r['task_id']:r for r in fixtures};ej={r['task_id']:r for r in exts}
    registry=[];taxonomy={}
    for r in rs:
        tid=r['task_id'];native=tid in UPSTREAM_IDS;ready=ej.get(tid,{}).get('ready',False)
        review_path=report/'standalone'/f'{tid}.json'
        review=json.loads(review_path.read_text()) if review_path.exists() else None
        status='upstream_fixture_verified' if native and fj.get(tid,{}).get('matches_pair_set') else 'upstream_fixture_mismatch' if native else 'extension_validated' if ready else 'generator_missing'
        record={'task_id':tid,'split':r['split'],'held_out':r['held_out'],'training_eligible':True,'status':status,'upstream':native,'extension':tid in extensions,
                'standalone_module':f'tasks/task_{tid}.py' if tid in source_ids else None,
                'standalone_review':{k:review.get(k) for k in ['scope','known_limitations','semantic_review','stress_test']} if review else None,
                'candidate_tactics':list(r['candidate_tactics']),'explanation':r['explanation'],
                'fixture':fj.get(tid),'extension_validation':ej.get(tid),'teaching_variant':r['teaching_variant'],
                'canonical':r['canonical'],'teacher_models':r['teacher_models'],
                'fixture_basis':fixture_basis(tid),
                'approved_teaching_fixture':r['teaching_fixture'] if fixture_basis(tid)['corrected'] else None}
        registry.append(record)
    for tag,meta in index['taxonomy'].items():
        tagged=[r for r in registry if tag in r['candidate_tactics']]
        taxonomy[tag]={'name':meta['name'],'description':meta['description'],'tasks':len(tagged),
          'missing':sum(not r['upstream'] and not ej.get(r['task_id'],{}).get('ready') for r in tagged),
          'training':sum(r['split']=='training' for r in tagged),'evaluation':sum(r['split']=='evaluation' for r in tagged)}
    hist={}
    for split in ['training','evaluation','combined']:
        group=[r for r in rs if split=='combined' or r['split']==split]
        for kind in ['queries','demonstrations','all_pairs']:
            ps=[p for r in group for p in (r['canonical']['test'] if kind=='queries' else r['canonical']['train'] if kind=='demonstrations' else pairs(r['canonical']))]
            hist[f'{split}_{kind}']=summarise(ps)
    if args.generated_dir:
        import pyarrow.parquet as pq
        q=[]
        for file in sorted(Path(args.generated_dir).glob('*.parquet')):
            for batch in pq.ParquetFile(file).iter_batches(columns=['test','solutions']):
                for row in batch.to_pylist():q.extend({'input':t['input'],'output':s} for t,s in zip(row['test'],row['solutions']))
        hist['generated_queries']=summarise(q)
    summary={'total_tasks':len(rs),'upstream_sources':len(set(present)&UPSTREAM_IDS),'upstream_fixture_pass':sum(x['matches_pair_set'] for x in fixtures if x['task_id'] in UPSTREAM_IDS),
       'upstream_fixture_mismatches':[x for x in fixtures if x['task_id'] in UPSTREAM_IDS and not x['matches_pair_set']],
       'new_extensions_pass':sum(x['ready'] and x['task_id'] not in UPSTREAM_IDS for x in exts),
       'reviewed_standalone_additions':sum(not r['upstream'] and r.get('standalone_review',{}).get('semantic_review',{}).get('status')=='reviewed' for r in registry if r.get('standalone_review')),
       'corrected_teaching_extensions':[x['task_id'] for x in exts if x['ready'] and x['fixture_basis']['corrected']],
       'size_extensions_pass':sum(x['ready'] and x['task_id'] in UPSTREAM_IDS for x in exts),
       'missing_upstream':sum(not r['upstream'] for r in registry),'holdouts':index['holdout_ids'],
       'active_excluded_ids':[],'training_family_target':1120,
       'status_counts':dict(Counter(r['status'] for r in registry)),
       'meaning':'Task-ID/source coverage is distinct from semantic coverage. Tactic tags are overlapping lexical candidates. Original fixtures are preserved unchanged.'}
    result={'summary':summary,'histograms':hist,'taxonomy':taxonomy,'tasks':registry,
      'generated_snapshot':'b0cdaf735fe3a0fa6f5e4f3713f98a75a146b298' if args.generated_dir else None}
    (report/'inventory.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    (report/'extension-validation.json').write_text(json.dumps(exts,indent=2)+'\n')
    with (report/'generator-roadmap.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n')
        w.writerow(['task_id','split','former_holdout','training_eligible','status','standalone_module','candidate_tactics','reference_file','query_shapes','required_next_step'])
        for r in registry:
            shape=';'.join(f"{len(p['input'])}x{len(p['input'][0])}->{len(p['output'])}x{len(p['output'][0])}" for p in r['canonical']['test'])
            next_step='Construct, validate and review standalone generator' if r['status']=='generator_missing' else 'Expand semantic and boundary-case tests'
            w.writerow([r['task_id'],r['split'],r['held_out'],True,r['status'],r['standalone_module'],
                        ';'.join(r['candidate_tactics']),f"references/{r['task_id']}.json",shape,next_step])
    with (report/'exact-size-histograms.csv').open('w') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(['source','grid','axis','size','count','percentage'])
        for name,histogram in hist.items():
            for g in ['input','output']:
                for axis in ['height','width','longest']:
                    for i,c in histogram[g][axis].items():w.writerow([name,g,axis,i,c,100*c/histogram['pairs']])
    with (report/'exact-shape-histograms.csv').open('w') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(['source','grid','height','width','count'])
        for name,histogram in hist.items():
            for g in ['input','output']:
                for shape,c in histogram[g]['shapes'].items():w.writerow([name,g,*shape.split('x'),c])
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
