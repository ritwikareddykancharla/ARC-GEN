"""Approve size overrides only after original replay and differential seed tests."""
import ast,concurrent.futures as cf,importlib,json,random
from .runtime import BASE,solver,check_reference,call,grid
IDS='0c9aba6e 15113be4 195ba7dc 281123b4 319f2597 31d5ba1a 34b99a2b 3d31c5b3 465b7d93 506d28a5 5d2a5c43 626c0bcc 66f2d22f 6a11f6da 996ec1f3 d19f7514 d304284e e133d23d e2092e0c e345f17b e99362f0 ea9794b1'.split()
def check(tid):
    mod=importlib.import_module('tasks.task_'+tid);f=solver(tid)
    if not check_reference(tid)['canonical']['all_exact']:return tid,{'approved':[],'reason':'reference does not reproduce canonical fixtures'}
    import inspect
    defaults={k:v.default for k,v in inspect.signature(mod.generate).parameters.items() if k in ['height','width','size'] and type(v.default)==int}
    candidates=[]
    if 'size' in defaults:candidates=[{'size':i} for i in [6,8,10,12,15,18,21,24,27,30] if i!=defaults['size']]
    elif 'width' in defaults and 'height' in defaults:candidates=[{'width':w,'height':h} for h,w in [(4,6),(6,8),(8,10),(10,12),(12,14),(14,20),(20,14),(21,24),(24,27),(27,30)]]
    approved=[];rejected=[]
    for kw in candidates:
        errors=[];shapes=set()
        for seed in range(12):
            random.seed(20261021+seed)
            try:
                p=call(mod.generate,seconds=.6,**kw);grid(p['input']);grid(p['output'])
                if grid(call(f,p['input'],seconds=.6))!=p['output']:raise ValueError('reference disagreement')
                shapes.add((len(p['input']),len(p['input'][0]),len(p['output']),len(p['output'][0])))
            except Exception as e:errors.append(type(e).__name__);break
        if errors:rejected.append({'parameters':kw,'errors':errors})
        else:approved.append({'parameters':kw,'tested_seeds':12,'shapes':sorted(shapes)})
    return tid,{'approved':approved,'rejected':rejected,'scope':'Bounded differential validation against saved solver; original replay passed.'}
def main():
    with cf.ProcessPoolExecutor(max_workers=4) as pool:result=dict(pool.map(check,IDS))
    (BASE/'reports/parameter-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Approved families',sum(bool(x['approved']) for x in result.values()),'configurations',sum(len(x['approved']) for x in result.values()),flush=True)
if __name__=='__main__':main()
