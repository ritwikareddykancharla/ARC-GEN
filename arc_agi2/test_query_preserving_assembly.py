"""Evidence retries change demonstrations, not the selected query difficulty."""
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from . import build_million as builder
from .colour_evidence import MissingColourEvidence, require_colour_evidence
from tasks import task_bd283c4a as task


class QueryPreservingAssemblyTests(unittest.TestCase):
    def run_assembly(self,reject_count):
        rows=[];tid='bd283c4a'
        for seed in range(8):
            values=[1]*49+[2]*31+[3]*15+[4]*5
            random.Random(seed).shuffle(values)
            p=task.generate(colors=values)
            rows.append(dict(task_id=tid,**p,seed=seed,parameters='{}',
                generator_mode='standalone_constructor',input_hash=builder.digest(p['input']),
                canonical_input_hash=builder.canonical_input(p['input']),split='train',stratum=builder.stratum(p)))
        seen=[];demo_sets=[]
        def gate(task_id,demos,queries,*args,**kwargs):
            self.assertNotIn('output',queries[0])
            seen.append(builder.digest(queries[0]['input']))
            demo_sets.append(tuple(sorted(builder.digest(d['input']) for d in demos)))
            if len(seen)<=reject_count:raise MissingColourEvidence('test: more teaching evidence needed')
            return require_colour_evidence(task_id,demos,queries,*args,**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'pools').mkdir()
            builder.pq.write_table(builder.pa.Table.from_pylist(rows),root/'pools'/f'{tid}.parquet')
            with patch.object(builder,'OUT',root),patch.object(builder,'OUTPUT_FORMAT','grid-pool'),patch.object(builder,'require_colour_evidence',side_effect=gate):
                result=builder.make_episodes((tid,{'train':{rows[0]['stratum']:1}}))['splits']['train']
            if result['fresh_episodes']:
                saved=builder.pq.read_table(root/'data/train'/f'{tid}.parquet').to_pylist()
                native=next(r for r in saved if r['d4_transform']==0)
                inverse={v:k for k,v in enumerate(native['color_permutation'])}
                query=[[inverse[v] for v in row] for row in native['test'][0]['input']]
                self.assertEqual(builder.digest(query),seen[0])
        return result,seen,demo_sets

    def test_retries_keep_query_and_resample_demonstrations(self):
        result,seen,demos=self.run_assembly(3)
        self.assertEqual(result['fresh_episodes'],1)
        self.assertEqual(len(set(seen)),1)
        self.assertGreaterEqual(len(seen),4)
        self.assertGreater(len(set(demos)),1)
        self.assertEqual(result['query_context_shortfalls'],[])

    def test_failed_context_reports_shortfall_instead_of_easier_query(self):
        result,seen,_=self.run_assembly(100)
        self.assertEqual(result['fresh_episodes'],0)
        self.assertEqual(len(seen),50)
        self.assertEqual(len(set(seen)),1)
        self.assertEqual(result['query_context_shortfalls'],[
            dict(query_input_hash=seen[0],stratum='10|same_shape',context_attempts=50)])


if __name__=='__main__':unittest.main()
