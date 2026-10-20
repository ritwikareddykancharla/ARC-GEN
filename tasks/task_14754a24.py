# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC task 14754a24: complete yellow plus-sign fragments with red.

The input is a noisy field of grey (5) and black (0) cells. It also holds a
few small yellow (4) clusters. Each cluster is part of a 5-cell plus sign:
a centre and its four orthogonal arms. The missing cells of that plus are
grey in the input. In the output they turn red (2). A plus centred on the
border may be clipped by the edge. Clipped cells are simply absent.

Ambiguity is resolved by black cells. A plus is a valid completion only when
all of these hold:
  * its in-grid cells contain the whole yellow cluster;
  * none of its in-grid cells is black.
The generator builds latent plus centres and yellow fragments. It requires
each fragment to be 8-connected, to have at least 2 cells, and to have at
least 1 missing in-grid cell. It then inserts black cells into every
competing candidate plus, so the intended centre is the only valid one.

Scope: grid sizes 12..30 per side, grey density 0.4..0.6, 2..12 plus
fragments. Fragments may or may not include the centre, and border-clipped
pluses are allowed. Colours (0/5 field, 4 yellow, 2 red) are fixed, as in
the task.
"""

import itertools
import random

import common


def _plus(r, c):
  return [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]


def _inside(cells, h, w):
  return [(y, x) for (y, x) in cells if 0 <= y < h and 0 <= x < w]


def _connected8(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        n = (y + dy, x + dx)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _components8(g, color):
  h, w = len(g), len(g[0])
  seen = set()
  comps = []
  for y in range(h):
    for x in range(w):
      if g[y][x] != color or (y, x) in seen:
        continue
      comp = []
      stack = [(y, x)]
      seen.add((y, x))
      while stack:
        cy, cx = stack.pop()
        comp.append((cy, cx))
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and g[ny][nx] == color:
              if (ny, nx) not in seen:
                seen.add((ny, nx))
                stack.append((ny, nx))
      comps.append(frozenset(comp))
  return comps


def _candidates(g, frag, h, w):
  """Centres of black-free in-grid pluses containing the whole fragment."""
  cs = set(frag)
  cands = set()
  for (cy, cx) in cs:
    for (ey, ex) in _plus(cy, cx):
      inside = _inside(_plus(ey, ex), h, w)
      if not cs <= set(inside):
        continue
      if any(g[y][x] == 0 for (y, x) in inside):
        continue
      cands.add((ey, ex))
  return cands


def _fragment_options(r, c, h, w):
  cells = _inside(_plus(r, c), h, w)
  opts = []
  for k in range(2, len(cells)):
    for sub in itertools.combinations(cells, k):
      if _connected8(sub):
        opts.append(list(sub))
  return opts


def _place(h, w, num_pluses):
  if num_pluses is None:
    num_pluses = random.randint(3, min(12, max(3, (h * w) // 40)))
  plan = []
  for _ in range(num_pluses):
    for _ in range(100):
      if random.random() < 0.8:
        r, c = random.randint(1, h - 2), random.randint(1, w - 2)
      else:
        r, c = random.randint(0, h - 1), random.randint(0, w - 1)
      if any(max(abs(r - pr), abs(c - pc)) < 4 for pr, pc, _ in plan):
        continue
      opts = _fragment_options(r, c, h, w)
      if not opts:
        continue
      plan.append((r, c, random.choice(opts)))
      break
  return plan if len(plan) >= 2 else None


def _force_unique(g, plan, reserved, h, w):
  for r, c, frag in plan:
    for alt in sorted(_candidates(g, frag, h, w)):
      if alt == (r, c):
        continue
      inside = _inside(_plus(*alt), h, w)
      if any(g[y][x] == 0 for (y, x) in inside):
        continue
      options = [p for p in inside if p not in reserved]
      if not options:
        return False
      y, x = random.choice(options)
      g[y][x] = 0
  for r, c, frag in plan:
    if _candidates(g, frag, h, w) != {(r, c)}:
      return False
  return True


def generate(width=None, height=None, noise=None, pluses=None, density=None,
             num_pluses=None):
  """Returns a plus-completion example.

  Args:
    width: grid width (12..30 when sampled).
    height: grid height (12..30 when sampled).
    noise: optional grey/black field (rows of 0/5); fixes the grid size.
    pluses: optional list of (centre_row, centre_col, fragment_cells), where
      fragment_cells are the absolute (row, col) yellow cells.
    density: probability of grey in the sampled noise field (0.4..0.6).
    num_pluses: number of plus fragments to try to place.
  """
  if noise is not None:
    height, width = len(noise), len(noise[0])
  for _ in range(300):
    h = height if height is not None else random.randint(12, 30)
    w = width if width is not None else random.randint(12, 30)
    if noise is not None:
      g = [[5 if v != 0 else 0 for v in row] for row in noise]
    else:
      p = density if density is not None else random.uniform(0.4, 0.6)
      g = common.grid(w, h, 0)
      for y in range(h):
        for x in range(w):
          g[y][x] = 5 if random.random() < p else 0
    if pluses is not None:
      plan = [(r, c, [tuple(q) for q in cells]) for r, c, cells in pluses]
    else:
      plan = _place(h, w, num_pluses)
      if plan is None:
        continue
    reserved = set()
    for r, c, frag in plan:
      fset = set(frag)
      for (y, x) in _inside(_plus(r, c), h, w):
        g[y][x] = 4 if (y, x) in fset else 5
        reserved.add((y, x))
    if pluses is None:
      if not _force_unique(g, plan, reserved, h, w):
        continue
      comps = set(_components8(g, 4))
      if comps != {frozenset(f) for _, _, f in plan}:
        continue
    out = [row[:] for row in g]
    for r, c, frag in plan:
      fset = set(frag)
      for (y, x) in _inside(_plus(r, c), h, w):
        if (y, x) not in fset:
          out[y][x] = 2
    return {"input": g, "output": out}
  raise RuntimeError("could not build a valid scene")


def _decode(rows):
  return [[0 if ch == "0" else 5 for ch in row] for row in rows]


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  t1 = ["055400000005555", "004005545005055", "505000445055505",
        "500505540005505", "550505000550050", "050050550055500",
        "550550050000000", "554050500505055", "545405504545050",
        "555005500405055", "000500000000505", "050050500550500",
        "000005055000005", "050055550505000"]
  p1 = [(0, 2, [(1, 2), (0, 3)]),
        (2, 7, [(1, 7), (2, 6), (2, 7), (3, 7)]),
        (8, 2, [(7, 2), (8, 1), (8, 3)]),
        (8, 9, [(8, 8), (8, 10), (9, 9)])]
  t2 = ["0500550005505005", "5500005050055500", "0045050550045550",
        "0554005005004005", "0045005050000050", "0005055550505505",
        "5050045455550500", "0000554550000005", "0055005055055450",
        "0050050005505545", "5004000050000555", "5545450555000055",
        "5005550545405000", "5005500504000550", "5555500055505500",
        "5555000050555505", "5050000050505500", "5000050055550005"]
  p2 = [(3, 2, [(2, 2), (3, 3), (4, 2)]),
        (2, 12, [(2, 11), (3, 12)]),
        (6, 6, [(6, 5), (6, 7), (7, 6)]),
        (9, 13, [(8, 13), (9, 14)]),
        (11, 3, [(10, 3), (11, 2), (11, 4)]),
        (12, 9, [(12, 8), (12, 10), (13, 9)])]
  t3 = ["005000000500500", "050005550550555", "005000550500555",
        "555450004450505", "054500000505005", "505050000005505",
        "000505000000055", "550055050550000", "505005554500050",
        "045500545555000", "054505550000505", "005000550050500",
        "005000000050555", "000555050055050"]
  p3 = [(3, 2, [(3, 3), (4, 2)]),
        (3, 9, [(3, 8), (3, 9)]),
        (8, 7, [(8, 8), (9, 7)]),
        (9, 2, [(9, 1), (10, 2)])]
  t4 = ["0505505550005005050", "0005000555000055000",
        "0550005055000050050", "0055055005505050500",
        "0050040505050005505", "0050454550500054555",
        "5000040055000054450", "5055550500050504500",
        "5500505055055555000", "5500555050050050000",
        "0055000054505500000", "5554050554450055550",
        "0045005504505005555", "0000500500005050055",
        "5505000555550500000", "5500050000000505005",
        "5050550550000550000", "0550000005555500000"]
  p4 = [(5, 5, [(4, 5), (5, 4), (5, 6), (6, 5)]),
        (6, 15, [(5, 15), (6, 15), (6, 16), (7, 15)]),
        (11, 9, [(10, 9), (11, 9), (11, 10), (12, 9)]),
        (11, 2, [(11, 3), (12, 2)])]
  te = ["0050055050505545005", "0550545550550450550",
        "5550554055055550505", "5540000500050500055",
        "5455550500550550500", "5505000550545005055",
        "0555505555445055000", "5005555000050550050",
        "0500000500500050505", "0000500500500500550",
        "0000550505050400050", "5545555500504540505",
        "5554000555055405555", "0045000005050555555",
        "5050050450055555005", "5505505540055505055",
        "5550555405505500550", "5555000500505050500",
        "0505550055500555555"]
  pe = [(0, 13, [(0, 14), (1, 13)]),
        (1, 6, [(1, 5), (2, 6)]),
        (3, 1, [(3, 2), (4, 1)]),
        (6, 11, [(5, 11), (6, 10), (6, 11)]),
        (11, 13, [(10, 13), (11, 12), (11, 14), (12, 13)]),
        (12, 2, [(11, 2), (12, 3), (13, 2)]),
        (15, 7, [(14, 7), (15, 8), (16, 7)])]
  train = [generate(noise=_decode(t), pluses=p)
           for t, p in ((t1, p1), (t2, p2), (t3, p3), (t4, p4))]
  test = [generate(noise=_decode(te), pluses=pe)]
  return {"train": train, "test": test}
