"""Exhaustively check two native parameter expansions; no publication or training."""
import hashlib, importlib, itertools, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from arc_agi2.runtime import check_reference, verification_solver, call, grid, reference
from arc_agi2.program_targets import compile_target, make_record
from arc_agi2.augmentation import exhaustive_variants, demonstrations_disambiguate
from arc_agi2.build_million import canonical_input, input_split, digest

out=Path(__file__).with_name('two-expanded-domains.json')
results=[]
for tid in ('6f8cd79b','794b24be'):
    module=importlib.import_module('tasks.task_'+tid)
    assert check_reference(tid)['canonical']['all_exact']
    legacy=verification_solver(tid)
    code,_=compile_target(tid); ns={}; exec(code,ns)
    fixture=module.validate()['train']
    params=([{'width':w,'height':h} for w in range(3,31) for h in range(3,31)]
        if tid=='6f8cd79b' else
        [{'size':4,'rows':[v//4 for v in points],'cols':[v%4 for v in points]}
         for n in range(1,5) for points in itertools.combinations(range(16),n)])
    pairs=[]; hashes=set()
    for kw in params:
        pair=module.generate(**kw)
        for key in ('input','output'): pair[key]=grid(pair[key])
        assert grid(call(legacy,pair['input'],seconds=2))==pair['output'],(tid,kw,'legacy')
        assert grid(call(ns['solve'],fixture,pair['input'],seconds=2))==pair['output'],(tid,kw,'target')
        h=digest(pair['input']); assert h not in hashes;hashes.add(h);pairs.append(pair)
    eligible=[p for p in pairs if input_split(canonical_input(p['input']))=='train']
    rng=random.Random(20261021); bases=[]; variants_count=0
    for ep in range(20):
        while True:
            four=rng.sample(eligible,4)
            if len({canonical_input(p['input']) for p in four})==4: break
        palette=list(range(10));rng.shuffle(palette)
        variants=exhaustive_variants(four,palette)
        assert demonstrations_disambiguate(variants)
        for v in variants:
            f=v['pairs']; record=make_record({'episode_id':f'expansion-{tid}-{ep}-{v["d4_transform"]}',
                'task_id':tid,'train':f[:3],'test':[{'input':f[-1]['input']}],
                'solutions':[f[-1]['output']], 'd4_transform':v['d4_transform'],
                'color_permutation':v['color_permutation']},source_revision='local-validation')
            assert record['verification']['all_exact']; variants_count+=1
        bases.append({'input_hashes':[digest(p['input']) for p in four],
            'palette':palette,'represented_d4':sorted(i for v in variants for i in v['equivalent_d4'])})
    result={'task_id':tid,'native_source_sha256':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        'fixture_exact':True,'distinct_pairs_exhaustively_verified':len(pairs),
        'native_input_domain_sha256':digest(sorted(hashes)),
        'training_inputs':len(eligible),'validation_inputs':len(pairs)-len(eligible),
        'program_sha256':hashlib.sha256(code.encode()).hexdigest(),
        'checked_fresh_episodes':20,'checked_distinct_d4_records':variants_count,
        'episodes':bases,'model_training_launched':False,'published':False}
    results.append(result);out.write_text(json.dumps(results,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='episodes'},flush=True)
