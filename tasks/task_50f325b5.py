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

"""ARC task 50f325b5: paint hidden green copies of the 8-template.

Rule: the grid is dense noise in colours 0, 2, 3, 4 and 7. It also holds one
small template shape drawn in colour 8. Look at every placement of that
template, in any rotation or reflection, whose cells are all green (3). Those
placements are repainted 8. Green cells next to a placement that are not part
of it stay 3.

Scope of the generator. These are sampled: the grid size (10-30 per side by
default, which is a synthetic extension of the fixture sizes 11-18), the
template shape (a connected shape of 4-6 cells inside a 3x3 box, mostly
4-connected and sometimes diagonally connected), the template position, the
number of hidden copies (1-3), their orientations and positions, the green
density of the noise, extra green 'padding' cells touching copies (as in
fixture pair 1), and near-miss distractors (a template orientation with one
cell knocked out).

The scene is then repaired so that the set of all-green placements is exactly
the planted copies. It does this by recolouring non-copy cells of every
accidental placement, preserving planted near-miss cells. Scenes whose
accidental placements cannot be removed without damaging those controls are
rejected. Those copies are pairwise disjoint, so the reference's
maximum disjoint packing is unique. Its reflection tie-break is never needed.
Scenes with overlapping competing placements are deliberately not generated.

The original fixtures are rebuilt with explicit latent arguments: the input
noise grid that already contains the template (`grid`) and the absolute cells
of each hidden copy (`copies`). The output is produced by painting those
copies 8. No search for placements is done in that path.
"""

import random

import common

NOISE = (0, 2, 4, 7)
GREEN = 3
TEMPLATE = 8
_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_N8 = tuple((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0))


def _normalize(cells):
  mr = min(r for r, _ in cells)
  mc = min(c for _, c in cells)
  return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _dims(shape):
  return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _variants(cells):
  out, seen = [], set()
  for mirror in (False, True):
    cur = [(r, -c) if mirror else (r, c) for r, c in cells]
    for _ in range(4):
      cur = [(c, -r) for r, c in cur]
      norm = _normalize(cur)
      if norm not in seen:
        seen.add(norm)
        out.append(norm)
  return out


def _all_placements(g, variants):
  height, width = len(g), len(g[0])
  found = set()
  for v in variants:
    vh, vw = _dims(v)
    for y in range(height - vh + 1):
      for x in range(width - vw + 1):
        if all(g[y + r][x + c] == GREEN for r, c in v):
          found.add(frozenset((y + r, x + c) for r, c in v))
  return found


def _random_template():
  for _ in range(100):
    n = random.randint(4, 6)
    steps = _N4 if random.random() < 0.7 else _N8
    cells = {(random.randint(0, 2), random.randint(0, 2))}
    while len(cells) < n:
      frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in steps
                         if 0 <= r + dr <= 2 and 0 <= c + dc <= 2} - cells)
      cells.add(random.choice(frontier))
    norm = _normalize(cells)
    th, tw = _dims(norm)
    if th >= 2 and tw >= 2:
      return list(norm)
  raise RuntimeError("could not sample a template")


def _replay(grid, copies):
  """Fixture replay: paint the given copies of an explicit input grid."""
  if copies is None:
    raise ValueError("grid replay requires explicit copies")
  inp = [list(row) for row in grid]
  if not inp or any(len(row) != len(inp[0]) for row in inp):
    raise ValueError("grid must be a non-empty rectangle")
  height, width = len(inp), len(inp[0])
  tcells = [(r, c) for r in range(height) for c in range(width)
            if inp[r][c] == TEMPLATE]
  if not tcells:
    raise ValueError("grid has no 8-template")
  variants = set(_variants(tcells))
  out = [list(row) for row in inp]
  seen = set()
  for cells in copies:
    cells = [tuple(p) for p in cells]
    if _normalize(cells) not in variants:
      raise ValueError("copy is not an orientation of the template")
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("copy cell out of bounds")
      if (r, c) in seen or inp[r][c] != GREEN:
        raise ValueError("copies must be disjoint and lie on green")
      seen.add((r, c))
      out[r][c] = TEMPLATE
  return {"input": inp, "output": out}


def generate(width=None, height=None, template=None, template_pos=None,
             copies=None, num_copies=None, green_density=None,
             num_distractors=None, grid=None):
  """Build one input/output pair.

  Args:
    width: grid width, 1-30 (sampled 10-30, enlarged if needed for copies).
    height: grid height, 1-30 (sampled 10-30, enlarged if needed).
    template: relative cells of the 8-template (sampled if None).
    template_pos: (row, col) of the template's bounding-box top-left.
    copies: list of absolute cell lists, one per hidden green copy. Each must
      be an orientation of `template`, which is then required.
    num_copies: number of hidden copies to plant (sampled 1-3). It must equal
      len(copies) if both are given.
    green_density: probability that a noise cell is green (sampled
      0.15-0.35).
    num_distractors: number of near-miss template shapes (sampled 0-2).
    grid: explicit input grid for fixture replay. It must already contain the
      8-template, and `copies` must lie on green. No other arguments may be
      combined with it.
  """
  if grid is not None:
    others = (width, height, template, template_pos, num_copies,
              green_density, num_distractors)
    if any(a is not None for a in others):
      raise ValueError("grid replay accepts only grid and copies")
    return _replay(grid, copies)

  for name, val in (("width", width), ("height", height)):
    if val is not None and not 1 <= val <= 30:
      raise ValueError(name + " must be in 1..30")
  if green_density is not None and not 0 <= green_density < 1:
    raise ValueError("green_density must be in [0, 1)")
  if num_copies is not None and num_copies < 1:
    raise ValueError("num_copies must be >= 1")
  if num_distractors is not None and num_distractors < 0:
    raise ValueError("num_distractors must be >= 0")
  if template_pos is not None and (template_pos[0] < 0 or template_pos[1] < 0):
    raise ValueError("template_pos must be non-negative")
  shape_fixed = None
  if template is not None:
    pts = [tuple(p) for p in template]
    if not pts or len(set(pts)) != len(pts):
      raise ValueError("template must be a non-empty set of distinct cells")
    shape_fixed = list(_normalize(pts))
  fixed_copies = None
  if copies is not None:
    if shape_fixed is None:
      raise ValueError("copies requires an explicit template")
    fixed_copies = [frozenset(tuple(p) for p in cells) for cells in copies]
    if not fixed_copies:
      raise ValueError("copies must be non-empty")
    allowed = set(_variants(shape_fixed))
    seen = set()
    for cells in fixed_copies:
      if _normalize(cells) not in allowed:
        raise ValueError("copy is not an orientation of the template")
      if cells & seen or min(min(p) for p in cells) < 0:
        raise ValueError("copies must be disjoint and non-negative")
      seen |= cells
    if num_copies is not None and num_copies != len(fixed_copies):
      raise ValueError("num_copies disagrees with copies")

  for _ in range(200):
    shape = shape_fixed if shape_fixed is not None else _random_template()
    variants = _variants(shape)
    th, tw = _dims(shape)
    need_h, need_w = th, tw
    if template_pos is not None:
      need_h = max(need_h, template_pos[0] + th)
      need_w = max(need_w, template_pos[1] + tw)
    if fixed_copies is not None:
      need_h = max(need_h, max(r for cs in fixed_copies for r, _ in cs) + 1)
      need_w = max(need_w, max(c for cs in fixed_copies for _, c in cs) + 1)
    if need_h > 30 or need_w > 30:
      if shape_fixed is not None:
        raise ValueError("requested layout does not fit in 30x30")
      continue
    h = height if height is not None else random.randint(
        max(10, need_h), 30)
    w = width if width is not None else random.randint(
        max(10, need_w), 30)
    if h < need_h or w < need_w:
      continue
    p3 = green_density if green_density is not None else random.uniform(
        0.15, 0.35)
    g = common.grid(w, h, 0)
    for r in range(h):
      for c in range(w):
        g[r][c] = GREEN if random.random() < p3 else random.choice(NOISE)

    blocked = set()
    if fixed_copies is not None:
      for cells in fixed_copies:
        blocked |= cells
    tcells = None
    for _ in range(50):
      if template_pos is not None:
        ty, tx = template_pos
      else:
        ty, tx = random.randint(0, h - th), random.randint(0, w - tw)
      cand = {(ty + r, tx + c) for r, c in shape}
      if not cand & blocked:
        tcells = cand
        break
      if template_pos is not None:
        break
    if tcells is None:
      continue
    for r, c in tcells:
      g[r][c] = TEMPLATE
    used = set(tcells)

    if fixed_copies is not None:
      planted = list(fixed_copies)
      used |= blocked
    else:
      k = num_copies if num_copies is not None else random.randint(1, 3)
      planted = []
      for _ in range(300):
        if len(planted) >= k:
          break
        v = random.choice(variants)
        vh, vw = _dims(v)
        if vh > h or vw > w:
          continue
        y, x = random.randint(0, h - vh), random.randint(0, w - vw)
        cells = frozenset((y + r, x + c) for r, c in v)
        if cells & used:
          continue
        planted.append(cells)
        used |= cells
      if len(planted) < k:
        continue
    union = set()
    for cells in planted:
      union |= cells
      for r, c in cells:
        g[r][c] = GREEN

    # Extra green cells touching copies (the copy is not a whole component).
    for cells in planted:
      if random.random() < 0.5:
        ring = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _N4
                       if 0 <= r + dr < h and 0 <= c + dc < w} - used)
        if ring:
          for r, c in random.sample(ring, min(len(ring), random.randint(1, 2))):
            g[r][c] = GREEN

    # Near-miss distractors: one orientation with a single cell knocked out.
    nd = num_distractors if num_distractors is not None else random.randint(0, 2)
    placed = 0
    distractor_green = set()
    for _ in range(300):
      if placed >= nd:
        break
      v = random.choice(variants)
      vh, vw = _dims(v)
      if vh > h or vw > w:
        continue
      y, x = random.randint(0, h - vh), random.randint(0, w - vw)
      cells = frozenset((y + r, x + c) for r, c in v)
      if cells & used:
        continue
      miss = random.choice(sorted(cells))
      for r, c in cells:
        g[r][c] = GREEN
      g[miss[0]][miss[1]] = random.choice(NOISE)
      used |= cells
      distractor_green |= set(cells) - {miss}
      placed += 1
    if placed < nd:
      continue

    # Repair: break every accidental all-green placement on a non-copy cell.
    # Recolouring only removes green, so no new placements can appear.
    planted_set = set(planted)
    ok = True
    for p in sorted(_all_placements(g, variants) - planted_set, key=sorted):
      if all(g[r][c] == GREEN for r, c in p):
        free = sorted(p - union - distractor_green)
        if not free:
          ok = False
          break
        r, c = random.choice(free)
        g[r][c] = random.choice(NOISE)
    if not ok:
      continue

    out = [list(row) for row in g]
    for r, c in union:
      out[r][c] = TEMPLATE
    return {"input": g, "output": out}
  raise ValueError("could not construct a scene for the requested parameters")


def validate():
  """Rebuild the canonical fixtures from their input grids and copy cells."""
  g1 = [[3, 0, 0, 7, 3, 3, 3, 2, 2, 3, 3, 2, 0, 2, 4, 7, 2, 0], [0, 2, 4, 0, 2, 0, 7, 0, 0, 2, 0, 3, 2, 2, 2, 2, 2, 7], [7, 0, 2, 3, 0, 4, 4, 7, 2, 7, 7, 0, 4, 0, 4, 3, 0, 3], [7, 3, 0, 2, 4, 3, 7, 2, 0, 2, 0, 3, 3, 2, 2, 7, 4, 0], [0, 3, 4, 3, 2, 4, 3, 8, 0, 2, 3, 3, 4, 0, 3, 0, 3, 0], [0, 2, 2, 0, 7, 3, 8, 8, 8, 4, 3, 0, 7, 3, 4, 2, 2, 2], [2, 3, 2, 4, 7, 0, 7, 2, 0, 4, 0, 0, 0, 0, 7, 0, 4, 7], [3, 4, 7, 7, 0, 3, 2, 0, 0, 7, 3, 0, 2, 7, 4, 2, 0, 3], [2, 3, 0, 3, 3, 0, 0, 2, 2, 0, 7, 7, 3, 0, 2, 2, 2, 3], [0, 3, 3, 4, 0, 3, 0, 0, 2, 7, 3, 0, 0, 0, 2, 3, 7, 3], [0, 3, 4, 3, 0, 7, 2, 0, 3, 0, 3, 3, 0, 4, 0, 2, 3, 3], [3, 2, 0, 4, 0, 2, 7, 3, 7, 0, 3, 3, 2, 0, 0, 2, 2, 7], [2, 2, 3, 3, 4, 3, 7, 7, 2, 2, 4, 0, 0, 0, 4, 2, 3, 2], [0, 2, 0, 2, 0, 0, 4, 0, 0, 3, 7, 0, 0, 0, 4, 3, 4, 2], [0, 4, 3, 0, 0, 3, 0, 0, 7, 0, 0, 0, 2, 3, 3, 7, 4, 3]]
  g2 = [[2, 7, 7, 0, 0, 3, 3, 2, 2, 0, 0, 2, 3, 3, 7, 0, 0], [0, 3, 7, 2, 2, 4, 2, 7, 4, 2, 7, 2, 2, 7, 0, 7, 2], [2, 3, 0, 3, 7, 3, 0, 2, 7, 2, 0, 2, 2, 3, 2, 3, 2], [2, 4, 7, 3, 0, 0, 4, 2, 4, 2, 4, 0, 7, 0, 3, 3, 0], [7, 3, 2, 4, 3, 2, 0, 0, 7, 2, 0, 3, 2, 2, 3, 0, 2], [2, 7, 3, 7, 2, 2, 2, 0, 2, 2, 7, 4, 2, 2, 3, 0, 3], [0, 3, 0, 0, 2, 3, 0, 2, 2, 0, 7, 7, 3, 2, 0, 0, 0], [2, 0, 0, 4, 0, 2, 2, 2, 0, 4, 4, 0, 7, 0, 0, 3, 2], [3, 2, 7, 0, 7, 8, 0, 8, 0, 4, 2, 2, 2, 2, 0, 0, 0], [7, 2, 3, 4, 3, 2, 8, 8, 2, 0, 4, 0, 3, 7, 0, 3, 2], [7, 7, 2, 2, 0, 7, 7, 4, 2, 3, 2, 7, 2, 2, 7, 2, 3], [0, 0, 0, 4, 2, 3, 0, 4, 7, 7, 3, 0, 7, 2, 0, 3, 0], [0, 0, 7, 2, 3, 0, 2, 3, 0, 3, 4, 2, 3, 3, 3, 2, 3], [7, 2, 2, 2, 2, 3, 0, 3, 0, 3, 3, 0, 7, 0, 3, 3, 2]]
  g3 = [[2, 3, 2, 8, 4, 4, 0, 2, 3, 0, 2, 4, 7, 7, 3, 7, 3], [3, 4, 8, 8, 8, 0, 0, 2, 0, 2, 0, 2, 7, 7, 7, 3, 7], [7, 3, 0, 8, 0, 2, 2, 0, 2, 2, 0, 7, 3, 0, 3, 3, 3], [2, 0, 2, 0, 2, 0, 3, 2, 0, 7, 0, 7, 0, 0, 2, 3, 0], [7, 7, 4, 3, 7, 2, 0, 2, 3, 0, 3, 4, 7, 2, 0, 3, 7], [2, 4, 0, 7, 0, 0, 3, 4, 4, 0, 3, 4, 4, 3, 3, 4, 0], [3, 2, 7, 3, 7, 3, 7, 2, 0, 2, 3, 2, 3, 3, 3, 4, 4], [3, 7, 4, 0, 2, 0, 2, 0, 3, 7, 2, 3, 3, 3, 3, 0, 2], [3, 2, 3, 2, 0, 2, 0, 2, 0, 7, 2, 0, 2, 4, 4, 7, 3], [4, 3, 4, 2, 0, 7, 0, 0, 7, 0, 0, 0, 0, 3, 0, 0, 3], [2, 3, 0, 0, 4, 0, 2, 0, 3, 3, 2, 0, 4, 0, 0, 2, 2], [3, 3, 4, 3, 2, 7, 2, 4, 3, 0, 7, 3, 3, 4, 2, 0, 3], [2, 0, 7, 7, 0, 3, 7, 4, 3, 7, 0, 2, 0, 3, 7, 0, 2], [2, 3, 0, 0, 2, 3, 0, 7, 0, 7, 3, 7, 0, 4, 0, 3, 7], [2, 0, 2, 2, 7, 2, 0, 0, 2, 2, 3, 0, 0, 3, 7, 0, 3], [7, 2, 4, 0, 3, 0, 0, 2, 2, 7, 4, 0, 0, 2, 2, 0, 4], [0, 0, 3, 0, 4, 4, 7, 7, 4, 2, 0, 0, 3, 7, 0, 2, 0], [2, 3, 4, 0, 3, 0, 3, 3, 2, 3, 4, 7, 7, 0, 2, 0, 3]]
  g4 = [[2, 2, 0, 7, 0, 3, 2, 7, 0, 2, 7, 0, 3, 2, 7, 0, 0, 3], [2, 2, 0, 0, 2, 3, 3, 4, 0, 0, 7, 0, 0, 0, 0, 0, 0, 7], [4, 2, 7, 2, 7, 0, 4, 0, 0, 7, 2, 0, 3, 0, 7, 3, 2, 0], [3, 7, 2, 2, 7, 0, 0, 3, 0, 2, 4, 0, 2, 4, 0, 4, 3, 3], [2, 4, 3, 2, 0, 4, 3, 2, 3, 2, 0, 0, 8, 8, 8, 7, 0, 2], [2, 7, 3, 2, 7, 0, 0, 2, 3, 3, 3, 7, 0, 8, 2, 2, 2, 0], [0, 2, 2, 2, 0, 3, 2, 7, 3, 3, 7, 0, 0, 8, 0, 0, 0, 0], [4, 2, 7, 3, 0, 3, 0, 7, 2, 7, 2, 0, 4, 2, 7, 7, 0, 0], [0, 0, 2, 0, 2, 0, 4, 7, 4, 0, 0, 2, 2, 2, 3, 3, 3, 0], [2, 0, 4, 7, 0, 7, 0, 3, 2, 4, 2, 0, 0, 2, 0, 0, 2, 7], [7, 4, 2, 7, 4, 3, 3, 7, 2, 2, 0, 0, 7, 7, 0, 7, 0, 4]]
  gt = [[7, 3, 2, 2, 4, 3, 7, 2, 7, 0, 7, 3, 4, 0, 3, 2, 4], [0, 2, 2, 2, 2, 3, 0, 3, 3, 0, 3, 2, 0, 0, 3, 0, 7], [3, 2, 0, 3, 7, 0, 2, 2, 2, 3, 7, 0, 3, 3, 0, 2, 2], [4, 2, 7, 7, 0, 0, 2, 0, 0, 0, 7, 4, 3, 2, 3, 7, 2], [7, 0, 8, 3, 0, 7, 3, 3, 0, 2, 3, 0, 4, 0, 0, 7, 0], [3, 4, 8, 8, 3, 2, 0, 0, 3, 4, 2, 4, 0, 3, 3, 2, 4], [2, 3, 0, 8, 0, 0, 2, 4, 0, 4, 4, 0, 0, 7, 2, 3, 0], [2, 4, 0, 3, 0, 0, 2, 2, 3, 2, 7, 3, 3, 7, 0, 4, 0], [2, 7, 7, 4, 0, 3, 0, 2, 7, 7, 0, 4, 7, 0, 7, 3, 3], [0, 0, 7, 3, 4, 0, 2, 3, 0, 7, 4, 3, 2, 3, 0, 7, 3], [2, 7, 0, 3, 4, 7, 3, 4, 0, 4, 0, 0, 0, 3, 3, 7, 2], [4, 3, 0, 2, 3, 0, 4, 0, 4, 3, 3, 2, 2, 3, 3, 0, 3], [4, 7, 0, 7, 3, 3, 2, 3, 3, 0, 7, 0, 0, 0, 0, 4, 7], [3, 3, 3, 3, 0, 4, 3, 4, 4, 7, 3, 7, 0, 0, 0, 3, 0], [0, 2, 2, 3, 3, 3, 0, 7, 3, 2, 7, 3, 4, 3, 3, 3, 3], [3, 3, 3, 4, 7, 4, 3, 3, 3, 0, 0, 4, 0, 7, 0, 4, 3]]
  train = [
      generate(grid=g1, copies=[
          [(8, 1), (9, 1), (9, 2), (10, 1)],
          [(9, 10), (10, 10), (10, 11), (11, 10)]]),
      generate(grid=g2, copies=[
          [(2, 13), (2, 15), (3, 14), (3, 15)],
          [(11, 10), (12, 9), (13, 9), (13, 10)],
          [(11, 15), (12, 14), (13, 14), (13, 15)]]),
      generate(grid=g3, copies=[
          [(1, 15), (2, 14), (2, 15), (2, 16), (3, 15)],
          [(5, 13), (6, 12), (6, 13), (6, 14), (7, 13)]]),
      generate(grid=g4, copies=[
          [(4, 8), (5, 8), (5, 9), (5, 10), (6, 8)]]),
  ]
  test = [
      generate(grid=gt, copies=[
          [(9, 13), (10, 13), (10, 14), (11, 14)],
          [(13, 2), (13, 3), (14, 3), (14, 4)],
          [(13, 15), (14, 15), (14, 16), (15, 16)]]),
  ]
  return {"train": train, "test": test}
