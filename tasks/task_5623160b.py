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

"""ARC task 5623160b: objects touching a 9 are pushed away to the border.

Rule: the background is 7. Colour-9 shapes are fixed anchors. Every other
single-colour object that is orthogonally adjacent to a 9 slides in a straight
line directly away from that 9 until it reaches the grid border. It keeps its
shape while it slides. Objects that do not touch a 9 stay where they are, and
so do 9 shapes with nothing attached.

Scope: the generator samples the grid size and one to three 9 shapes. The
shapes are random polyominoes, crosses, bars and blocks. It attaches one to
six movers to randomly chosen sides of those shapes, and it can use several
sides of one shape at once. A mover may already sit on the border, in which
case it stays put. The generator also adds up to two distractor objects that
do not touch any 9.

Every non-9 object has its own colour. Each mover touches 9 cells from exactly
one side. Slide paths are kept clear of other objects, so every mover reaches
the border. Sizes from 5 to 30 per side can be requested. The default sampler
uses 7..30, a synthetic extension around the 9..16 fixture sizes.
"""

import random

import common


BACKGROUND = 7
ANCHOR = 9
PALETTE = [0, 1, 2, 3, 4, 5, 6, 8]
DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def _normalize(cells):
  mr = min(r for r, _ in cells)
  mc = min(c for _, c in cells)
  return sorted((r - mr, c - mc) for r, c in cells)


def _poly(size, maxh, maxw):
  """Random 4-connected polyomino of up to `size` cells inside maxh x maxw."""
  cells = {(0, 0)}
  tries = 0
  while len(cells) < size and tries < 300:
    tries += 1
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(list(DIRS.values()))
    n = (r + dr, c + dc)
    if n in cells:
      continue
    trial = cells | {n}
    rs = [p[0] for p in trial]
    cs = [p[1] for p in trial]
    if max(rs) - min(rs) >= maxh or max(cs) - min(cs) >= maxw:
      continue
    cells = trial
  return _normalize(cells)


def _nine_shape():
  """Random anchor shape: a cross, a block or bar, or a small polyomino."""
  u = random.random()
  if u < 0.25:
    cells = {(0, 0)}
    for dr, dc in DIRS.values():
      if random.random() < 0.75:
        for t in range(1, random.randint(1, 2) + 1):
          cells.add((dr * t, dc * t))
    return _normalize(cells)
  if u < 0.4:
    h, w = random.choice([(2, 2), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3)])
    return [(r, c) for r in range(h) for c in range(w)]
  return _poly(random.randint(1, 5), 3, 4)


def _dist(cells, d, height, width):
  """Number of steps until the shape reaches the border in direction d."""
  dr, dc = d
  best = None
  for r, c in cells:
    if dr == -1:
      v = r
    elif dr == 1:
      v = height - 1 - r
    elif dc == -1:
      v = c
    else:
      v = width - 1 - c
    best = v if best is None else min(best, v)
  return best


def _near(p, cellset, rad):
  r, c = p
  for dr in range(-rad, rad + 1):
    for dc in range(-rad, rad + 1):
      if (r + dr, c + dc) in cellset:
        return True
  return False


def _touch_sides(cells, nine_cells):
  """Motion directions implied by 9 cells adjacent to this object."""
  cs = set(cells)
  sides = set()
  for r, c in cells:
    for d in DIRS.values():
      q = (r - d[0], c - d[1])
      if q in nine_cells and q not in cs:
        sides.add(d)
  return sides


def _path(cells, d, k):
  cs = set(cells)
  out = set()
  for r, c in cells:
    for t in range(1, k + 1):
      out.add((r + d[0] * t, c + d[1] * t))
  return out - cs


def _random_scene(width, height, num_anchors, num_movers, num_distractors, mover_size):
  for _ in range(500):
    h_ = height if height is not None else random.randint(7, 30)
    w_ = width if width is not None else random.randint(7, 30)
    big = min(h_, w_) >= 13
    n9 = num_anchors if num_anchors is not None else random.choice([1, 1, 2, 2, 3])
    nines = []
    nine_cells = set()
    for _ in range(80):
      if len(nines) == n9:
        break
      sh = _nine_shape()
      sh_h = max(r for r, _ in sh) + 1
      sh_w = max(c for _, c in sh) + 1
      if sh_h > h_ or sh_w > w_:
        continue
      r0 = random.randint(0, h_ - sh_h)
      c0 = random.randint(0, w_ - sh_w)
      cells = [(r + r0, c + c0) for r, c in sh]
      if any(_near(p, nine_cells, 2) for p in cells):
        continue
      nines.append(cells)
      nine_cells.update(cells)
    if not nines or (num_anchors is not None and len(nines)!=num_anchors):
      continue

    target = num_movers if num_movers is not None else random.randint(2, 6)
    obj_cells = set()
    sweeps = set()
    movers = []
    for _ in range(400):
      if len(movers) >= target:
        break
      name = random.choice(sorted(DIRS))
      d = DIRS[name]
      base = random.choice(random.choice(nines))
      a = (base[0] + d[0], base[1] + d[1])
      size = mover_size if mover_size is not None else random.choice([1, 1, 2, 2, 3, 4, 5, 6] + ([7, 8, 12, 16, 20] if big else []))
      shape = _poly(size, 6 if big else 3, 8 if big else 4)
      if mover_size is not None and len(shape)!=mover_size:
        continue
      anc = random.choice(shape)
      cells = [(a[0] + r - anc[0], a[1] + c - anc[1]) for r, c in shape]
      cs = set(cells)
      if any(not (0 <= r < h_ and 0 <= c < w_) for r, c in cells):
        continue
      if cs & nine_cells or cs & sweeps:
        continue
      if any(_near(p, obj_cells, 1) for p in cells):
        continue
      # It must touch 9 cells only from the side opposite its motion.
      if _touch_sides(cells, nine_cells) != {d}:
        continue
      k = _dist(cells, d, h_, w_)
      if k == 0 and random.random() < 0.8:
        continue
      sweep = _path(cells, d, k)
      if sweep & (nine_cells | obj_cells | sweeps):
        continue
      movers.append((cells, name, k))
      obj_cells.update(cells)
      sweeps.update(sweep)
    if not movers or (num_movers is not None and len(movers)!=num_movers) or all(m[2] == 0 for m in movers):
      continue

    distractors = []
    n_dis = num_distractors if num_distractors is not None else random.randint(0, min(2, len(PALETTE) - len(movers)))
    for _ in range(100):
      if len(distractors) >= n_dis:
        break
      shape = _poly(random.randint(1, 5), 3, 3)
      sh_h = max(r for r, _ in shape) + 1
      sh_w = max(c for _, c in shape) + 1
      if sh_h > h_ or sh_w > w_:
        continue
      r0 = random.randint(0, h_ - sh_h)
      c0 = random.randint(0, w_ - sh_w)
      cells = [(r + r0, c + c0) for r, c in shape]
      if set(cells) & sweeps:
        continue
      if any(_near(p, nine_cells, 1) or _near(p, obj_cells, 1) for p in cells):
        continue
      distractors.append(cells)
      obj_cells.update(cells)

    if num_distractors is not None and len(distractors)!=num_distractors:
      continue
    total = len(movers) + len(distractors)
    colours = random.sample(PALETTE, total)
    objects = []
    for i, (cells, name, _) in enumerate(movers):
      objects.append((colours[i], cells, name))
    for j, cells in enumerate(distractors):
      objects.append((colours[len(movers) + j], cells, None))
    random.shuffle(objects)
    return w_, h_, nines, objects
  raise ValueError("could not build a scene for size %sx%s" % (width, height))


def _check_scene(width, height, nines, objects):
  """Reject explicit scenes that the latent model cannot express exactly."""
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid size out of range")
  nine_cells = set()
  for shape in nines:
    for r, c in shape:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError("9 cell out of bounds")
      nine_cells.add((r, c))
  used = set(nine_cells)
  for colour, cells, name in objects:
    if colour in (BACKGROUND, ANCHOR) or not 0 <= colour <= 9:
      raise ValueError("object colour collides with background or anchor")
    if name is not None and name not in DIRS:
      raise ValueError("unknown direction %r" % (name,))
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width) or (r, c) in used:
        raise ValueError("object cell out of bounds or overlapping")
      used.add((r, c))
  finals = []
  for colour, cells, name in objects:
    sides = _touch_sides(cells, nine_cells)
    if name is None:
      if sides:
        raise ValueError("static object touches a 9")
      finals.append(set(cells))
      continue
    d = DIRS[name]
    if sides != {d}:
      raise ValueError("direction does not match the touching side")
    finals.append({(r + d[0] * _dist(cells, d, height, width),
                    c + d[1] * _dist(cells, d, height, width))
                   for r, c in cells})
  for i, (colour, cells, name) in enumerate(objects):
    if name is None:
      continue
    d = DIRS[name]
    path = _path(cells, d, _dist(cells, d, height, width))
    blockers = set(nine_cells)
    for j, (_, other, _) in enumerate(objects):
      if j != i:
        blockers |= set(other) | finals[j]
    if path & blockers:
      raise ValueError("slide path of a mover is blocked")


def _render(width, height, nines, objects, moved):
  g = common.grid(width, height, BACKGROUND)
  for shape in nines:
    for r, c in shape:
      g[r][c] = ANCHOR
  for colour, cells, name in objects:
    dr = dc = 0
    if moved and name is not None:
      d = DIRS[name]
      k = _dist(cells, d, height, width)
      dr, dc = d[0] * k, d[1] * k
    for r, c in cells:
      g[r + dr][c + dc] = colour
  return g


def generate(width=None, height=None, nines=None, objects=None,
             num_anchors=None, num_movers=None, num_distractors=None, mover_size=None):
  """Build one input/output pair.

  Args:
    width: grid width (columns), 5..30 for random scenes. If it is None with
      no explicit scene, a width is sampled.
    height: grid height (rows), 5..30 for random scenes. If it is None with
      no explicit scene, a height is sampled.
    nines: list of colour-9 anchor shapes, each a list of (row, col) cells.
      This must be given together with objects, width and height.
    num_anchors: exact random anchor count, 1..3.
    num_movers: exact random mover count, 1..6.
    num_distractors: exact random distractor count, 0..2.
    mover_size: exact cells per random mover, 1..24 (large grids advised).
    objects: list of (colour, cells, direction). direction is 'up', 'down',
      'left' or 'right' for an object pushed away from a 9. It is None for an
      object that stays in place. Explicit scenes are checked for
      consistency, and a ValueError is raised if they do not fit the rule.
  """
  controls=(("num_anchors",num_anchors,1,3),("num_movers",num_movers,1,6),
            ("num_distractors",num_distractors,0,2),("mover_size",mover_size,1,24))
  for name,value,lo,hi in controls:
    if value is not None and (not isinstance(value,int) or not lo<=value<=hi):
      raise ValueError(name+" outside supported range")
  if nines is None and objects is None:
    for v in (width, height):
      if v is not None and not 5 <= v <= 30:
        raise ValueError("random scenes need sizes in 5..30")
    width, height, nines, objects = _random_scene(width, height, num_anchors, num_movers, num_distractors, mover_size)
  else:
    if any(value is not None for _,value,_,_ in controls):
      raise ValueError("count/size controls apply only to random scenes")
    if nines is None or objects is None or width is None or height is None:
      raise ValueError("explicit scenes need width, height, nines and objects")
    _check_scene(width, height, nines, objects)
  return {"input": _render(width, height, nines, objects, False),
          "output": _render(width, height, nines, objects, True)}


def validate():
  """Reconstruct the canonical fixtures from explicit latent scenes."""
  train = [
      generate(10, 10,
               [[(3, 7), (4, 7)], [(7, 2)]],
               [(1, [(2, 5), (3, 5), (3, 6)], "left"),
                (0, [(3, 8), (3, 9)], "right"),
                (6, [(5, 6), (5, 7), (5, 8), (6, 7)], "down"),
                (2, [(7, 1)], "left"),
                (8, [(8, 2)], "down")]),
      generate(9, 9,
               [[(4, 3)]],
               [(5, [(3, 3)], "up"),
                (2, [(4, 4), (4, 5), (5, 5)], "right"),
                (8, [(5, 3), (6, 3)], "down")]),
      generate(12, 12,
               [[(5, 5), (6, 5), (7, 3), (7, 4), (7, 5), (8, 5)]],
               [(4, [(3, 4), (3, 6), (4, 4), (4, 5), (4, 6)], "up"),
                (6, [(6, 3)], "up"),
                (3, [(7, 6), (7, 7), (8, 6), (8, 7)], "right"),
                (8, [(8, 3)], "down")]),
  ]
  five = [(4, 2), (4, 3), (4, 4), (4, 5), (4, 7), (4, 8),
          (5, 2), (5, 5), (5, 6), (5, 7),
          (6, 2), (6, 7), (6, 8), (6, 9),
          (7, 2), (7, 3), (7, 4), (7, 7), (7, 9)]
  zero = [(10, 10), (11, 10), (11, 11), (12, 11), (12, 13),
          (13, 10), (13, 11), (13, 12), (13, 13)]
  test = [
      generate(16, 16,
               [[(1, 12), (2, 12), (3, 12), (3, 13)],
                [(8, 9), (8, 10), (9, 9), (9, 10)],
                [(10, 3), (11, 3), (12, 1), (12, 2), (12, 3), (12, 4),
                 (12, 5), (13, 3), (14, 3)]],
               [(5, five, "up"),
                (8, [(8, 11), (9, 11)], "right"),
                (3, [(9, 8)], "left"),
                (6, [(10, 9)], "down"),
                (0, zero, "down"),
                (4, [(13, 1)], "down"),
                (2, [(14, 2)], "left")]),
  ]
  return {"train": train, "test": test}
