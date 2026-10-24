"""Batch-3 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: ladder_rules_a1aa0c1e.py N [SEED]

Builds the certified direct-factory program for a1aa0c1e (d4=0, identity palette)
and evaluates its two internal readings, length RANK (mode 0, the native
constructor rule, task lines 66-76) and RUNG count (mode 1), on N native draws
and on the canonical fixture pairs. Reports how often the two readings give
different outputs, i.e. how often a single pair can separate them. The factory's
solve() raises when demonstrations leave the query unresolved, and admission
resamples the demonstration context instead.
"""
import sys, random
sys.path.insert(0, '.')
from arc_agi2 import runtime
from arc_agi2.direct_factories import task_a1aa0c1e as fac
from tasks import task_a1aa0c1e as m

n = int(sys.argv[1])
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
ns = {}
exec(fac.build_program(0, list(range(10))), ns)
pred = ns["_predict"]
can = runtime.reference("a1aa0c1e")["canonical"]
fx = [(pred(p["input"], 0) == p["output"], pred(p["input"], 1) == p["output"])
      for p in can["train"] + can["test"]]
print("canonical pairs (rank matches, rungs matches):", fx)
differ = rank_ok = 0
for _ in range(n):
    p = m.generate()
    a, b = pred(p["input"], 0), pred(p["input"], 1)
    rank_ok += a == p["output"]
    differ += a != b
print(f"native draws {n}: rank reading == native output {rank_ok}/{n}; "
      f"rank and rung readings differ on {differ}/{n}")
