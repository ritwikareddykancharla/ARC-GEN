"""Exercise proposed actual make_episodes AST with deterministic storage/model fakes.
No jobs, network, repository mutations, generation or model training.
"""
import ast, builtins, collections, copy, hashlib, importlib, json, pathlib, random, symtable, sys, tempfile, types, unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parent
from arc_agi2.colour_evidence import MissingColourEvidence,IntrinsicQueryEvidence,EvidenceSearchBudget,require_colour_evidence
from arc_agi2.augmentation import exhaustive_variants,demonstrations_disambiguate
# Real production helpers used by make_episodes; only storage, models and
# randomness are faked below.
from arc_agi2.finite_input_policy import (FAMILY_PROVENANCE,FINITE_INPUT_TASK_IDS,
    POLICY_SIGNATURE as FINITE_INPUT_POLICY_SIGNATURE,identity_key,input_split,minimum_class_requirement)
from arc_agi2.episode_shape_policy import profile_from_task,select_demonstrations,describe as describe_shapes
from arc_agi2.context_budget import reuse_limits,VERSION as CONTEXT_BUDGET_VERSION
from arc_agi2.runtime import call
from arc_agi2.contextual import verify_shared_picture_episode
from arc_agi2.motif_context import MissingMotifEvidence,solve_demonstrated_motifs
# Reached only by the legacy Parquet format or legend families, never by this
# PNG-format synthetic family; any other unsupplied global fails loudly.
UNREACHED_GLOBALS={'pa','legend_solver'}
class TargetError(ValueError):pass
class Writer:
    def __init__(self,*a):self.records=0;self.paths=[];self.manifest=[];self.items=[]
    def write(self,r):self.items.append(r);self.records+=1
    def abort(self):pass
    def close(self):pass
class FakeRandom:
    def __init__(self,*a):self.calls=0
    def shuffle(self,a):pass
    def choice(self,a):return a[0]
    def sample(self,a,n):
        self.calls+=1;offset=(self.calls-1)%len(a);return (a[offset:]+a[:offset])[:n]

def global_names(func):
    """Module-level names make_episodes needs, so harness drift fails explicitly."""
    table=symtable.symtable(ast.unparse(ast.Module(body=[func],type_ignores=[])),'make_episodes','exec')
    names=set();stack=[table]
    while stack:
        t=stack.pop();stack+=t.get_children()
        names|={s.get_name() for s in t.get_symbols() if s.is_global()}
    return {n for n in names if not hasattr(builtins,n)}

def assembly(gate,record=lambda row,**kw:{},n=1,output_poison=False,variants=exhaustive_variants,disambiguate=demonstrations_disambiguate):
    # Synthetic SHA-256 canonical hashes, split by the real global policy.
    rows=[{'input':[[i,0],[0,0]],'output':[[0,i],[0,0]],'input_hash':str(i),
           'canonical_input_hash':hashlib.sha256(f'test0000-canonical-{i}'.encode()).hexdigest(),
           'stratum':'small','seed':i,'parameters':{},'generator_mode':'default'} for i in range(1,7)]
    for row in rows:row['split']=input_split(row['canonical_input_hash'])
    assert all(row['split']=='train' for row in rows)
    fixture={'train':[{'input':r['input'],'output':r['output']} for r in rows[:3]],
             'test':[{'input':rows[3]['input'],'output':rows[3]['output']}]}
    if output_poison:rows[0]['output']=[[9,9],[9,9]]
    logs={};captured=[]
    def checked_gate(tid,demos,queries):
        assert list(queries[0])==['input']
        captured.append(copy.deepcopy((demos,queries)));return gate(tid,demos,queries)
    tree=ast.parse((HERE/'build_million.py').read_text())
    func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='make_episodes')
    # The production per-variant program check, which calls make_record.
    variant=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='verified_variant')
    with tempfile.TemporaryDirectory() as temp:
        env=dict(fixture_basis=lambda _: {'fixture':'canonical','corrected':False},
            pq=types.SimpleNamespace(read_table=lambda _:types.SimpleNamespace(to_pylist=lambda:copy.deepcopy(rows))),
            OUT=pathlib.Path(temp),defaultdict=collections.defaultdict,Counter=collections.Counter,
            random=types.SimpleNamespace(Random=FakeRandom),seed=lambda *a:0,OUTPUT_FORMAT='program-grid-png',VisualShardWriter=Writer,
            STORED_CONTEXT_TASK_IDS=set(),CONTEXTUAL_TASK_IDS=set(),LEGEND_TASK_IDS=set(),
            MissingColourEvidence=MissingColourEvidence,IntrinsicQueryEvidence=IntrinsicQueryEvidence,EvidenceSearchBudget=EvidenceSearchBudget,
            require_colour_evidence=checked_gate,digest=lambda a:json.dumps(a),compact=lambda a:json.dumps(a),
            POLICY={'augmentation':{'colour_permutation_default':False,'colour_permutation_task_ids':[]}},
            exhaustive_variants=variants,demonstrations_disambiguate=disambiguate,os=types.SimpleNamespace(environ={}),
            json=json,relation=lambda p:'same',make_record=record,TargetError=TargetError,
            dump=lambda path,obj:logs.update({str(path):copy.deepcopy(obj)}),
            reference=lambda _:{'canonical':copy.deepcopy(fixture)},
            identity_key=identity_key,input_split=input_split,minimum_class_requirement=minimum_class_requirement,
            FINITE_INPUT_TASK_IDS=FINITE_INPUT_TASK_IDS,FAMILY_PROVENANCE=FAMILY_PROVENANCE,
            FINITE_INPUT_POLICY_SIGNATURE=FINITE_INPUT_POLICY_SIGNATURE,
            profile_from_task=profile_from_task,select_demonstrations=select_demonstrations,describe_shapes=describe_shapes,
            reuse_limits=reuse_limits,CONTEXT_BUDGET_VERSION=CONTEXT_BUDGET_VERSION,
            call=call,verify_shared_picture_episode=verify_shared_picture_episode,
            MissingMotifEvidence=MissingMotifEvidence,solve_demonstrated_motifs=solve_demonstrated_motifs)
        missing=global_names(func)-set(env)-{'make_episodes','verified_variant'}-UNREACHED_GLOBALS
        assert not missing,f'make_episodes harness lacks production helpers: {sorted(missing)}'
        exec(compile(ast.Module(body=[variant,func],type_ignores=[]),'actual_proposed_make_episodes','exec'),env)
        result=env['make_episodes'](('test0000',{'train':{'small':n}}))
    return result['splits']['train'],captured,logs

class AssemblyTests(unittest.TestCase):
    def test_context_retries_same_query_not_same_demos(self):
        seen=[]
        def gate(t,d,q):
            seen.append(q[0]['input'])
            if len(seen)<3:raise MissingColourEvidence('thin context')
        result,calls,_=assembly(gate)
        self.assertEqual(len(calls),3);self.assertTrue(all(q==seen[0] for q in seen))
        self.assertNotEqual(calls[0][0],calls[1][0]);self.assertEqual(result['fresh_episodes'],1)
        self.assertEqual(result['failures']['missing_colour_evidence_attempts'],2)
    def test_intrinsic_query_not_retried(self):
        def gate(*a):raise IntrinsicQueryEvidence('latent tie',{'outputs':2})
        result,calls,_=assembly(gate)
        self.assertEqual(len(calls),1);self.assertEqual(result['quarantined_query_count'],1)
        self.assertEqual(result['query_context_shortfalls'],[])
        self.assertEqual(result['query_rejections'][0]['witness'],{'outputs':2})
    def test_intrinsic_query_never_revisited(self):
        def gate(t,d,q):
            if q[0]['input'][0][0]==1:raise IntrinsicQueryEvidence('latent tie')
        result,calls,_=assembly(gate,n=8)
        self.assertEqual(sum(q[0]['input'][0][0]==1 for d,q in calls),1)
    def test_budget_is_not_ambiguity(self):
        def gate(*a):raise EvidenceSearchBudget('exhausted')
        result,calls,_=assembly(gate)
        self.assertEqual(len(calls),1)
        self.assertEqual(result['query_rejections'][0]['kind'],'evidence_search_budget_exhausted')
    def test_program_mismatch_quarantines_all_orientations(self):
        records=[]
        def record(row,**kw):
            records.append(row)
            if len(records)==2:raise TargetError('Program not exact: [true, false]')
            return {}
        result,calls,logs=assembly(lambda *a:None,record)
        self.assertEqual(len(calls),1);self.assertEqual(len(records),2)
        self.assertEqual(result['episodes'],0);self.assertEqual(result['fresh_episodes'],0)
        self.assertEqual(result['query_rejections'][0]['kind'],'post_gate_program_rejected')
        self.assertEqual(result['query_context_shortfalls'],[])
        self.assertTrue(any('/rejections/train/test0000/1.json' in p for p in logs))
    def test_poison_answer_does_not_change_context_selection(self):
        def gate(t,d,q):pass
        def record(row,**kw):
            if row['solutions'][0]==[[9,9],[9,9]]:raise TargetError('query mismatch')
            return {}
        clean,cc,_=assembly(gate,record)
        poison,pc,_=assembly(gate,record,output_poison=True)
        self.assertEqual(cc,pc);self.assertEqual(len(pc),1)
        self.assertEqual(clean['fresh_episodes'],1);self.assertEqual(poison['fresh_episodes'],0)
    def test_augmented_label_conflict_never_retries_context(self):
        result,calls,_=assembly(lambda *a:None,disambiguate=lambda _:False)
        self.assertEqual(len(calls),1);self.assertEqual(result['query_rejections'][0]['kind'],'augmented_label_conflict')
    def test_unknown_gate_error_propagates(self):
        def gate(*a):raise RuntimeError('bug')
        with self.assertRaisesRegex(RuntimeError,'bug'):assembly(gate)
    def test_cap_shortfall_is_explicit(self):
        def gate(*a):raise MissingColourEvidence('missing prefix')
        result,calls,_=assembly(gate)
        self.assertEqual(len(calls),50);self.assertEqual(result['query_context_shortfalls'][0]['context_attempts'],50)
        self.assertEqual(result['quarantined_query_count'],0)

class TypedDispatchTests(unittest.TestCase):
    def test_c6_real_intrinsic_witness(self):
        from arc_agi2.test_slide_stack_c6e1b8da_evidence import SlideStackTests
        SlideStackTests("test_hidden_order_ambiguity_is_rejected").test_hidden_order_ambiguity_is_rejected()
        from arc_agi2.slide_stack_c6e1b8da_evidence import IntrinsicAmbiguity
        self.assertTrue(issubclass(IntrinsicAmbiguity,IntrinsicQueryEvidence))
    def test_b795_real_intrinsic_witness(self):
        from arc_agi2.test_occluded_boxes_b7955b3c_evidence import WITNESS,fixtures
        from tasks.task_b7955b3c import generate
        ds,_=fixtures();q=generate(bgcolor=4,**WITNESS)
        with self.assertRaises(IntrinsicQueryEvidence):require_colour_evidence('b7955b3c',ds,[{'input':q['input']}])
    def test_d5_classification(self):
        import arc_agi2.t_tally_d5c634a2_evidence as m
        for error,expect in [(m.MissingTTallyEvidence('query_t_cover_ambiguous',True),IntrinsicQueryEvidence),
                             (m.MissingTTallyEvidence('cover_search_limit',True),EvidenceSearchBudget),
                             (m.MissingTTallyEvidence('tally_prefix_2_unobserved'),m.MissingTTallyEvidence)]:
            with patch.object(m,'require_t_tally_evidence',side_effect=error):
                with self.assertRaises(expect):require_colour_evidence('d5c634a2',[],[{'input':[[0]]}])
    def test_docking_demo_vs_query(self):
        import arc_agi2.pixel_docking_evidence as m
        with patch.object(m,'_enumerate',return_value=[([[0]],None),([[1]],None)]):
            with self.assertRaises(IntrinsicQueryEvidence):m._require_native(None,'query',0)
            try:m._require_native(None,'demonstration',0)
            except MissingColourEvidence as exc:self.assertNotIsInstance(exc,IntrinsicQueryEvidence)
            else:self.fail('demo must reject')
        with patch.object(m,'require_evidence',side_effect=m.DockingSearchBudget('limit')):
            with self.assertRaises(EvidenceSearchBudget):require_colour_evidence('1b8318e3',[],[])
    def test_e048_f3e_context_failures_are_retryable(self):
        for tid,name in [('e048c9ed','bar_length_hypothesis_evidence'),('f3e14006','weave_hypothesis_evidence')]:
            m=importlib.import_module('arc_agi2.'+name)
            with patch.object(m,'gate',return_value={'status':'context_shortfall'}):
                with self.assertRaises(MissingColourEvidence):require_colour_evidence(tid,[],[{'input':[[0]]}])
    def test_standalone_hypothesis_gate_imports(self):
        import importlib.util
        for name in ('weave_hypothesis_evidence','bar_length_hypothesis_evidence'):
            path=HERE/(name+'.py')
            spec=importlib.util.spec_from_file_location('standalone_'+name,path)
            m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            with patch.object(m,'gate',return_value={'status':'context_shortfall'}):
                with self.assertRaises(MissingColourEvidence):m.require_evidence([], [{'input':[[0]]}],list(range(10)))
    def test_b198_unreadable_query_is_intrinsic(self):
        import arc_agi2.square_stack_hypothesis_evidence as m
        with patch.object(m,'features',side_effect=[None,ValueError('roles')]),patch.object(m,'render',return_value=[[0]]):
            with self.assertRaises(IntrinsicQueryEvidence):m.require_evidence([{'input':[[0]],'output':[[0]]}],[{'input':[[1]]}])
    def test_df8_context_vs_intrinsic(self):
        import arc_agi2.checkerboard_phase_evidence as m
        for status,expected in [('role_ambiguous',IntrinsicQueryEvidence),('phase_context_shortfall',MissingColourEvidence)]:
            with patch.object(m,'gate',return_value={'status':status}):
                with self.assertRaises(expected):require_colour_evidence('df8cc377',[],[{'input':[[0]]}])

if __name__=='__main__':unittest.main(verbosity=2)
