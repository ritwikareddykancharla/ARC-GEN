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

"""ARC task 3dc255db: cups eject their contents through their closed side.

Rule: each container is a single-colour, diagonally connected cup that is
closed on three sides and open on one. Marker cells of another colour sit
inside the cup's bounding box. In the output the markers are erased. A
straight line of the marker colour is then drawn outward from the cup's
extreme cell on the closed side, opposite the opening. The line's length
equals the number of markers, and it is clipped at the grid border.

Scope: the random scenes contain one to four cups of distinct colours on a
black background. Each cup is a U shape or a vertical/diagonal arch with variable interior
width and depth. Its two walls may have unequal heights, its corners may be cut
(diagonal joins), and its wall tops may be flared. A one- or two-cell knob
on the closed side makes the start cell unique. The cup is rotated to any of
the four orientations. Markers of a single colour are scattered in the cup
interior, and that colour may coincide with other cups' colours. Lone
distractor cells may lie outside every cup. Lines are often clipped by the
border. The original fixtures, which use irregular arch and chevron shapes,
are reproduced through the explicit `containers` / `distractors` latent
arguments.
"""

import random

import common

_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rot(p, t):
  r, c = p
  for _ in range(t):
    r, c = c, -r
  return r, c


def _dilate(cells):
  out = set()
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _cup_shape(iw, idp, hl, hr, cut, kc, stem, fl, fr):
  """Local cup that opens upward; the closed side (with knob) points down."""
  rr = iw + 1
  b = max(hl, hr)
  cells = set()
  for r in range(b - hl, b):
    cells.add((r, 0))
  for r in range(b - hr, b):
    cells.add((r, rr))
  lo, hi = (1, rr - 1) if cut else (0, rr)
  for c in range(lo, hi + 1):
    cells.add((b, c))
  kc = min(max(kc, lo), hi)
  for s in range(1, stem + 1):
    cells.add((b + s, kc))
  if fl:
    cells.add((b - hl - 1, -1))
  if fr:
    cells.add((b - hr - 1, rr + 1))
  interior = [(r, c) for r in range(b - idp, b) for c in range(1, rr)]
  return cells, interior


def _arch_shape(radius, depth, stem):
  """A curved/chevron bowl built from vertical and diagonal side segments."""
  cells=set();interior=[]
  for r in range(depth+1):
    spread=min(radius,depth-r)
    cells.add((r,-spread));cells.add((r,spread))
    interior.extend((r,c) for c in range(-spread+1,spread))
  for y in range(1,stem+1):cells.add((depth+y,0))
  return cells,interior


def _start(spec):
  dr, dc = spec["direction"]
  cells = [tuple(c) for c in spec["cells"]]
  key = lambda p: p[0] * dr + p[1] * dc
  mx = max(key(p) for p in cells)
  ext = [p for p in cells if key(p) == mx]
  ms = spec["markers"]
  my = sum(m[0] for m in ms) / len(ms)
  mxx = sum(m[1] for m in ms) / len(ms)
  return min(ext, key=lambda p: (abs(p[0] - my) + abs(p[1] - mxx), p))


def _line(spec, height, width):
  dr, dc = spec["direction"]
  sr, sc = _start(spec)
  r, c = sr + dr, sc + dc
  out = []
  while len(out) < len(spec["markers"]) and 0 <= r < height and 0 <= c < width:
    out.append((r, c))
    r += dr
    c += dc
  return out


def _render(height, width, containers, distractors):
  grid = common.grid(width, height, 0)
  for spec in containers:
    for r, c in spec["cells"]:
      grid[r][c] = spec["colour"]
    for r, c in spec["markers"]:
      grid[r][c] = spec["marker_colour"]
  for r, c, col in distractors:
    grid[r][c] = col
  output = [row[:] for row in grid]
  for spec in containers:
    for r, c in spec["markers"]:
      output[r][c] = 0
    for r, c in _line(spec, height, width):
      output[r][c] = spec["marker_colour"]
  return grid, output


def _rays_ok(grid, spec):
  """Opening side: every marker ray escapes; other sides: strictly fewer."""
  height, width = len(grid), len(grid[0])
  col = spec["colour"]
  opening = (-spec["direction"][0], -spec["direction"][1])
  counts = {}
  for d in _DIRS:
    esc = 0
    for r, c in spec["markers"]:
      rr, cc = r + d[0], c + d[1]
      hit = False
      while 0 <= rr < height and 0 <= cc < width:
        if grid[rr][cc] == col:
          hit = True
          break
        rr += d[0]
        cc += d[1]
      if not hit:
        esc += 1
    counts[d] = esc
  k = len(spec["markers"])
  if counts[opening] != k:
    return False
  return all(counts[d] < k for d in _DIRS if d != opening)


def _sample_container(colour, height, width, blocked, shape_mode, marker_count):
  for _ in range(60):
    iw = random.randint(1, 4)
    idp = random.randint(1, 4)
    hl = random.randint(idp, idp + 2)
    hr = random.randint(idp, idp + 2)
    cut = random.random() < 0.4
    kc = random.randint(0, iw + 1)
    stem = random.choice([1, 1, 2])
    fl = random.random() < 0.25
    fr = random.random() < 0.25
    kind=random.choice(("u","arch")) if shape_mode=="mixed" else shape_mode
    if kind=="arch":
      radius=random.randint(1,4);depth=random.randint(radius,radius+4)
      cells,interior=_arch_shape(radius,depth,stem)
    else:
      cells,interior=_cup_shape(iw,idp,hl,hr,cut,kc,stem,fl,fr)
    k=marker_count if marker_count is not None else random.randint(1,min(len(interior),15))
    if k>len(interior):continue
    if k >= len(cells):
      continue
    markers = random.sample(interior, k)
    t = random.randint(0, 3)
    cl = [_rot(p, t) for p in cells]
    mk = [_rot(p, t) for p in markers]
    d = _rot((1, 0), t)
    minr = min(p[0] for p in cl)
    minc = min(p[1] for p in cl)
    h = max(p[0] for p in cl) - minr + 1
    w = max(p[1] for p in cl) - minc + 1
    if h > height or w > width:
      continue
    r0 = random.randint(0, height - h) - minr
    c0 = random.randint(0, width - w) - minc
    spec = {
        "colour": colour,
        "cells": [(r + r0, c + c0) for r, c in cl],
        "markers": [(r + r0, c + c0) for r, c in mk],
        "marker_colour": random.choice([x for x in range(1, 10) if x != colour]),
        "direction": d,
    }
    line = _line(spec, height, width)
    if not line:
      continue
    br, bc = minr + r0, minc + c0
    zone = {(r, c) for r in range(br, br + h) for c in range(bc, bc + w)}
    zone |= set(line)
    if zone & blocked:
      continue
    return spec, zone
  return None


def _sample_scene(height, width, num_containers, shape_mode, marker_count):
  for _ in range(200):
    hh = height if height is not None else random.randint(9,30)
    ww = width if width is not None else random.randint(9,30)
    n = num_containers if num_containers is not None else random.choice([1,2,2,3,3,4])
    colours = random.sample(range(1, 10), n)
    blocked = set()
    containers = []
    ok = True
    for colour in colours:
      res = _sample_container(colour, hh, ww, blocked, shape_mode, marker_count)
      if res is None:
        ok = False
        break
      containers.append(res[0])
      blocked |= _dilate(res[1])
    if not ok:
      continue
    distractors = []
    for _ in range(random.randint(0, 3)):
      for _ in range(30):
        r, c = random.randrange(hh), random.randrange(ww)
        if (r, c) in blocked:
          continue
        distractors.append((r, c, random.randint(1, 9)))
        blocked |= _dilate([(r, c)])
        break
    grid, _ = _render(hh, ww, containers, distractors)
    if not all(_rays_ok(grid, s) for s in containers):
      continue
    counts = [0] * 10
    for row in grid:
      for v in row:
        counts[v] += 1
    if any(counts[x] >= counts[0] for x in range(1, 10)):
      continue
    return hh, ww, containers, distractors
  raise RuntimeError("could not construct a scene")


def generate(height=None, width=None, containers=None, distractors=None,
             num_containers=None, shape_mode=None, marker_count=None):
  """Returns an input/output pair.

  Args:
    height: grid height (rows); sampled in 9..30 when None.
    width: grid width (columns); sampled in 9..30 when None.
    containers: optional list of dicts with keys "colour", "cells" (list of
      (row, col)), "markers" (list of (row, col)), "marker_colour" and
      "direction" (unit (dr, dc) in which the line is drawn, i.e. away from
      the opening). When given, height and width must also be given.
    distractors: optional list of (row, col, colour) lone cells outside cups.
    num_containers: exact random cup count, 1..4.
    shape_mode: u, arch, or mixed (default mixed).
    marker_count: exact markers per random cup, 1..15, subject to fit.
  """
  for d in (height,width):
    if d is not None and (not isinstance(d,int) or not 1 <= d <= 30):raise ValueError("Dimensions must be in 1..30")
  if num_containers is not None and (not isinstance(num_containers,int) or not 1 <= num_containers <= 4):raise ValueError("num_containers must be in 1..4")
  if marker_count is not None and (not isinstance(marker_count,int) or not 1 <= marker_count <= 15):raise ValueError("marker_count must be in 1..15")
  if shape_mode not in (None,"u","arch","mixed"):raise ValueError("Unknown cup shape_mode")
  if containers is None:
    if distractors is not None:raise ValueError("Explicit distractors require containers")
    if any(d is not None and d < 9 for d in (height,width)):raise ValueError("Random sides must be at least 9")
    height, width, containers, distractors = _sample_scene(height,width,num_containers,shape_mode or "mixed",marker_count)
  elif any(v is not None for v in (num_containers,shape_mode,marker_count)):
    raise ValueError("Sampling controls cannot accompany explicit containers")
  if distractors is None:
    distractors = []
  if height is None or width is None or not containers:raise ValueError("Explicit containers require dimensions")
  occupied=set();colours=[]
  for spec in containers:
    if spec['colour'] not in range(1,10) or spec['marker_colour'] not in range(1,10) or spec['colour']==spec['marker_colour']:raise ValueError("Invalid container or marker colour")
    colours.append(spec['colour'])
    if tuple(spec['direction']) not in _DIRS or not spec['cells'] or not spec['markers']:raise ValueError("Invalid direction or empty container")
    pts=[tuple(pt) for pt in spec['cells']+spec['markers']]
    if len(set(pts))!=len(pts) or any(not (0<=r<height and 0<=c<width) or (r,c) in occupied for r,c in pts):raise ValueError("Overlapping or out-of-bounds container")
    occupied.update(pts)
  if len(set(colours))!=len(colours):raise ValueError("Container colours must differ")
  for r,c,col in distractors:
    if col not in range(1,10) or not (0<=r<height and 0<=c<width) or (r,c) in occupied:raise ValueError("Invalid distractor")
    occupied.add((r,c))
  grid, output = _render(height, width, containers, distractors)
  return {"input": grid, "output": output}


def _c(colour, cells, markers, mcol, direction):
  return {"colour": colour, "cells": cells, "markers": markers,
          "marker_colour": mcol, "direction": direction}


def validate():
  """Reconstructs the canonical fixtures from explicit latent scenes."""
  train = [
      generate(12, 12, [
          _c(4, [(1, 2), (1, 3), (2, 4), (2, 5), (3, 4), (3, 5), (3, 6),
                 (4, 2), (4, 3), (4, 4), (4, 5)],
             [(2, 3), (3, 2)], 6, (0, 1)),
          _c(3, [(7, 6), (7, 7), (7, 8), (7, 9), (8, 4), (8, 5), (9, 4),
                 (9, 5), (10, 3), (10, 4), (10, 5), (11, 6), (11, 7),
                 (11, 8)],
             [(8, 6), (9, 7)], 7, (0, -1)),
      ], [(2, 0, 6)]),
      generate(10, 10, [
          _c(3, [(3, 2), (4, 2), (5, 1), (5, 3), (6, 0), (6, 4), (7, 4),
                 (8, 4)],
             [(5, 2), (6, 1), (7, 2)], 9, (-1, 0)),
          _c(6, [(3, 7), (4, 6), (4, 8), (5, 6), (5, 8)],
             [(5, 7)], 9, (-1, 0)),
      ]),
      generate(12, 12, [
          _c(6, [(3, 5), (4, 4), (4, 5), (4, 6), (5, 3), (5, 4), (5, 7),
                 (6, 2), (6, 8), (7, 2), (7, 8), (8, 2), (8, 8), (9, 2),
                 (9, 8), (10, 2), (10, 8)],
             [(7, 3), (7, 4), (7, 5), (7, 6), (8, 6), (9, 3), (9, 5)], 7,
             (-1, 0)),
      ]),
  ]
  test = [
      generate(12, 13, [
          _c(2, [(2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (3, 10), (4, 5),
                 (4, 6), (4, 7), (4, 8), (4, 9)],
             [(3, 6), (3, 7), (3, 8)], 4, (0, 1)),
          _c(9, [(6, 3), (7, 2), (7, 3), (8, 1), (8, 4), (9, 1), (9, 4),
                 (10, 1), (10, 4), (11, 1), (11, 4)],
             [(9, 2), (9, 3), (10, 3), (11, 2)], 7, (-1, 0)),
          _c(8, [(7, 9), (8, 10), (9, 11), (10, 10), (11, 9)],
             [(9, 10), (10, 9)], 2, (0, 1)),
      ], [(9, 7, 2)]),
  ]
  return {"train": train, "test": test}
