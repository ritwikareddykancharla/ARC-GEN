"""Fixed queries; resample demonstrations only; no target-aware context selection."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path
from tasks.task_973e499e import generate
from arc_agi2.runtime import BASE,reference,verification_solver,grid
from arc_agi2.episode_shape_policy import profile_from_task,select_demonstrations
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.colour_evidence import require_colour_evidence,MissingColourEvidence
from arc_agi2.program_targets import make_record
from arc_agi2.augmentation import transformed
from arc_agi2.self_match_evidence import candidate_predictions


def main():
    started=time.monotonic();rng=random.Random(2026102506)
    random.seed(2026102506)
    profile=profile_from_task(reference('973e499e')['canonical'])
    checker=verification_solver('973e499e');rows=[];failures=Counter();shapes=Counter();checks=0
    for index in range(1000):
        q=generate();qh=input_orbit(q['input']);fixed=json.dumps(q['input'])
        assert grid(checker(q['input']))==q['output']
        shapes[f"{len(q['input'])}x{len(q['input'][0])}"]+=1
        accepted=False
        for attempt in range(64):
            pool=[]
            for _ in range(32):
                p=generate();h=input_orbit(p['input'])
                if h!=qh:p['canonical_input_hash']=h;pool.append(p)
            ds,sr=select_demonstrations(pool,q['input'],rng,profile,'canonical_input_hash')
            if not ds or not sr['matched']:
                failures['context_shape_support']+=1;continue
            assert len({qh,*[d['canonical_input_hash'] for d in ds]})==4
            pal=list(range(10));rng.shuffle(pal)
            try:
                for d4 in range(8):
                    demos=[{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in ds]
                    query={'input':transformed(q['input'],d4,pal)}
                    require_colour_evidence('973e499e',demos,[query],pal,d4)
            except MissingColourEvidence:
                failures['demonstration_ambiguity']+=1;continue
            # Read the query answer only after every admission decision passed.
            for d4 in range(8):
                demos=[{k:transformed(p[k],d4,pal) for k in ('input','output')} for p in ds]
                qi=transformed(q['input'],d4,pal);answer=transformed(q['output'],d4,pal)
                assert candidate_predictions(demos,qi)=={tuple(map(tuple,answer))}
                ep=dict(episode_id=f'self-match-audit-{index:04d}-{d4}',task_id='973e499e',
                        train=demos,test=[dict(input=qi)],solutions=[answer],
                        d4_transform=d4,color_permutation=pal)
                assert make_record(ep,source_repo='ritwikareddykancharla/ARC-GEN',
                                   source_revision='self-match-context-audit')['verification']['all_exact']
                checks+=1
            accepted=True;break
        assert json.dumps(q['input'])==fixed
        rows.append(dict(query=index,accepted=accepted,attempts=attempt+1,input_orbit=qh))
        if (index+1)%100==0:print(json.dumps(dict(queries=index+1,accepted=sum(x['accepted'] for x in rows),checks=checks)),flush=True)
    files=['tasks/task_973e499e.py','arc_agi2/self_match_evidence.py','arc_agi2/colour_evidence.py',
           'arc_agi2/direct_factories/task_973e499e.py','arc_agi2/direct_factories/973e499e.json',
           'arc_agi2/program_targets.py','arc_agi2/diversity/prepare.py','arc_agi2/episode_shape_policy.py',
           str(Path(__file__).resolve().relative_to(BASE.parent))]
    report=dict(fixed_queries=1000,accepted_queries=sum(x['accepted'] for x in rows),
                augmented_record_checks=checks,rejections=dict(failures),shapes=dict(shapes),queries=rows,
                seconds=time.monotonic()-started,
                source_hashes={f:hashlib.sha256((BASE.parent/f).read_bytes()).hexdigest() for f in files},
                limitations='Finite equal/unequal/all, colour-source and orientation competitors only; not universal identifiability.')
    (Path(__file__).parent/'context-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['accepted_queries']==1000 and checks==8000

if __name__=='__main__':main()
