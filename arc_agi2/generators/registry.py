"""Candidate constructors. Eligibility additionally requires a passing audit."""
import random
from .extended import GENERATORS as INITIAL
from .coverage_batch1 import GENERATORS as COVERAGE
from .coverage_batch2 import GENERATORS as COVERAGE2

GENERATORS={**INITIAL,**COVERAGE,**COVERAGE2}

def generate(tid,seed=0,**kwargs):
    return GENERATORS[tid](random.Random(seed),**kwargs)
