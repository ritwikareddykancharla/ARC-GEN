"""Distance and tie evidence across geometry and palette transformations."""
import random
import unittest

from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.nearest_marker_evidence import marker_candidates
from arc_agi2.program_targets import compile_target, verify
from tasks import task_6df30ad6 as task


class NearestMarkerEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]

    def explicit(self,shape,markers):
        return task.generate(height=14,width=14,shape=shape,markers=markers)

    def translated(self,pair):
        # New visible scene with the same geometric relation and new colours.
        g=pair['input'];shape=[];markers=[]
        for r,row in enumerate(g):
            for c,v in enumerate(row):
                if v==5:shape.append((r+1,c+1))
                elif v:markers.append((r+1,c+1,{1:3,2:4}.get(v,v)))
        return self.explicit(shape,markers)

    def check(self,demos,query,accept):
        for d4 in range(8):
            ds=apply_episode(demos,d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                if accept:
                    require_colour_evidence('6df30ad6',ds,[payload],self.palette,d4)
                else:
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence('6df30ad6',ds,[payload],self.palette,d4)

    def test_tie_query_requires_evidence_not_assumed_majority(self):
        query=self.explicit([(4,5),(5,5)],[(1,2,1),(4,2,2),(7,2,2)])
        self.assertEqual(query['output'][4][5],1)
        self.assertEqual(marker_candidates(query['input'],list(range(10)))[8],2)
        weak=self.explicit([(5,5),(6,5)],[(5,3,1),(10,10,2)])
        self.check([weak],query,False)
        self.check([weak,self.translated(query)],query,True)

    def test_primary_metric_must_be_demonstrated(self):
        query=self.explicit([(5,5),(6,5)],[(2,2,1),(5,9,2)])
        candidates=marker_candidates(query['input'],list(range(10)))
        self.assertEqual(candidates[0],1)
        self.assertEqual(candidates[32],2)
        self.assertEqual(candidates[64],2)
        weak=self.explicit([(5,5),(6,5)],[(5,3,1),(10,10,2)])
        self.check([weak],query,False)
        self.check([weak,self.translated(query)],query,True)

    def test_canonical_query_and_all_d4_hypothesis_sets(self):
        data=task.validate()
        self.check(data['train'],data['test'][0],True)
        random.seed(106400)
        for pair in data['train']+[task.generate() for _ in range(25)]:
            colours=set(marker_candidates(pair['input'],list(range(10))))
            for d4 in range(8):
                augmented=apply_episode([pair],d4,self.palette)[0]
                self.assertEqual(set(marker_candidates(augmented['input'],self.palette)),
                                 {self.palette[v] for v in colours})

    def test_emitted_target_matches_explicit_ties_in_all_orientations(self):
        random.seed(91872)
        shape=[(5,5),(6,5)]
        positions=[(r,c) for r in range(1,12) for c in range(1,12)
                   if min(max(abs(r-y),abs(c-x)) for y,x in shape)==3]
        pairs=[]
        for _ in range(40):
            markers=[]
            for r,c in random.sample(positions,len(positions)):
                if all(abs(r-y)+abs(c-x)>1 for y,x,v in markers):
                    markers.append((r,c,random.choice([1,2,3])))
                if len(markers)==5:break
            pairs.append(self.explicit(shape,markers))
        for d4 in range(8):
            transformed=apply_episode(pairs,d4,self.palette)
            episode=dict(train=transformed[:3],test=[{'input':p['input']} for p in transformed[3:]],
                         solutions=[p['output'] for p in transformed[3:]])
            verify(compile_target('6df30ad6',d4,self.palette)[0],episode)

    def test_corrupt_shape_or_unerased_markers_are_rejected(self):
        data=task.validate()
        p=data['train'][0]
        corrupt=dict(input=p['input'],output=p['input'])
        self.check([corrupt],data['test'][0],False)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('6df30ad6',[],[{'input':p['input']}])


if __name__=='__main__':unittest.main()
