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

"""ARC task 1b59e163: stamp marked templates onto lone marker cells.

Rule: on a background of 4, each template is a small shape. It has a body of
one colour and exactly one embedded marker cell of a unique colour. The body
and marker together form one 8-connected component. Elsewhere there are
isolated single cells. A lone cell whose colour equals a template's marker
receives a copy of that template, placed so the marker lands on the lone
cell. Lone 5s match no template and are discarded. The original templates are
erased, so the output is a fresh canvas containing only the stamped copies.

Scope: grid sizes from 14 to 30 per side. There are 2-4 random 8-connected
templates. Each one has 1-3 lone target markers. There are 0-3 distractor 5s.
Body colours come from one or two colours, and these are disjoint from the
marker colours. Stamped copies may touch each other in the output, but they
never overlap.
"""

import random

import common


_PALETTE = [0, 1, 2, 3, 6, 7, 8, 9]


def _footprint(t, pos):
  """Absolute (row, col, colour) cells of template t with its marker at pos."""
  r, c = pos
  cells = [(r, c, t["marker"])]
  for dr, dc in t["shape"]:
    cells.append((r + dr, c + dc, t["body"]))
  return cells


def _in_bounds(cells, height, width):
  return all(0 <= r < height and 0 <= c < width for r, c, _ in cells)


def _touches(cells, occ):
  for r, c, _ in cells:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        if (r + a, c + b) in occ:
          return True
  return False


def _random_shape():
  """Body offsets relative to the marker; body+marker are 8-connected."""
  bh = random.randint(2, 4)
  bw = random.randint(2, 4)
  if bh * bw < 4:
    bw = 3
  mr, mc = random.randrange(bh), random.randrange(bw)
  n_body = random.randint(2, min(8, bh * bw - 1))
  cells = {(mr, mc)}
  body = []
  for _ in range(200):
    if len(body) >= n_body:
      break
    frontier = set()
    for (r, c) in cells:
      for a in (-1, 0, 1):
        for b in (-1, 0, 1):
          nr, nc = r + a, c + b
          if 0 <= nr < bh and 0 <= nc < bw and (nr, nc) not in cells:
            frontier.add((nr, nc))
    if not frontier:
      break
    cell = random.choice(sorted(frontier))
    cells.add(cell)
    body.append(cell)
  return [(r - mr, c - mc) for r, c in body]


def _random_scene(requested_height=None, requested_width=None):
  for _ in range(300):
    height = requested_height if requested_height is not None else random.randint(14, 30)
    width = requested_width if requested_width is not None else random.randint(14, 30)
    n = random.randint(2, 4)
    pool = _PALETTE[:]
    random.shuffle(pool)
    nb = 1 if random.random() < 0.6 else 2
    bodies, markers = pool[:nb], pool[nb:nb + n]
    occ = set()
    stamps = set()
    templates = []
    ok = True
    for i in range(n):
      t = {"body": random.choice(bodies), "marker": markers[i],
           "shape": _random_shape(), "targets": []}
      placed = None
      for _ in range(100):
        pos = (random.randrange(height), random.randrange(width))
        cells = _footprint(t, pos)
        if _in_bounds(cells, height, width) and not _touches(cells, occ):
          placed = pos
          break
      if placed is None:
        ok = False
        break
      t["anchor"] = placed
      for r, c, _ in _footprint(t, placed):
        occ.add((r, c))
      for _ in range(random.randint(1, 3)):
        for _ in range(100):
          pos = (random.randrange(height), random.randrange(width))
          single = [(pos[0], pos[1], t["marker"])]
          stamp = _footprint(t, pos)
          if (_touches(single, occ) or not _in_bounds(stamp, height, width)
              or any((r, c) in stamps for r, c, _ in stamp)):
            continue
          occ.add(pos)
          for r, c, _ in stamp:
            stamps.add((r, c))
          t["targets"].append(pos)
          break
      if not t["targets"]:
        ok = False
        break
      templates.append(t)
    if not ok:
      continue
    distractors = []
    for _ in range(random.randint(0, 3)):
      for _ in range(100):
        pos = (random.randrange(height), random.randrange(width))
        if not _touches([(pos[0], pos[1], 5)], occ):
          occ.add(pos)
          distractors.append(pos)
          break
    return height, width, templates, distractors
  raise RuntimeError("failed to build scene")


def generate(height=None, width=None, templates=None, distractors=None,
             background=4, distractor_color=5):
  """Build one input/output pair.

  Args:
    height: grid height (rows).
    width: grid width (columns).
    templates: list of dicts with keys "body" (body colour), "marker"
      (unique marker colour), "anchor" ((row, col) of the template's marker
      in the input), "shape" (list of (dr, dc) body offsets from the marker)
      and "targets" (list of (row, col) lone marker cells).
    distractors: list of (row, col) lone cells of distractor_color.
    background: background colour.
    distractor_color: colour of unmatched lone cells.
  """
  if templates is None:
    if any(v is not None and not 14 <= v <= 30 for v in (height, width)):
      raise ValueError("grid dimensions must be 14..30")
    if background != 4 or distractor_color != 5:
      raise ValueError("random scenes use background 4 and distractor colour 5")
    if distractors is not None:
      raise ValueError("explicit distractors require explicit templates")
    height, width, templates, distractors = _random_scene(height, width)
  distractors = distractors or []
  grid_in = common.grid(width, height, background)
  grid_out = common.grid(width, height, background)
  for t in templates:
    for r, c, col in _footprint(t, t["anchor"]):
      grid_in[r][c] = col
    for (r, c) in t["targets"]:
      grid_in[r][c] = t["marker"]
      for rr, cc, col in _footprint(t, (r, c)):
        if 0 <= rr < height and 0 <= cc < width:
          grid_out[rr][cc] = col
  for (r, c) in distractors:
    grid_in[r][c] = distractor_color
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  ring = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
  train = [
      generate(18, 18, templates=[
          {"body": 1, "marker": 6, "anchor": (1, 3),
           "shape": [(1, -1), (1, 0), (1, 1), (2, 0)], "targets": [(1, 12)]},
          {"body": 1, "marker": 3, "anchor": (12, 7),
           "shape": [(-2, -1), (-2, 0), (-2, 1), (-1, -1), (-1, 1)],
           "targets": [(12, 3), (12, 14)]},
      ], distractors=[(5, 12), (7, 3), (15, 7)]),
      generate(18, 18, templates=[
          {"body": 1, "marker": 2, "anchor": (2, 2), "shape": ring,
           "targets": [(2, 7), (2, 13)]},
          {"body": 1, "marker": 3, "anchor": (9, 2),
           "shape": [(-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
                     (1, -1), (1, 1)], "targets": [(9, 9)]},
          {"body": 1, "marker": 8, "anchor": (15, 14),
           "shape": [(-1, -1), (-1, 0), (-1, 1), (0, -2), (0, 2), (1, -1),
                     (1, 1)], "targets": [(15, 3)]},
      ], distractors=[(5, 12), (12, 6)]),
  ]
  test = [
      generate(18, 18, templates=[
          {"body": 1, "marker": 6, "anchor": (4, 4),
           "shape": [(-2, 0), (-1, 0), (0, -1), (0, 1), (1, 0)],
           "targets": [(4, 9), (4, 12), (4, 15)]},
          {"body": 1, "marker": 3, "anchor": (10, 3),
           "shape": [(-2, 0), (-1, -1), (-1, 1)], "targets": [(10, 10)]},
          {"body": 2, "marker": 8, "anchor": (15, 11),
           "shape": [(-2, -1), (-2, 1), (-1, -1), (-1, 0), (-1, 1), (0, -1),
                     (0, 1)], "targets": [(15, 1), (15, 5)]},
      ], distractors=[(6, 8), (11, 16)]),
  ]
  return {"train": train, "test": test}
