"""Validate a standalone task module without registering unreviewed code.

Invoked in a separate, bounded process by the CLI drafting coordinator.
This is a conservative AST screen and timeout, not a security sandbox.
"""
import argparse,ast,hashlib,importlib.util,json,random,traceback
from pathlib import Path
import numpy as np
from .runtime import reference,solver,grid,call,pairs,check_reference

from .fixture_policy import fixture_basis
from .contextual import CONTEXTUAL_TASK_IDS, verify_shared_picture_episode

ALLOWED={'random','math','collections','itertools','functools','copy','heapq','statistics','numpy','common'}

def screen(source):
    tree=ast.parse(source)
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
            if any(x.split('.')[0] not in ALLOWED for x in names):raise ValueError('Disallowed import: '+str(names))
        if isinstance(n,ast.Name) and n.id in {'open','exec','eval','compile','__import__','globals','locals','getattr','setattr','delattr','vars','input','breakpoint'}:
            raise ValueError('Disallowed operation: '+n.id)
        if isinstance(n,ast.Attribute) and (n.attr.startswith('__') or n.attr in {'load','save','loadtxt','savetxt','fromfile','tofile','memmap','ctypeslib','system','popen'}):
            raise ValueError('Disallowed attribute: '+n.attr)
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    if not {'generate','validate'}<=funcs.keys():raise ValueError('Requires generate and validate functions')
    if not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='generate' for n in ast.walk(funcs['validate'])):
        raise ValueError('validate() must construct fixtures via generate(...) calls')
    return tree

def validate(tid,path,samples=300,seed_start=0):
    if samples < 1 or seed_start < 0:
        raise ValueError('samples must be positive and seed_start nonnegative')
    source=path.read_text();screen(source)
    spec=importlib.util.spec_from_file_location('candidate_'+tid,path);m=importlib.util.module_from_spec(spec)
    call(spec.loader.exec_module,m,seconds=5)
    r=reference(tid);f=solver(tid);original=check_reference(tid)
    got=call(m.validate,seconds=30)
    # Keep corrected variants explicit; never silently overwrite the benchmark.
    matches={kind:got==r[kind] for kind in ['canonical','teaching_fixture']}
    # Match original train/test membership, allowing order changes within each.
    key=lambda p:json.dumps(p,sort_keys=True,separators=(',',':'))
    for kind in matches:
        matches[kind]=all(sorted(map(key,got[s]))==sorted(map(key,r[kind][s])) for s in ['train','test'])
    if not any(matches.values()):
        diffs=[]
        for split in ['train','test']:
            expected=r['teaching_fixture'][split]
            if len(got[split])!=len(expected):diffs.append({'split':split,'expected_pairs':len(expected),'actual_pairs':len(got[split])})
            for i,(a,b) in enumerate(zip(got[split],expected)):
                for field in ['input','output']:
                    if a[field]==b[field]:continue
                    cells=[]
                    if len(a[field])==len(b[field]) and all(len(x)==len(y) for x,y in zip(a[field],b[field])):
                        cells=[{'row':y,'col':x,'actual':v,'expected':b[field][y][x]} for y,row in enumerate(a[field]) for x,v in enumerate(row) if v!=b[field][y][x]][:30]
                    diffs.append({'split':split,'pair':i,'field':field,'actual_shape':[len(a[field]),len(a[field][0])],
                                  'expected_shape':[len(b[field]),len(b[field][0])],'cell_mismatches':cells})
        raise ValueError(json.dumps({'reason':'validate() does not reproduce original fixture','details':diffs[:12]}))
    errors=[];shapes=set();seen=set();changed=0;replays=0;passed=0;attempted=0
    canonical_inputs={key(p['input']) for p in pairs(r['canonical'])}
    for seed in range(seed_start,seed_start+samples):
        attempted+=1
        random.seed(seed);np.random.seed(seed)
        try:
            if tid in CONTEXTUAL_TASK_IDS:
                episode=call(m.generate_episode,seconds=3)
                call(verify_shared_picture_episode,episode,seconds=3)
                raw=episode['test'][0]
            else:
                raw=call(m.generate,seconds=3)
            p={k:grid(raw[k]) for k in ['input','output']}
            if tid not in CONTEXTUAL_TASK_IDS:
                actual=grid(call(f,p['input'],seconds=3))
                if actual!=p['output']:
                    raise ValueError(json.dumps({'reason':'reference_disagreement','input':p['input'],'candidate':p['output'],'reference':actual}))
            seen.add(key(p['input']));changed+=p['input']!=p['output'];replays+=key(p['input']) in canonical_inputs
            shapes.add((len(p['input']),len(p['input'][0]),len(p['output']),len(p['output'][0])))
            passed+=1
        except Exception as e:
            errors.append({'seed':seed,'error':str(e)[:16000]})
            if len(errors)>=3:break
    basis=fixture_basis(tid,r)
    ready=not errors and len(seen)>=20 and changed>=20 and replays<=samples//10 and matches[basis['fixture']] and original[basis['fixture']]['all_exact']
    return {'task_id':tid,'ready':ready,'samples_requested':samples,'samples_attempted':attempted,'samples_passed':passed,
            'verifier_mode':'demonstration_conditioned_episode' if tid in CONTEXTUAL_TASK_IDS else 'archived_pair_solver',
            'seed_start':seed_start,'seed_end_exclusive':seed_start+attempted,
            'fixture_basis':basis,'unique_inputs':len(seen),'changed_pairs':changed,'fixture_replays':replays,
            'shapes':[list(s) for s in sorted(shapes)],'fixture_matches':matches,'original_solver_replay':original,
            'errors':errors,'sha256':hashlib.sha256(source.encode()).hexdigest(),
            'status':'validated_candidate_needs_semantic_review' if ready else 'needs_repair',
            'limitations':'Bounded randomized agreement with a saved solver is not proof of semantic completeness.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('task_id');ap.add_argument('path',type=Path);ap.add_argument('--samples',type=int,default=300);ap.add_argument('--seed-start',type=int,default=0);a=ap.parse_args()
    try:r=validate(a.task_id,a.path,a.samples,a.seed_start)
    except Exception as e:r={'task_id':a.task_id,'ready':False,'errors':[{'error':str(e),'traceback':traceback.format_exc()}]}
    print(json.dumps(r,separators=(',',':')))

if __name__=='__main__':main()
