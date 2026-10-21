"""Audit only: proposed six-cell copy, native random labels, canonical untouched."""
import hashlib,json,random,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import audit
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=audit.load(audit.FORK/'tasks/task_963c33f8.py','native963')
factory=audit.load(HERE.parent/'factory.py','factory963').build_program

def independent(g):
    """Scalar row scan, independent of emitted visible-coordinate target."""
    H,W=len(g),len(g[0]);out=[row[:] for row in g]
    cols=[c for c in range(W) if g[0][c]==9]
    assert len(cols)==3 and cols==list(range(min(cols),max(cols)+1))
    for c in cols:
        assert [g[r][c] for r in range(3)] in ([9,9,9],[9,9,1])
        for r in range(3):out[r][c]=7
    for c in cols:
        if g[2][c]==9:
            for x in range(max(0,c-2),min(W,c+3)):out[-1][x]=7
    for c in cols:
        stop=H-1
        if g[2][c]==1:stop=next((r-1 for r in range(3,H) if out[r][c]==5),H-1)
        for j in range(3):out[stop-2+j][c]=g[j][c]
    return out

def diffs(a,b):
 return [dict(part=s,pair_index=i,row=r,col=c,old=x,new=b[s][i]['output'][r][c]) for s in ['train','test'] for i,p in enumerate(a[s]) for r,row in enumerate(p['output']) for c,x in enumerate(row) if x!=b[s][i]['output'][r][c]]

r=dict(task_id='963c33f8',status='audit-only proposed six-cell teaching copy preserving floor clear; not admitted',fresh_pairs_checked=0,augmented_pair_checks=0,fixture_variants_checked=0,passed=False,factory_sha256=sha(HERE.parent/'factory.py'),native_constructor_sha256=sha(Path(native.__file__)))
start=time.monotonic();seen=set()
try:
 ref=audit.reference('963c33f8');task=ref['canonical']
 proposal={s:[dict(input=p['input'],output=independent(p['input'])) for p in task[s]] for s in ['train','test']}
 assert len(diffs(task,proposal))==6
 for name,data in [('proposed-teaching-native-floor-clear',proposal),('canonical-snapshot',task),('existing-eight-cell-snapshot',ref['teaching_fixture']),('fixture-differences',dict(canonical_to_proposed_six=diffs(task,proposal),canonical_to_existing_eight=diffs(task,ref['teaching_fixture']),proposed_six_to_existing_eight=diffs(proposal,ref['teaching_fixture'])))]:
  (HERE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
 p=task['train'][1]
 (HERE/'floor-clear-visible-evidence.json').write_text(json.dumps(dict(pair_index=1,description='Canonical unlit column7 clears bottom row7..9 before landing, while columns10,11 stay gray. Zero-based coordinates. Supports floor-clear hypothesis but cannot rule out these two cells being erroneous.',input=p['input'],output=p['output'],bottom_row_observations=[dict(row=13,col=c,input=p['input'][13][c],output=p['output'][13][c]) for c in range(7,12)]),indent=2)+'\n')
 for pal in [list(range(10)),[3,9,0,7,2,8,1,6,4,5]]:
  for d4 in range(8):
   ep={'train':[{k:audit.transformed(p[k],d4,pal) for k in ['input','output']} for p in proposal['train']],'test':[{'input':audit.transformed(p['input'],d4,pal)} for p in proposal['test']],'solutions':[audit.transformed(p['output'],d4,pal) for p in proposal['test']]}
   source=factory(d4,pal);audit.audit_target('963c33f8',source);audit.verify(source,ep);r['fixture_variants_checked']+=1
 for batch in range(250):
  random.seed(963330000+batch);pairs=[audit.call(native.generate,seconds=10) for _ in range(4)]
  for p in pairs:assert independent(p['input'])==p['output'];seen.add(json.dumps(p['input']))
  pal=list(range(10));random.Random(batch+963).shuffle(pal)
  for d4 in range(8):
   source=factory(d4,pal);audit.audit_target('963c33f8',source);audit.verify(source,audit.episode(pairs,d4,pal));r['augmented_pair_checks']+=4
  r['fresh_pairs_checked']+=4
 r['canonical_cell_mismatches']=len(diffs(task,proposal));r['passed']=True
except Exception as exc:r['error']=repr(exc)
r.update(unique_base_inputs=len(seen),seconds=time.monotonic()-start)
(HERE/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if not r['passed']:raise SystemExit(1)
