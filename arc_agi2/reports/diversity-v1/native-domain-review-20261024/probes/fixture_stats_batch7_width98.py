"""Batch-7 follow-up probe: 98c475bf at independent widths. Read-only.

Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch7_width98.py

The constructor pins WIDTH = 20 (tasks/task_98c475bf.py line 54). Its
decorations sit at absolute x, up to x = 16, so they fit on any width of 18
or more. Hypothesis tested: the canvas width may vary independently,
provided the demonstrations and the query of one episode share it. That is
the canonical uniform/seen profile, and the factory and gate enforce it.

The module global WIDTH is set temporarily to 18, 20 (control), 24 and 30 and
restored in a finally block. No source file is changed. For each width,
heights are 20 and 100 queries are drawn up front and held fixed. For each
query, contexts of 3 demonstrations at the same width are redrawn until the
production gate accepts, at most 64 tries.

Checks on accepted episodes, against the constructor label:
  * the archived verifier (runtime.verification_solver, the pair check prepare
    applies);
  * motif_context.solve_demonstrated_motifs, which learns templates from
    demonstrations only and has no colour table;
  * line_motif_evidence.solve_visible_motifs, the production gate's own
    prediction;
  * the certified factory program (certified_factory_source, d4 = 0).
Then the first 20 accepted episodes per width run under all 8 D4 transforms
with the identity palette and one fixed non-identity palette. Gate and
program are compared with the transformed label. The archived verifier and
motif_context only read horizontal lines, so they are reported at d4 = 0.

A cross-width negative check gives each width-20 query width-24
demonstrations, and each width-24 query width-20 ones. Gate and program must
both refuse, because a novel width leaves anchoring undetermined.

Seeds are fixed (2509 * 100 + width), so output is byte-identical between runs.
"""
import random
import sys

sys.path.insert(0, '.')
from arc_agi2 import runtime  # noqa: E402
from arc_agi2.augmentation import transformed  # noqa: E402
from arc_agi2.colour_evidence import require_colour_evidence  # noqa: E402
from arc_agi2.direct_certificates import certified_factory_source  # noqa: E402
from arc_agi2.line_motif_evidence import solve_visible_motifs  # noqa: E402
from arc_agi2.motif_context import solve_demonstrated_motifs  # noqa: E402

import tasks.task_98c475bf as m  # noqa: E402

TID = '98c475bf'
WIDTHS = (18, 20, 24, 30)
QUERIES = 100
D4_QUERIES = 20
TRIES = 64
HEIGHT = 20
ID = list(range(10))
PAL = [0, 3, 7, 1, 9, 2, 8, 5, 4, 6]   # fixed bijection with 0 kept as background


def prog(d4, palette):
  ns = {}
  exec(certified_factory_source(TID, d4, palette), ns)
  return lambda g, demos: [list(map(int, r)) for r in ns['solve'](list(demos), g)]


def safe(fn, *a):
  try:
    return runtime.call(fn, *a, seconds=5)
  except Exception as exc:  # noqa: BLE001
    return exc


def gate_ok(demos, query, palette, d4=0):
  try:
    require_colour_evidence(TID, demos, [query], palette, d4)
    return True
  except Exception:  # noqa: BLE001
    return False


def at_width(w, fn):
  old = m.WIDTH
  m.WIDTH = w
  try:
    return fn()
  finally:
    m.WIDTH = old


def episodes(w):
  random.seed(2509 * 100 + w)
  queries = [m.generate(height=HEIGHT) for _ in range(QUERIES)]
  accepted, retries, failures = [], 0, 0
  for q in queries:
    for t in range(TRIES):
      demos = [m.generate(height=HEIGHT) for _ in range(3)]
      if gate_ok(demos, q, ID):
        accepted.append((demos, q))
        retries += t
        break
    else:
      failures += 1
      retries += TRIES
  return accepted, retries, failures


print('== 98c475bf independent width, same-width episodes (module WIDTH set temporarily)')
assert m.WIDTH == 20
verifier = runtime.verification_solver(TID)
p0 = prog(0, ID)
EP = {}
for w in WIDTHS:
  acc, retries, failures = at_width(w, lambda: episodes(w))
  EP[w] = acc
  ver = ctx = gate = fac = 0
  for demos, q in acc:
    want = q['output']
    ver += safe(lambda g: runtime.grid(verifier(g)), q['input']) == want
    ctx += safe(solve_demonstrated_motifs, demos, q['input']) == want
    gate += safe(solve_visible_motifs, demos, q['input'], 0) == want
    fac += safe(p0, q['input'], demos) == want
  shapes = sorted({(len(q['input']), len(q['input'][0])) for _, q in acc})
  n = len(acc)
  print(f'  width {w}: accepted {n}/{QUERIES} fixed queries, demo retries {retries}, failures {failures}, '
        f'shapes {shapes}; archived verifier {ver}/{n}, motif_context {ctx}/{n}, gate prediction {gate}/{n}, '
        f'factory {fac}/{n}')
assert m.WIDTH == 20

print()
print(f'== all 8 D4 x 2 palettes on the first {D4_QUERIES} accepted episodes per width (gate and factory)')
for w in WIDTHS:
  gate = fac = total = 0
  for palette in (ID, PAL):
    for d4 in range(8):
      p = prog(d4, palette)
      for demos, q in EP[w][:D4_QUERIES]:
        tdemos = [{'input': transformed(d['input'], d4, palette),
                   'output': transformed(d['output'], d4, palette)} for d in demos]
        tq = transformed(q['input'], d4, palette)
        want = transformed(q['output'], d4, palette)
        total += 1
        gate += gate_ok(tdemos, {'input': tq}, palette, d4) and \
            safe(solve_visible_motifs, tdemos, tq, palette[0]) == want
        fac += safe(p, tq, tdemos) == want
  print(f'  width {w}: gate accepted and exact {gate}/{total}, factory exact {fac}/{total}')

print()
print('== cross-width negative check (demonstrations at another width must be refused)')
for qw, dw in ((20, 24), (24, 20)):
  refused_gate = refused_prog = total = 0
  for (_, q), (demos, _) in zip(EP[qw][:D4_QUERIES], EP[dw][:D4_QUERIES]):
    total += 1
    refused_gate += not gate_ok(demos, q, ID)
    refused_prog += isinstance(safe(p0, q['input'], demos), Exception)
  print(f'  query width {qw}, demo width {dw}: gate refused {refused_gate}/{total}, factory raised {refused_prog}/{total}')
print(f'  module WIDTH after probe: {m.WIDTH}')
