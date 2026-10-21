# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2,<3", "pyarrow>=19,<26", "huggingface-hub>=1,<2", "Pillow>=11,<13", "datasets>=4,<6"]
# ///
"""Two-stage adaptive episode builder. Run as python -m arc_agi2.build_million.

No language-model calls. Persist pools and reports as workers complete, then
allocate fresh training episodes by query size and output-shape relation,
then expand every fresh episode into all eight D4 transforms.
Shortfalls are reported explicitly, never padded with duplicate episodes.
"""
import argparse,concurrent.futures as cf,copy,hashlib,importlib,json,math,os,random,time
from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from .context_budget import bounds as context_bounds, reuse_limits, VERSION as CONTEXT_BUDGET_VERSION
from huggingface_hub import HfApi,CommitOperationAdd,snapshot_download
from .runtime import BASE,reference,solver,verification_solver,call,grid
from .fixture_policy import fixture_basis,APPROVED_CORRECTIONS
from .generators.registry import GENERATORS,generate
from .task_registry import NEW_TASK_IDS
from .audit import relation,UPSTREAM_IDS
from .augmentation import transformed, exhaustive_variants, demonstrations_disambiguate
from .contextual import CONTEXTUAL_TASK_IDS, verify_shared_picture_episode
from .motif_context import MissingMotifEvidence, solve_demonstrated_motifs
from .colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence, EvidenceSearchBudget, require_colour_evidence
from .program_targets import compile_target, audit_target, make_record, TargetError
from .visual_shards import VisualShardWriter
from .episode_shape_policy import profile_from_task, select_demonstrations, describe as describe_shapes
from .pool_sampling import sample_native, SamplerTimeout, load_native_seed_pool, family_budget_seconds, timeout_limits
from .finite_input_policy import (FINITE_INPUT_TASK_IDS, FAMILY_PROVENANCE,
    VERSION as FINITE_INPUT_POLICY_VERSION, POLICY_SIGNATURE as FINITE_INPUT_POLICY_SIGNATURE,
    identity_key, minimum_class_requirement, input_split)

STORED_CONTEXT_TASK_IDS = CONTEXTUAL_TASK_IDS | {'7b7f7511'}

LEGEND_TASK_IDS = frozenset(('27a28665', '9110e3c5', 'd4469b4b'))

@lru_cache(maxsize=3)
def legend_solver(tid):
    source, _ = compile_target(tid)
    audit_target(tid, source)
    namespace = {}
    exec(source, namespace)
    return namespace['solve']

POLICY=json.loads((BASE/'training_policy.json').read_text())

SEED=20261021
# Library callers retain the legacy grid-pool API; the CLI defaults to the
# combined PNG dataset below. Production jobs must use the CLI.
OUTPUT_FORMAT=os.environ.get('ARCGEN_OUTPUT_FORMAT','legacy-grid-parquet')
if OUTPUT_FORMAT not in ('program-grid-png','legacy-grid-parquet'):
    raise ValueError('Unsupported output format')
REPO=os.environ.get('ARCGEN_DATASET_REPO', 'ritwika96/arc-agi2-program-grid-sft' if OUTPUT_FORMAT=='program-grid-png' else 'ritwika96/arc-agi2-arcgen-1m-episodes')
OUT=Path(os.environ.get('ARCGEN_BUILD_ROOT','/tmp/arcgen-million'))
WORKERS=int(os.environ.get('ARCGEN_WORKERS','32'))
POOL_SIZE=int(os.environ.get('ARCGEN_POOL_SIZE','1200'))
FAMILY_SECONDS=int(os.environ.get('ARCGEN_FAMILY_SECONDS','900'))
TARGET=int(os.environ.get('ARCGEN_TARGET_EPISODES',str(POLICY['planned_dataset']['fresh_episode_target'])))
VAL_TARGET=int(os.environ.get('ARCGEN_VALIDATION_EPISODES','20000'))

def compact(x):return json.dumps(x,separators=(',',':'),sort_keys=True)
def digest(x):return hashlib.sha256(compact(x).encode()).hexdigest()
def seed(*parts):return int(digest([SEED,*parts])[:15],16)
def dump(path,x):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(path)
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
def repartition_pool(rows, report):
    """Pure migration of saved pools to the global input split policy.

    Run on ALL families, not just finite families: their orbits can overlap.
    Regenerate affected episodes; never retain an old validation episode with
    an input now reserved for training. No labels are consulted for selection.
    File hashes/cache signatures are removed until the caller persists and
    audits the migrated pool. The original values survive in the migration.
    """
    updated=[];changed=[];dropped=[];seen=set()
    for original in rows:
        row=copy.deepcopy(original)
        members=[row]+row.get('context_pairs',[])
        for pair in members:
            ih=digest(pair['input']);ch=canonical_input(pair['input'])
            if pair['input_hash']!=ih or pair['canonical_input_hash']!=ch:
                raise ValueError('Saved pool input identity disagrees with visible grid')
            old=pair['split'];pair['split']=input_split(ch)
            if old!=pair['split']:
                changed.append({'input_hash':ih,'canonical_input_hash':ch,
                                'old_split':old,'new_split':pair['split']})
        if row['input_hash'] in seen:raise ValueError('Saved pool contains duplicate exact query inputs')
        seen.add(row['input_hash'])
        if any(p['split']!=row['split'] for p in row.get('context_pairs',[])):
            dropped.append({'input_hash':row['input_hash'],
                            'reason':'stored_context_spans_new_global_splits'})
            continue
        updated.append(row)
    result=copy.deepcopy(report)
    migration={'version':FINITE_INPUT_POLICY_VERSION,'policy_signature':FINITE_INPUT_POLICY_SIGNATURE,
               'original_source_signature':result.pop('source_signature',None),
               'original_file_sha256':result.pop('sha256',None),
               'original_pairs':len(rows),'retained_pairs':len(updated),
               'changed_inputs':changed,'dropped_stored_contexts':dropped,
               'requires_episode_rebuild':bool(changed or dropped),
               'scope_requirement':'Apply globally across every family before rebuilding episodes.'}
    result.update(pairs=len(updated),complete=bool(updated),
                  distinct_canonical_inputs=len({p['canonical_input_hash'] for p in updated}),
                  finite_input_policy_signature=FINITE_INPUT_POLICY_SIGNATURE,
                  finite_input_identity_key=identity_key(report['task_id']),
                  finite_input_provenance=dict(FAMILY_PROVENANCE[report['task_id']])
                  if report['task_id'] in FINITE_INPUT_TASK_IDS else None)
    for split in ('train','validation'):
        selected=[p for p in updated if p['split']==split]
        result[split+'_strata']=counts(updated,split)
        result[split+'_canonical']=len({p['canonical_input_hash'] for p in selected})
        result[split+'_context_episodes']=len(selected) if report.get('contextual') else 0
        result[split+'_distinct_context_upper_by_stratum']=context_bounds(selected,identity_key(report['task_id']),bool(report.get('contextual')))
    result['context_budget_version']=CONTEXT_BUDGET_VERSION
    if 'requested_pool_size' in result:
        result['quota_complete']=len(updated)>=result['requested_pool_size']
        result['pool_shortfall']=max(0,result['requested_pool_size']-len(updated))
    result['split_migration']=migration
    return updated,result,migration

def input_stats(g):
    c=Counter(v for row in g for v in row)
    return {'height':len(g),'width':len(g[0]),'colours':len(c),'dominant_fraction':max(c.values())/sum(c.values())}

def picture_episode(module, tid, sample_seed):
    """Preserve episode context AND deterministic input-equivalence splits."""
    random.seed(sample_seed)
    first=call(module.generate_episode,seconds=3)
    # A demonstrated full picture is sufficient context; no canonical bitmap.
    picture=first['train'][0]['output']
    colours=sorted({v for row in picture for v in row})
    template=[[int(v==colours[0]) for v in row] for row in picture]
    context_id=canonical_input(picture)
    split=input_split(context_id)
    selected=[];seen=set()
    initial=first['train']+first['test']
    for attempt in range(400):
        pair_seed=sample_seed if attempt<len(initial) else seed(tid,sample_seed,'context-crop',attempt)
        if attempt<len(initial):
            pair=initial[attempt]
        else:
            random.seed(pair_seed)
            pair=call(module.generate,template=template,seconds=3)
        pair={k:grid(pair[k]) for k in ['input','output']}
        identity=canonical_input(pair['input'])
        pair_split=input_split(identity)
        if pair_split!=split or identity in seen:continue
        seen.add(identity)
        selected.append(dict(pair,task_id=tid,seed=pair_seed,
            parameters=compact({'context_id':context_id,'episode_seed':sample_seed}),
            generator_mode='episode_shared_picture',input_hash=digest(pair['input']),
            canonical_input_hash=identity,split=split,stratum=stratum(pair)))
        if len(selected)==4:
            episode={'train':selected[:3],'test':selected[3:]}
            call(verify_shared_picture_episode,episode,seconds=3)
            return selected,context_id
    raise ValueError('Could not obtain four distinct crops in the shared-picture split')

def pool_signature(tid,configs):
    # Invalidate cached pools after constructor, verifier, policy or selection changes.
    files=[Path(__file__),BASE/'runtime.py',BASE/'verified_rules.py',BASE/'joint_fragments.py',BASE/'contextual.py',BASE/'motif_context.py',BASE/'repeat_tile_context.py',BASE/'program_targets.py',BASE/'direct_programs.py',BASE/'fixture_policy.py',BASE/'helpers.py',BASE/'training_policy.json',
           BASE/'references'/f'{tid}.json',BASE.parent/'common.py',BASE/'task_registry.py']
    files+=sorted((BASE/'generators').glob('*.py'))
    # Evidence policies and target factories affect which inputs/contexts are
    # eligible. A pool built under an older policy must not silently resume.
    files+=sorted(p for p in BASE.glob('*.py') if not p.name.startswith('test_'))
    for name in (f'task_{tid}.py', f'{tid}.json'):
        path=BASE/'direct_factories'/name
        if path.exists():files.append(path)
    certificate=BASE/'reports/direct-certificates'/f'{tid}.json'
    if certificate.exists():files.append(certificate)
    files=list(dict.fromkeys(files))
    native=BASE.parent/'tasks'/f'task_{tid}.py'
    if native.exists():files.append(native)
    if tid == '985ae207':files.append(BASE/'audit_support/task_985ae207_parameter_sampler.cpp')
    if tid == '1b8318e3':files.append(BASE/'audit_support/task_1b8318e3_raw_pool.jsonl')
    hashes={str(p.relative_to(BASE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return digest({'source_hashes':hashes,'approved_parameters':configs,'reviewed_standalone':tid in NEW_TASK_IDS,'output_format':OUTPUT_FORMAT,
                   'finite_input_policy_signature':FINITE_INPUT_POLICY_SIGNATURE,
                   'family_budget_seconds':family_budget_seconds(tid,FAMILY_SECONDS),'sampling_timeout_limits':timeout_limits(tid)})

def make_pool(tid):
    start=time.monotonic();rng=random.Random(seed(tid,'pool'));r=reference(tid)
    assert tid not in POLICY['excluded_task_ids']
    report_path=OUT/'pool_reports'/f'{tid}.json';file=OUT/'pools'/f'{tid}.parquet'
    configs=json.loads((BASE/'reports/parameter-validation.json').read_text()).get(tid,{}).get('approved',[])
    signature=pool_signature(tid,configs);family_seconds=family_budget_seconds(tid,FAMILY_SECONDS)
    if file.exists() and report_path.exists():
        old=json.loads(report_path.read_text())
        if (old.get('complete') and old.get('seed')==SEED and old.get('source_signature')==signature
                and old.get('requested_pool_size')==POOL_SIZE
                and old.get('sha256')==hashlib.sha256(file.read_bytes()).hexdigest()):return old
    existing=(BASE.parent/'tasks'/f'task_{tid}.py').exists()
    native_module=importlib.import_module('tasks.task_'+tid) if existing else None
    native=native_module.generate if existing else None
    refs=verification_solver(tid) if tid in GENERATORS or tid not in UPSTREAM_IDS else None
    if configs and refs is None:refs=verification_solver(tid)
    seed_records,seed_pool_metadata=load_native_seed_pool(tid,native) if native else ([],None)
    seed_record_cursor=0;sampling_modes=Counter();timeout_records=[];termination_reason=None
    rows=[];seen={};canonical=set();reject=Counter();stale=0;trials=0
    while len(rows)<POOL_SIZE and time.monotonic()-start<family_seconds and trials<POOL_SIZE*40:
        trials+=1;s=seed(tid,'pair',trials);random.seed(s);np.random.seed(s % (2**32));kw={};mode='default' if tid in UPSTREAM_IDS else 'standalone_constructor'
        if getattr(native_module, 'SYNTHETIC_VARIANT', None):
            # A versioned family definition must not mix legacy extension labels.
            mode = 'default'
        elif tid in NEW_TASK_IDS:
            pass  # Reviewed standalone replaces, rather than mixes with, its archived draft.
        elif tid in GENERATORS and (native is None or rng.random()<.6):mode='extension'
        elif configs and rng.random()<.6:kw=rng.choice(configs)['parameters'];mode='parameter_override'
        contextual=None;sampling_metadata=None;phase='sampling'
        try:
            if seed_record_cursor < len(seed_records):
                saved=seed_records[seed_record_cursor];seed_record_cursor+=1
                p={k:grid(saved['pair'][k]) for k in ['input','output']}
                s=saved['seed'];kw={};mode='default'
                sampling_metadata=dict(seed_pool_metadata,index=saved['index'],seed=s,
                                       archived_status=saved['status'],archived_generation_seconds=saved.get('gen_seconds'),attempts=[])
            elif tid == '7b7f7511':
                from .repeat_tile_context import generate_episode
                # Give rare native ambiguity cases explicit curriculum coverage.
                four,context_id=generate_episode(s,canonical_input,digest,
                                                force_ambiguous_query=trials%10==0)
                for pair in four:
                    pair['stratum']=stratum(pair)
                    pair['split']=input_split(pair['canonical_input_hash'])
                if len({pair['split'] for pair in four})!=1:
                    raise ValueError('Stored repeat context spans global input splits')
                contextual=dict(four[-1],context_pairs=four[:3],context_id=context_id)
                p={k:four[-1][k] for k in ['input','output']}
                mode='episode_shared_repeat_axis'
            elif tid in CONTEXTUAL_TASK_IDS:
                four,context_id=picture_episode(native_module,tid,s)
                contextual=dict(four[-1],context_pairs=four[:3],context_id=context_id)
                p={k:four[-1][k] for k in ['input','output']}
                mode='episode_shared_picture'
            else:
                if mode=='extension':
                    p,sampling_metadata=sample_native(tid,lambda:generate(tid,s),s,use_compiled=False)
                    sampling_metadata['mode']='legacy_extension'
                else:
                    p,sampling_metadata=sample_native(tid,native,s,kw)
                p={k:grid(p[k]) for k in ['input','output']}
            if sampling_metadata:
                sampling_modes[sampling_metadata['mode']]+=1
                if any(a.get('status')=='timeout' for a in sampling_metadata.get('attempts',[])):
                    timeout_records.append(sampling_metadata)
            phase='legacy_verification'
            if tid not in STORED_CONTEXT_TASK_IDS and mode!='default' and grid(call(refs,p['input'],seconds=2))!=p['output']:
                reject['reference_disagreement']+=1;continue
        except SamplerTimeout as e:
            reject['sampler_timeout_exhausted']+=1;e.metadata['generator_mode']=mode;timeout_records.append(e.metadata);continue
        except TimeoutError:
            if phase=='legacy_verification':reject['reference_timeout']+=1
            else:
                reject['context_sampler_timeout']+=1
                timeout_records.append({'task_id':tid,'seed':s,'mode':mode,'attempts':[{'status':'timeout','limit_seconds':None,'deadline_source':'context generator internal deadline'}]})
            continue
        except Exception as e:reject[type(e).__name__]+=1;continue
        ih,oh=digest(p['input']),digest(p['output'])
        if ih in seen:
            reason=('duplicate_input' if seen[ih]==oh else
                    'duplicate_query_input_other_context' if tid=='7b7f7511' else 'conflicting_label')
            reject[reason]+=1;stale+=1
            if stale>=max(200,len(rows)*3):
                termination_reason='duplicate_stagnation';break
            continue
        stale=0;seen[ih]=oh;c=canonical_input(p['input']);canonical.add(c)
        # Split assignment depends only on input equivalence class, not family/seed/output.
        split=input_split(c)
        rows.append(contextual if contextual is not None else
                    dict(task_id=tid,input=p['input'],output=p['output'],seed=s,parameters=compact({'requested_parameters':kw,'sampling':sampling_metadata}) if sampling_metadata else compact(kw),
                    generator_mode=mode,input_hash=ih,canonical_input_hash=c,split=split,stratum=stratum(p)))
    if termination_reason is None:
        termination_reason=('requested_pool_reached' if len(rows)>=POOL_SIZE else
                            'family_time_budget' if time.monotonic()-start>=family_seconds else 'draw_attempt_limit')
    sampling_report={'family_budget_seconds':family_seconds,'termination_reason':termination_reason,
                     'draw_attempts':trials,'quota_complete':len(rows)>=POOL_SIZE,'pool_shortfall':max(0,POOL_SIZE-len(rows)),
                     'sampling_modes':dict(sampling_modes),'sampling_timeout_attempts':sum(sum(a.get('status')=='timeout' for a in m.get('attempts',[])) for m in timeout_records),
                     'sampling_timeouts':timeout_records,'archived_raw_pool':seed_pool_metadata,'archived_records_consumed':seed_record_cursor,
                     'archived_status_counts_consumed':dict(Counter(r['status'] for r in seed_records[:seed_record_cursor]))}
    if not rows:
        report=dict(task_id=tid,complete=False,pairs=0,reason='no valid unique pairs',rejections=dict(reject),**sampling_report)
        dump(report_path,report);return report
    file.parent.mkdir(parents=True,exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows),file,compression='zstd')
    assert pq.read_table(file).to_pylist()==rows
    report={'task_id':tid,'seed':SEED,'source_signature':signature,'requested_pool_size':POOL_SIZE,'complete':True,'pairs':len(rows),'distinct_canonical_inputs':len(canonical),
       'finite_input_policy_signature':FINITE_INPUT_POLICY_SIGNATURE,
       'finite_input_identity_key':identity_key(tid),
       'finite_input_provenance':dict(FAMILY_PROVENANCE[tid]) if tid in FINITE_INPUT_TASK_IDS else None,
       'train_strata':counts(rows,'train'),'validation_strata':counts(rows,'validation'),
       'train_canonical':len({r['canonical_input_hash'] for r in rows if r['split']=='train'}),
       'validation_canonical':len({r['canonical_input_hash'] for r in rows if r['split']=='validation'}),
       'contextual':tid in STORED_CONTEXT_TASK_IDS,
       'train_context_episodes':sum(r['split']=='train' for r in rows) if tid in STORED_CONTEXT_TASK_IDS else 0,
       'validation_context_episodes':sum(r['split']=='validation' for r in rows) if tid in STORED_CONTEXT_TASK_IDS else 0,
       'modes':dict(Counter(r['generator_mode'] for r in rows)),'rejections':dict(reject),'seconds':time.monotonic()-start,
       'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),**sampling_report}
    for split in ('train','validation'):
        report[split+'_distinct_context_upper_by_stratum']=context_bounds(
            [r for r in rows if r['split']==split],identity_key(tid),tid in STORED_CONTEXT_TASK_IDS)
    report['context_budget_version']=CONTEXT_BUDGET_VERSION
    dump(report_path,report);return report

def allocate(reports,split,target,desired):
    from arc_agi2.finite_input_policy import capacity_basis, FINITE_INPUT_TASK_IDS
    from arc_agi2.context_budget import VERSION as CONTEXT_BUDGET_VERSION
    # Fresh episode quotas, before augmentation. The histogram is a preference,
    # not a reason to withhold a family's otherwise feasible 1,000 episodes.
    if target < 0 or any(v < 0 for v in desired.values()):
        raise ValueError('Allocation counts must be nonnegative')
    ceiling=POLICY['planned_dataset']['fresh_episodes_per_family']
    # Canonical classes decide within-episode eligibility, not corpus size.
    # Ordinary episodes retain four distinct canonical inputs, but different
    # exact queries/context sets can form fresh episodes from the same orbits.
    # Legacy reports keep their historical reuse budget. Re-audited reports
    # instead carry an exact combinatorial upper bound before semantic gates.
    multipliers={r['task_id']:1 if r.get('contextual') or r['task_id'] in FINITE_INPUT_TASK_IDS else 4
                 for r in reports}
    capacity={r['task_id']:min(ceiling,r[split+'_context_episodes'] if r.get('contextual') else
                              multipliers[r['task_id']]*sum(r[split+'_strata'].values())) for r in reports
              if capacity_basis(r,split)>0}
    support={r['task_id']:r[split+'_strata'] for r in reports if r['task_id'] in capacity}
    contextual={r['task_id']:r.get('contextual',False) for r in reports}
    limits={t:{k:multipliers[t]*n for k,n in support[t].items()}
            for t in capacity}
    for report in reports:
        tid=report['task_id']
        if tid in capacity and report.get('context_budget_version')==CONTEXT_BUDGET_VERSION:
            limits[tid]={k:min(ceiling,n) for k,n in report[split+'_distinct_context_upper_by_stratum'].items()}
            capacity[tid]=min(ceiling,sum(limits[tid].values()))
    capacity={t:min(c,sum(limits[t].values())) for t,c in capacity.items()}
    budgets={};keys=sorted(k for k in desired if desired[k]);total=sum(desired.values())
    for k in keys:budgets[k]=int(target*desired[k]/total)
    for k in sorted(keys,key=lambda k:target*desired[k]/total-budgets[k],reverse=True)[:target-sum(budgets.values())]:budgets[k]+=1
    allocation={tid:Counter() for tid in capacity};used=Counter();missing={}
    # Scarce strata first. Per-stratum caps also limit reusing a small query pool.
    order=sorted(keys,key=lambda k:sum(min(capacity[t],limits[t].get(k,0)) for t in capacity)/max(1,budgets[k]))
    for k in order:
        remaining=budgets[k]
        available={t:min(capacity[t]-used[t],limits[t].get(k,0)) for t in capacity}
        while remaining:
            ts=[t for t,c in available.items() if c>0]
            if not ts:break
            share=max(1,remaining//len(ts))
            for t in sorted(ts,key=lambda t:(used[t],seed(t,k))):
                n=min(share,available[t],remaining);allocation[t][k]+=n;used[t]+=n;available[t]-=n;remaining-=n
                if not remaining:break
        if remaining:missing[k]=remaining
    preferred_allocated=sum(used.values())
    actual=Counter()
    for row in allocation.values():actual.update(row)
    remaining=min(target,sum(capacity.values()))-preferred_allocated
    # Recover quota stranded by unavailable sizes using real pool strata only.
    # Equal shares favour underfilled families; within each family, prefer the
    # largest outstanding histogram deficit before accepting a size deviation.
    while remaining:
        ts=[t for t in capacity if used[t]<capacity[t]]
        if not ts:break
        share=max(1,remaining//len(ts));progress=0
        for t in sorted(ts,key=lambda t:(used[t],seed(t,'quota-recovery'))):
            allowance=min(share,capacity[t]-used[t],remaining)
            ks=sorted(limits[t],key=lambda k:(
                -(budgets.get(k,0)-actual[k]),-desired.get(k,0),k))
            for k in ks:
                n=min(allowance,limits[t][k]-allocation[t][k])
                if n<=0:continue
                allocation[t][k]+=n;used[t]+=n;actual[k]+=n
                allowance-=n;remaining-=n;progress+=n
                if not allowance:break
            if not remaining:break
        if not progress:break
    missing={k:n-actual[k] for k,n in budgets.items() if n>actual[k]}
    return {t:dict(v) for t,v in allocation.items() if v},{
        'requested':target,'allocated':sum(used.values()),
        'allocation_shortfall':target-sum(used.values()),
        'shortfall_by_stratum':missing,'desired':budgets,'actual':dict(actual),
        'histogram_surplus_by_stratum':{k:n-budgets.get(k,0) for k,n in actual.items() if n>budgets.get(k,0)},
        'quota_recovered_outside_histogram':sum(used.values())-preferred_allocated,
        'family_capacity':capacity,'family_allocated':dict(used),
        'family_capacity_shortfall':{r['task_id']:ceiling-capacity.get(r['task_id'],0)
                                    for r in reports if capacity.get(r['task_id'],0)<ceiling},
        'family_unused_capacity':{t:c-used[t] for t,c in capacity.items() if c>used[t]},
        'capacity_policy':CONTEXT_BUDGET_VERSION if all(r.get('context_budget_version')==CONTEXT_BUDGET_VERSION for r in reports) else 'exact-query-reuse-budget-v2',
        'capacity_is_verified_episode_count':False,
        'policy':'Audited distinct demo-set/query combinations bound allocation where available; legacy reports use exact-query reuse budgets. Context/semantic verification determines realized fresh episodes.'}

def make_episodes(arg):
    tid,allocs=arg;basis=fixture_basis(tid);pool=pq.read_table(OUT/'pools'/f'{tid}.parquet').to_pylist();result={};all_hashes=set()
    identity=identity_key(tid)
    for row in pool:
        for pair in [row]+row.get('context_pairs',[]):
            if pair['split']!=input_split(pair['canonical_input_hash']):
                raise ValueError('Stale pool split: globally repartition and recount all pools before episode construction')
    shape_profile=profile_from_task(reference(tid)['canonical'])
    for split,quota in allocs.items():
        rows=[r for r in pool if r['split']==split];bins=defaultdict(list)
        for p in rows:bins[p['stratum']].append(p)
        identity_total=len({p[identity] for p in rows})
        rng=random.Random(seed(tid,split,'episodes'));query_uses=Counter();pair_uses=Counter();failures=Counter()
        accepted_contexts=defaultdict(set)
        _,pair_reuse_limit=reuse_limits(sum(quota.values()),len(rows),finite=tid in FINITE_INPUT_TASK_IDS,
                                       stored_context=tid in STORED_CONTEXT_TASK_IDS)
        query_context_shortfalls=[];query_rejections=[];quarantined_queries=set();shape_counts=Counter()
        hist={which:{axis:Counter() for axis in ['height','width','longest','shapes']} for which in ['input','output']};relations=Counter()
        path=OUT/'data'/split/f'{tid}.parquet';path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.parquet.tmp');writer=None;buffer=[]
        if OUTPUT_FORMAT == 'program-grid-png':
            writer=VisualShardWriter(OUT/'shards'/split,tid)
        fresh_count=0;variant_count=0;symmetric_duplicates=0;variant_counts=Counter()
        def flush():
            nonlocal writer
            if not buffer:return
            if OUTPUT_FORMAT == 'program-grid-png':
                for record in buffer:writer.write(record)
                buffer.clear();return
            if writer is None:
                # Optional shape fallback is often null throughout the first
                # batch, then a string later. Pin its semantic type before
                # streaming so Arrow's first-batch inference cannot lock it to null.
                schema=pa.Table.from_pylist(buffer).schema
                shape=pa.struct([('demo_input_shapes',pa.string()),('query_input_shape',pa.string())])
                pattern=pa.struct([('policy',pa.string()),('requested',shape),('matched',pa.bool_()),
                                   ('fallback',pa.string()),('observed',shape),('identity_key',pa.string())])
                index=schema.get_field_index('episode_input_shape_pattern')
                schema=schema.set(index,pa.field('episode_input_shape_pattern',pattern))
                writer=pq.ParquetWriter(temporary,schema,compression='zstd')
            table=pa.Table.from_pylist(buffer,schema=writer.schema)
            writer.write_table(table);buffer.clear()
        try:
            for k,n in quota.items():
                candidates=bins[k][:];rng.shuffle(candidates)
                query_reuse_limit,_=reuse_limits(n,len(candidates),finite=tid in FINITE_INPUT_TASK_IDS,
                                                stored_context=tid in STORED_CONTEXT_TASK_IDS)
                if len(rows)<4 or identity_total<minimum_class_requirement(tid) or not candidates:
                    failures['insufficient_distinct_inputs']+=n;continue
                for j in range(n):
                    accepted=False
                    # Fix the query BEFORE searching for teaching context.
                    # Switching queries after an evidence rejection would
                    # silently bias the dataset toward easier query cases.
                    q=next((candidates[(j+offset)%len(candidates)]
                            for offset in range(len(candidates))
                            if query_uses[candidates[(j+offset)%len(candidates)]['input_hash']]<query_reuse_limit
                            and candidates[(j+offset)%len(candidates)]['input_hash'] not in quarantined_queries),None)
                    if q is None:
                        failures['query_reuse_exhausted']+=1
                        continue
                    terminal_rejection=None
                    context_attempts=1 if tid in STORED_CONTEXT_TASK_IDS else 50
                    def quarantine_query(kind, exc, attempt):
                        nonlocal terminal_rejection
                        terminal_rejection=kind
                        quarantined_queries.add(q['input_hash'])
                        failures[kind]+=1
                        query_rejections.append({'query_input_hash':q['input_hash'],
                            'stratum':k,'context_attempts':attempt,'kind':kind,
                            'error':str(exc),'witness':getattr(exc,'witness',{})})
                    for retry in range(context_attempts):
                        shape_report=None
                        if tid in STORED_CONTEXT_TASK_IDS:
                            demos=q['context_pairs']
                            if len(demos)!=3 or any(p['split']!=split for p in demos):
                                raise ValueError('Invalid stored episode context')
                            if tid == '7b7f7511' and any(pair_uses[p['input_hash']]>=pair_reuse_limit for p in demos):
                                failures['stored_context_reuse_exhausted']+=1
                                break
                        else:
                            ds=[p for p in rows if p[identity]!=q[identity] and pair_uses[p['input_hash']]<pair_reuse_limit]
                            if len(ds)<3:break
                            if tid == 'b7cb93ac':
                                from .packing_evidence import select_packing_demonstrations
                                demos=select_packing_demonstrations(ds,q['input'],rng,q['canonical_input_hash'],pair_uses)
                                if demos is None:
                                    failures['no_three_demo_packing_context']+=1
                                    break
                            else:
                                demos,shape_report=select_demonstrations(ds,q['input'],rng,shape_profile,identity_key=identity,
                                    excluded_contexts=accepted_contexts[q['input_hash']])
                                if demos is None:break
                        if shape_report is None:
                            observed=describe_shapes(demos,q['input'])
                            shape_report={'policy':shape_profile['version'],'requested':shape_profile['patterns'],
                                'observed':observed,'matched':observed in shape_profile['patterns'],
                                'fallback':'required_semantic_context_selector'}
                        four=demos+[q]
                        try:
                            require_colour_evidence(tid,demos,[{'input':q['input']}])
                        except EvidenceSearchBudget as exc:
                            quarantine_query('evidence_search_budget_exhausted',exc,retry+1)
                            break
                        except IntrinsicQueryEvidence as exc:
                            quarantine_query('intrinsic_query_evidence_rejected',exc,retry+1)
                            break
                        except MissingColourEvidence:
                            failures['missing_motif_evidence_attempts' if tid=='98c475bf' else 'missing_colour_evidence_attempts']+=1
                            continue
                        if tid in CONTEXTUAL_TASK_IDS:
                            call(verify_shared_picture_episode,{'train':demos,'test':[q]},seconds=3)
                        if tid == '98c475bf':
                            try:
                                predicted=call(solve_demonstrated_motifs,demos,q['input'],seconds=3)
                            except MissingMotifEvidence:
                                failures['missing_motif_evidence_attempts']+=1
                                continue
                            if predicted!=q['output']:
                                raise ValueError('Demonstration-derived motif output disagrees')
                        if tid in LEGEND_TASK_IDS:
                            try:
                                predicted = call(legend_solver(tid), demos, q['input'], seconds=3)
                            except ValueError:
                                failures['missing_or_ambiguous_legend_attempts'] += 1
                                continue
                            if predicted != q['output']:
                                raise ValueError('Demonstration-derived legend output disagrees')
                        # Audited finite-orbit families may reuse an orbit, but
                        # never an exact input. Global split grouping is unchanged.
                        if len({p[identity] for p in four})<minimum_class_requirement(tid):continue
                        if all(p['input']==p['output'] for p in four):continue
                        basehash=digest([sorted(p['input_hash'] for p in demos),q['input_hash']])
                        if basehash in all_hashes:continue
                        palette=list(range(10));cfg=POLICY['augmentation']
                        if cfg['colour_permutation_default'] or tid in cfg['colour_permutation_task_ids']:rng.shuffle(palette)
                        variants=exhaustive_variants(four,palette)
                        if not demonstrations_disambiguate(variants):
                            quarantine_query('augmented_label_conflict',
                                ValueError('Same visible augmented puzzle has conflicting labels'),retry+1)
                            break
                        base_id=f'arcgen-{tid}-{split}-base-{fresh_count:05d}'
                        pending=[]
                        for variant in variants:
                            d4=variant['d4_transform'];transformed_pairs=variant['pairs']
                            train=transformed_pairs[:3];query=transformed_pairs[-1]
                            challenge={'train':train,'test':[{'input':query['input']}]}
                            prompt='Infer the shared transformation from the demonstrations. Return only JSON with key outputs and one grid per test input.\n'+compact(challenge)
                            row={'episode_id':f'{base_id}-d4-{d4}','base_episode_id':base_id,'task_id':tid,'split':split,
                              'variant':'native' if d4==0 and palette==list(range(10)) else 'augmented',
                              'train':train,'test':challenge['test'],'solutions':[query['output']],
                              'prompt':prompt,'completion':compact({'outputs':[query['output']]}),
                              'episode_input_shape_pattern':shape_report,
                              'pair_seeds':[p['seed'] for p in four],'pair_parameters':[p['parameters'] for p in four],
                              'pair_generator_modes':[p['generator_mode'] for p in four],
                              'context_id':q.get('context_id',''),
                              'fixture_basis':basis['fixture'],
                              'corrected_teaching_fixture':basis['corrected'],
                              'correction_source':basis.get('source',''),
                              'correction_evidence_status':basis.get('evidence_status',
                                  'reviewed_upstream_proposal' if basis['corrected'] else 'canonical'),
                              'base_input_hashes':[p['input_hash'] for p in four],
                              'canonical_input_hashes':[p['canonical_input_hash'] for p in four],
                              'finite_input_policy_signature':FINITE_INPUT_POLICY_SIGNATURE,
                              'within_episode_input_identity':identity,
                              'base_episode_sha256':basehash,'d4_transform':d4,'color_permutation':palette,
                              'equivalent_d4':variant['equivalent_d4'],'distinct_spatial_variants':len(variants),
                              'query_input_height':len(query['input']),'query_input_width':len(query['input'][0]),
                              'query_output_height':len(query['output']),'query_output_width':len(query['output'][0]),
                              'query_relation':relation(query),'source_commit':os.environ.get('ARCGEN_SOURCE_COMMIT','local')}
                            assert json.loads(row['completion'])=={'outputs':row['solutions']}
                            if OUTPUT_FORMAT == 'program-grid-png':
                                try:
                                    row.update(make_record(row,source_repo='ritwikareddykancharla/ARC-GEN',source_revision=row['source_commit']))
                                except (TargetError,ValueError,TypeError,IndexError,TimeoutError) as exc:
                                    # This stage may compare against the hidden answer.
                                    # Never redraw demos to search for a context that passes it.
                                    quarantine_query('post_gate_program_rejected',exc,retry+1)
                                    dump(OUT/'rejections'/split/tid/f"{q['input_hash']}.json",
                                         {'task_id':tid,'error':str(exc),'episode':row})
                                    pending=[];break
                            pending.append(row)
                        if terminal_rejection:break
                        if not pending:continue
                        for row in pending:
                            query={'input':row['test'][0]['input'],'output':row['solutions'][0]}
                            buffer.append(row);variant_count+=1
                            if len(buffer)>=64:flush()
                            for which in hist:
                                a=query[which];h,w=len(a),len(a[0]);hist[which]['height'][h]+=1;hist[which]['width'][w]+=1;hist[which]['longest'][max(h,w)]+=1;hist[which]['shapes'][f'{h}x{w}']+=1
                            relations[relation(query)]+=1
                        fresh_count+=1;variant_counts[len(variants)]+=1;symmetric_duplicates+=8-len(variants)
                        shape_counts['matched' if shape_report['matched'] else 'deviated']+=1
                        shape_counts[compact(shape_report['observed'])]+=1
                        if shape_report['fallback']:shape_counts['fallback:'+shape_report['fallback']]+=1
                        all_hashes.add(basehash);query_uses[q['input_hash']]+=1
                        accepted_contexts[q['input_hash']].add(tuple(sorted(p['input_hash'] for p in demos)))
                        for p in four:pair_uses[p['input_hash']]+=1
                        accepted=True;break
                    if not accepted and not terminal_rejection:
                        failures['episode_constraints_exhausted']+=1
                        query_context_shortfalls.append({'query_input_hash':q['input_hash'],
                            'stratum':k,'context_attempts':retry+1})
            flush()
        except BaseException:
            if OUTPUT_FORMAT == 'program-grid-png':writer.abort()
            raise
        finally:
            if writer is not None:writer.close()
        if OUTPUT_FORMAT == 'program-grid-png':
            assert writer.records==variant_count
        elif variant_count:
            assert pq.read_metadata(temporary).num_rows==variant_count
            temporary.replace(path)
        elif path.exists():path.unlink()  # Never republish a stale nonempty shard.
        result[split]={'files':[str(p.relative_to(OUT)) for p in writer.paths] if OUTPUT_FORMAT=='program-grid-png' else ([str(path.relative_to(OUT))] if variant_count else []),
            'shards':writer.manifest if OUTPUT_FORMAT=='program-grid-png' else [],'episodes':variant_count,'fresh_episodes':fresh_count,
            'requested_fresh_episodes':sum(quota.values()),'spatial_variant_upper_bound':8*fresh_count,
            'symmetric_variants_removed':symmetric_duplicates,'variants_per_fresh_episode':dict(variant_counts),
            'query_histograms':hist,'relations':dict(relations),'failures':dict(failures),
            'episode_input_shape_profile':shape_profile,'episode_input_shape_counts':dict(shape_counts),
            'query_context_shortfalls':query_context_shortfalls,
            'query_rejections':query_rejections,'quarantined_query_count':len(quarantined_queries),
            'max_query_reuse_in_fresh_episodes':max(query_uses.values(),default=0),
            'max_pair_reuse_in_fresh_episodes':max(pair_uses.values(),default=0),'distinct_inputs_used':len(pair_uses),
            'context_budget_version':CONTEXT_BUDGET_VERSION,'pair_reuse_limit':pair_reuse_limit}
    report={'task_id':tid,'splits':result,'finite_input_policy_signature':FINITE_INPUT_POLICY_SIGNATURE,
            'within_episode_input_identity':identity,
            'finite_input_provenance':dict(FAMILY_PROVENANCE[tid]) if tid in FINITE_INPUT_TASK_IDS else None}
    dump(OUT/'episode_reports'/f'{tid}.json',report);return report

def card(m):
    if OUTPUT_FORMAT == 'program-grid-png':
        from .visual_card import card as visual_card
        return visual_card(m)
    n=m.get('train_episodes',0);v=m.get('validation_episodes',0)
    fresh=m.get('train_fresh_episodes',0)
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
# ARC-AGI-2 · Fresh procedural episodes and exhaustive D4 augmentation

**Status: {m['status']} · {fresh:,} fresh training episodes · {n:,} training examples after augmentation · {v:,} validation examples published.**

Three demonstration pairs and one query per episode, with generator-produced output targets. No reasoning or Python code in the SFT targets. The configured target is {TARGET:,} fresh training episodes and up to {8*TARGET:,} spatial variants. Counts above describe saved examples, not promised final totals.

[Visual size and coverage audit](https://ritwika96-arc-episode-gallery.static.hf.space/coverage/index.html) · [Generator fork](https://github.com/ritwikareddykancharla/ARC-GEN/tree/arc2-diversity-and-reference-generators/arc_agi2) · [Original 100K baseline](https://huggingface.co/datasets/ritwika96/arc-agi2-arcgen-100k-episodes)

## What changes

- All fixture-verified ARC-GEN generators whose task IDs occur in ARC-AGI-2, plus independently constructed, tested extensions.
- Adaptive fresh quotas: re-audited pools count distinct demo-set/query combinations, excluding demonstration-order permutations. Stored-context families retain their original bundles. Older pool reports retain their legacy query-reuse allocation until re-audited. These are construction upper bounds; semantic/context checks determine the accepted count. Query/pair reuse and shape deviations are recorded per family. The family ceiling is {POLICY['planned_dataset']['fresh_episodes_per_family']:,} before augmentation. Families with little variation receive fewer examples.
- Target query longest-side distribution at each integer size 1–30 jointly with output expansion/shrinkage/same-shape, measured on all 1,120 public tasks. Exact height, width and rectangular-shape histograms are reported separately. Unsupported targets become explicit shortfalls; difficulty is not proven equal by dimensions.
- Size overrides require original replay and differential seed checks. Overridden/extended pairs use saved teacher solvers with documented verifier improvements: `78332cb0` checks the unique complete panel chain because the archived greedy program fails on valid panel permutations. `de493100` uses a dimension-aware reflection-orbit verifier for labelled even-sized crop extensions; its archived program hardcodes the original coordinate 31. Episode-shared picture family `269e22fb` uses an independent verifier conditioned on a demonstration output, since its archived solver contains only the original picture. Original teacher programs and benchmark data remain unchanged. Default upstream generators have fixture checks, not full semantic proofs.
- Fresh input pool, no duplicated full native episodes, and no repeated exact inputs inside an episode. Inputs must also be inequivalent under D4/palette except in the {len(FINITE_INPUT_TASK_IDS)} source-audited finite-orbit families listed in `arc_agi2/finite_input_policy.py`; these still require four exact-distinct inputs and all semantic checks. Every fresh episode expands into all eight D4 transforms. Symmetric identical episodes are stored once, with every represented transform recorded in `equivalent_d4`; fresh and augmented counts remain separate. Colours are generated natively and an additional shared palette permutation follows the recorded augmentation policy. One transformation applies consistently to all demonstration inputs/outputs and the query input/output.
- Input equivalence classes under palette renaming and D4 are assigned to one split before episode construction, including across families. The sole input orbit of `833966f4` is reserved globally for training, including matching inputs of other families. Single-orbit training families have no independent unseen-orbit validation. All 1,120 public task families, including the former 20 holdouts, are training-eligible after generator validation. Synthetic validation measures new-input generalization within known families where distinct validation orbits exist.
- For `269e22fb`, each fresh picture is shared by its three demonstrations and query. These pairs are stored together and never mixed with a different picture. The picture equivalence class and every crop belong to the same deterministic split. Fresh-episode capacity is limited to the number of complete context bundles, rather than multiplying the number of queries.
- For `98c475bf`, a query marker colour must have its full motif demonstrated in the selected inputs or outputs. An independent context solver learns those templates from the demonstrations and verifies the query before augmentation. Missing-evidence attempts are rejected and counted; query answers never supply the templates.
- For `27a28665`, `9110e3c5`, and `d4469b4b`, the query's legend key must be demonstrated. Fixed canonical answer tables are not substituted for missing evidence. Repeated equivalent masks in `27a28665` stay within the same data split and its small capacity is reported explicitly.

## Generator examples

These are exact saved **local validation episodes**, not a sample from a finished million-episode build.

Sequential colour substitutions:

![Sequential legend example](assets/e4888269.png)

Legend-based room selection:

![Room removal example](assets/d59b0160.png)

Quantity-controlled dimensions and pattern composition:

![Quadrant composition example](assets/f931b4a8.png)

## Audit and reproducibility

[Manifest](manifest.json), [pool reports](pool_reports), [episode reports](episode_reports), [allocation targets](allocation.json). Master seed {SEED}. Published partial shards are complete episodes; failed families and shortfalls remain visible. No model training or LLM calls occur in this job.

Corrected teaching fixtures are reviewed and hash-pinned; episode metadata records `fixture_basis`, `corrected_teaching_fixture`, `correction_source` and `correction_evidence_status`. These fields describe the constructor's validation basis, not a claim that synthetic pairs are original fixtures. The `e12f9a14` teaching correction is a locally reviewed hypothesis, not an official correction. Canonical benchmark data is preserved unchanged.

The reference packets include saved Opus/Fable solutions; they guide input construction and validation but are not exposed in episode prompts. Public evaluation tasks used in generation are training data for subsequent models, not independent evaluation. The historical holdout list is retained as provenance only; the active exclusion list is empty.

ARC-GEN upstream code is Copyright Google LLC, Apache-2.0. This is an independent derivative. Original benchmark grids remain unchanged.
'''

def eligible_tasks(inv):
    return [r['task_id'] for r in inv['tasks'] if r['task_id'] not in POLICY['excluded_task_ids']
            and r['status'] in ['upstream_fixture_verified','extension_validated']]

def require_complete_coverage(inv):
    ids={r['task_id'] for r in inv['tasks']}
    missing=sorted(ids-set(eligible_tasks(inv)))
    if len(ids)!=POLICY['required_task_count'] or missing:
        raise RuntimeError(f"Coverage first: {len(eligible_tasks(inv))}/{POLICY['required_task_count']} validated; "
                           f"{len(missing)} missing. Bulk generation remains disabled. Use --local for bounded tests.")

def require_build_ready(inv):
    require_complete_coverage(inv)
    if POLICY.get('planned_dataset',{}).get('bulk_builder_expansion_pending'):
        raise RuntimeError('Coverage is complete but exhaustive eight-variant episode expansion is still pending; no bulk launch.')
    pending=[r['task_id'] for r in inv['tasks'] if r['status']=='extension_validated' and r['task_id'] not in NEW_TASK_IDS]
    if pending:
        raise RuntimeError(f'{len(pending)} families still need reviewed standalone task files before bulk generation.')

def require_program_ready(task_ids):
    missing=[]
    for tid in task_ids:
        try:
            for d4 in range(8):
                compile_target(tid,d4,[3,9,0,7,2,8,1,6,4,5])
        except TargetError:
            missing.append(tid)
    if missing:
        raise RuntimeError(f"{len(missing)} families lack verified direct augmented programs; "
                           f"no generation launched. First missing: {', '.join(missing[:12])}")

def bounded_completed(executor, function, items, limit):
    """Bound queued artifact producers while the parent publishes completed work."""
    iterator=iter(items)
    pending={}
    def submit_one():
        try:item=next(iterator)
        except StopIteration:return False
        pending[executor.submit(function,item)]=item
        return True
    for _ in range(limit):
        if not submit_one():break
    while pending:
        done,_=cf.wait(pending,return_when=cf.FIRST_COMPLETED)
        for future in done:
            item=pending.pop(future)
            yield future,item
            submit_one()


def main():
    global OUTPUT_FORMAT, REPO
    ap=argparse.ArgumentParser();ap.add_argument('--local',action='store_true');ap.add_argument('--tasks',nargs='*');ap.add_argument('--resume',action='store_true');ap.add_argument('--format',choices=['program-grid-png','legacy-grid-parquet'],default=os.environ.get('ARCGEN_OUTPUT_FORMAT','program-grid-png'));args=ap.parse_args()
    OUTPUT_FORMAT=args.format
    # Spawned workers import this module afresh; propagate the selected format.
    os.environ["ARCGEN_OUTPUT_FORMAT"]=OUTPUT_FORMAT
    REPO=os.environ.get('ARCGEN_DATASET_REPO','ritwika96/arc-agi2-program-grid-sft' if OUTPUT_FORMAT=='program-grid-png' else 'ritwika96/arc-agi2-arcgen-1m-episodes')
    for d in ['pools','pool_reports','episode_reports','data/train','data/validation']: (OUT/d).mkdir(parents=True,exist_ok=True)
    inv=json.loads((BASE/'reports/inventory.json').read_text());pv=json.loads((BASE/'reports/parameter-validation.json').read_text())
    eligible=eligible_tasks(inv)
    if not args.local:
        require_build_ready(inv)
    if args.tasks:
        assert set(args.tasks)<=set(eligible);eligible=args.tasks
    if OUTPUT_FORMAT == 'program-grid-png':
        require_program_ready(eligible)
    api=None if args.local else HfApi()
    if api:
        assert api.whoami()['name']=='ritwika96'
        if args.resume:
            snapshot_download(REPO,repo_type='dataset',local_dir=OUT,allow_patterns=['pools/*.parquet','pool_reports/*.json'])
    m={'status':'generating_pair_pools','target_train_fresh_episodes':TARGET,'target_validation_fresh_episodes':VAL_TARGET,
       'train_spatial_variant_upper_bound':8*TARGET,'validation_spatial_variant_upper_bound':8*VAL_TARGET,
       'source_commit':os.environ.get('ARCGEN_SOURCE_COMMIT','local'),'seed':SEED,'workers':WORKERS,
       'task_ids':eligible,'excluded_task_ids':POLICY['excluded_task_ids'],
       'former_holdout_ids':inv['summary']['holdouts'],'training_policy':POLICY,
       'approved_teaching_corrections':APPROVED_CORRECTIONS,
       'completed_pools':0,'train_episodes':0,'validation_episodes':0,
       'train_fresh_episodes':0,'validation_fresh_episodes':0,
       'train_symmetric_variants_removed':0,'validation_symmetric_variants_removed':0,
       'errors':[],'model_training_launched':False,'output_format':OUTPUT_FORMAT,'episode_files':{'train':[],'validation':[]}}
    assert not set(eligible)&set(m['excluded_task_ids'])
    def publish(files=()):
        dump(OUT/'manifest.json',m);(OUT/'README.md').write_text(card(m))
        if api:
            # Keep the working viewer/card until a complete visual shard exists.
            card_files=['README.md'] if OUTPUT_FORMAT!='program-grid-png' or m['train_episodes'] else []
            ops=[CommitOperationAdd(path_in_repo=f,path_or_fileobj=str(OUT/f)) for f in ['manifest.json',*card_files,*files] if (OUT/f).exists()]
            for retry in range(5):
                try:api.create_commit(REPO,repo_type='dataset',operations=ops,commit_message=f"{m['status']}: {m['train_episodes']:,} training episodes");break
                except Exception:
                    if retry==4:raise
                    time.sleep(2**retry)
            # Dataset shards are durable only after a successful Hub commit.
            # Keep small pools/reports for reproducibility and delete only bulky
            # uploaded artifacts when running on an ephemeral job disk.
            if os.environ.get('ARCGEN_PRUNE_UPLOADED_SHARDS')=='1':
                for name in files:
                    path=Path(name)
                    if path.parts and path.parts[0] in ('shards','viewer') and path.suffix in ('.tar','.arrow'):
                        (OUT/path).unlink(missing_ok=True)
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
        'allocation_unit':'fresh episodes before exhaustive D4 expansion',
        'target_scope':'All 1,120 public canonical tasks, query-input longest side jointly with output-shape relation.'})
    m['status']='constructing_episodes';publish(['allocation.json']);files=[];last=time.monotonic()
    combined={tid:{s:a[tid] for s,a in [('train',alloc_train),('validation',alloc_val)] if tid in a} for tid in sorted(set(alloc_train)|set(alloc_val))}
    episode_reports=[]
    with cf.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for f,item in bounded_completed(pool,make_episodes,combined.items(),WORKERS):
            tid=item[0]
            try:
                r=f.result();episode_reports.append(r);files.append(f'episode_reports/{tid}.json')
                for split,x in r['splits'].items():
                    m[split+'_episodes']+=x['episodes']
                    m[split+'_fresh_episodes']+=x['fresh_episodes']
                    m[split+'_symmetric_variants_removed']+=x['symmetric_variants_removed']
                    if x['episodes']:
                        files.extend(x['files']);m['episode_files'][split].extend(x['files'])
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
    m.update(status='complete' if m['train_fresh_episodes']==TARGET and m['validation_fresh_episodes']==VAL_TARGET and not m['errors'] else 'complete_with_shortfall',
       train_fresh_shortfall=TARGET-m['train_fresh_episodes'],validation_fresh_shortfall=VAL_TARGET-m['validation_fresh_episodes'],
       represented_train_families=sum(r['splits'].get('train',{}).get('episodes',0)>0 for r in episode_reports))
    publish(files);print(compact(m),flush=True)
if __name__=='__main__':main()
