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
"""ARC task 5545f144: a mirror-symmetric arrow walks across the panel eating dots.

The input is one or more equal panels separated by full-height divider
columns. The panels are animation snapshots. The first panel holds the start
state: one multi-cell shape plus isolated single dots of the same colour. The
shape is mirror-symmetric about one axis and has a unique tip.

The walk works like this:
- From its tip, the shape moves straight ahead to the nearest dot. It is
  re-stamped with its tip on that dot, and the dot is eaten.
- If nothing lies ahead, the shape turns left or right towards the nearest dot
  in line with the tip, and rotates to face that way.
- If no dot lies ahead or to either side, the walk stops.

Later panels show the state after an increasing number of eaten dots. The
output is one panel showing only the shape at its final position and
orientation.

Scope: by default 1-4 panels, panel height 7-30 and width 6-30 (total width
<= 30). Sizes above the fixture range of 8-15 are synthetic extensions.
Explicit sizes up to 30 are accepted, and up to 6 panels. Background, divider
and shape colours are random and distinct. Arrow shapes are random and
symmetric (depth 1-3, half-width <= 2), with exactly one detectable tip. Walks
have 2-12 eats and mix straight runs with left/right turns. Every dot is
eventually eaten. Left/right turns never tie, dots are never 8-adjacent to each
other, and no shown shape touches a remaining dot.
"""

import random

import common

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _perp(d):
  return (d[1], -d[0])


def _place(shape, tip, d):
  """Maps local (forward, sideways) offsets to grid cells."""
  p = _perp(d)
  return [(tip[0] + a * d[0] + b * p[0], tip[1] + a * d[1] + b * p[1])
          for a, b in shape]


def _inside(cells, h, w):
  return all(0 <= y < h and 0 <= x < w for y, x in cells)


def _halo(cells):
  out = set()
  for y, x in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        out.add((y + dy, x + dx))
  return out


def _connected(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        q = (y + dy, x + dx)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
  return len(seen) == len(cells)


def _qualifying(cells):
  """Lists directions whose extreme cell is unique and lies on a mirror axis."""
  sset = set(cells)
  out = []
  for dy, dx in _DIRS:
    vals = [y * dy + x * dx for y, x in cells]
    m = max(vals)
    ext = [c for c in cells if c[0] * dy + c[1] * dx == m]
    if len(ext) != 1:
      continue
    t = ext[0]
    if dy:
      refl = set((y, 2 * t[1] - x) for y, x in cells)
    else:
      refl = set((2 * t[0] - y, x) for y, x in cells)
    if refl == sset:
      out.append((dy, dx))
  return out


def _check_shape(shape):
  """Validates a user-supplied local shape; returns it as a list of tuples."""
  sh = [tuple(c) for c in shape]
  if (0, 0) not in sh or len(set(sh)) != len(sh) or len(sh) < 3:
    raise ValueError("shape needs >= 3 distinct cells including tip (0, 0)")
  if any(a > 0 for a, _ in sh):
    raise ValueError("shape forward offsets must be <= 0")
  cells = _place(sh, (0, 0), (-1, 0))
  if not _connected(cells) or _qualifying(cells) != [(-1, 0)]:
    raise ValueError("shape must be connected with exactly one symmetric tip")
  return sh


def _sample_shape():
  """Samples a symmetric arrow in local coords; (0, 0) is the tip."""
  for _ in range(300):
    depth = random.randint(1, 3)
    shape = [(0, 0)]
    for a in range(1, depth + 1):
      offs = [s for s in range(3) if random.random() < 0.5]
      if not offs:
        offs = [random.randint(0, 2)]
      for s in offs:
        shape.append((-a, s))
        if s:
          shape.append((-a, -s))
    if len(shape) < 3 or len(shape) > 9:
      continue
    if all(b == 0 for a, b in shape if a == -depth):
      continue
    cells = _place(shape, (0, 0), (-1, 0))
    if not _connected(cells):
      continue
    if _qualifying(cells) != [(-1, 0)]:
      continue
    return shape
  raise ValueError("could not sample a unique-tip arrow")


def _ray(tip, d, dots, h, w):
  y, x = tip[0] + d[0], tip[1] + d[1]
  while 0 <= y < h and 0 <= x < w:
    if (y, x) in dots:
      return (y, x)
    y += d[0]
    x += d[1]
  return None


def _walk(tip, d, dots, h, w):
  """Runs the eating rule. Returns (targets, leftover), or None on a tie."""
  dots = set(dots)
  path = []
  for _ in range(len(dots) + 1):
    nxt = _ray(tip, d, dots, h, w)
    nd = d
    if nxt is None:
      p = _perp(d)
      cands = []
      for c in (p, (-p[0], -p[1])):
        hit = _ray(tip, c, dots, h, w)
        if hit is not None:
          cands.append((abs(hit[0] - tip[0]) + abs(hit[1] - tip[1]), hit, c))
      if not cands:
        break
      if len(cands) == 2 and cands[0][0] == cands[1][0]:
        return None
      cands.sort()
      nxt, nd = cands[0][1], cands[0][2]
    dots.discard(nxt)
    path.append(nxt)
    tip, d = nxt, nd
  return path, dots


def _directions(tip, path):
  dirs = []
  cur = tip
  for t in path:
    dy, dx = t[0] - cur[0], t[1] - cur[1]
    dirs.append(((dy > 0) - (dy < 0), (dx > 0) - (dx < 0)))
    cur = t
  return dirs


def _render(h, w, bg, color, shape, tip, d, dots):
  canvas = common.grid(w, h, bg)
  for y, x in dots:
    canvas[y][x] = color
  for y, x in _place(shape, tip, d):
    if 0 <= y < h and 0 <= x < w:
      canvas[y][x] = color
  return canvas


def _lattice_path(h,w,shape,tip,d,want):
  """Fresh spaced waypoint lattice, followed by the same local eating physics.

  This provides longer controlled walks without a canned fixed scene. A prefix
  of the resulting walk is accepted only after the ordinary full path checks.
  """
  radius=max(max(abs(a),abs(b)) for a,b in shape)
  if not (radius<=tip[0]<h-radius and radius<=tip[1]<w-radius):
    return None
  pitch=radius+2
  sy=d[0] if d[0] else random.choice((-1,1))
  sx=d[1] if d[1] else random.choice((-1,1))
  rows=list(range(tip[0],h-radius if sy>0 else radius-1,sy*pitch))
  cols=list(range(tip[1],w-radius if sx>0 else radius-1,sx*pitch))
  dots={(y,x) for y in rows for x in cols}-{tip}
  if len(dots)<want:
    return None
  walked=_walk(tip,d,dots,h,w)
  if walked is None or len(walked[0])<want:
    return None
  return walked[0][:want]


def _sample_scene(height, width, num_panels, shape, tip, direction, snapshots, num_eats):
  """Builds a dot path that the rule follows exactly; bounded retries."""
  for _ in range(500):
    if num_panels is not None:
      n = num_panels
    elif width is not None:
      n = random.choice([k for k in range(1, 5) if k * width + k - 1 <= 30])
    else:
      n = random.choice([1, 2, 2, 3, 3, 4])
    if width is not None:
      w = width
    else:
      wmax = min(30, (31 - n) // n)
      w = random.randint(min(6, wmax), wmax)
    h = height if height is not None else random.randint(7, 30)
    sh = shape if shape is not None else _sample_shape()
    d0 = direction if direction is not None else random.choice(_DIRS)
    if tip is not None:
      if not _inside(_place(sh, tip, d0), h, w):
        continue
      t0 = tip
    else:
      starts = [(y, x) for y in range(h) for x in range(w)
                if _inside(_place(sh, (y, x), d0), h, w)]
      if not starts:
        continue
      t0 = random.choice(starts)
    blocked = _halo(_place(sh, t0, d0))
    lo = max(2, n)
    if snapshots:
      lo = max(lo, snapshots[-1] + 1)
    hi = max(lo, min(12, (h * w) // 10))
    want = num_eats if num_eats is not None else random.randint(lo, hi)
    if want < lo:
      raise ValueError("num_eats too small for requested snapshots/panels")
    path = []
    cur, cd = t0, d0
    for step in range(want):
      p = _perp(cd)
      turns = [p, (-p[0], -p[1])]
      random.shuffle(turns)
      if random.random() < (0.5 if step == 0 else 0.35):
        order = [cd] + turns
      else:
        order = turns + [cd]
      moved = False
      for nd in order:
        options = []
        for dist in range(2, max(h, w)):
          t = (cur[0] + dist * nd[0], cur[1] + dist * nd[1])
          if not (0 <= t[0] < h and 0 <= t[1] < w):
            break
          if t in blocked:
            continue
          if any(max(abs(t[0] - q[0]), abs(t[1] - q[1])) <= 1 for q in path):
            continue
          if not _inside(_place(sh, t, nd), h, w):
            continue
          options.append(t)
        if options:
          t = random.choice(options)
          path.append(t)
          cur, cd = t, nd
          moved = True
          break
      if not moved:
        break
    if num_eats is not None and len(path)!=want:
      path=_lattice_path(h,w,sh,t0,d0,want) or path
    if len(path) < lo or (num_eats is not None and len(path) != num_eats):
      continue
    res = _walk(t0, d0, path, h, w)
    if res is None or res[0] != path or res[1]:
      continue
    dirs = _directions(t0, path)
    clean = True
    for k in range(1, len(path)):
      halo = _halo(_place(sh, path[k - 1], dirs[k - 1]))
      if any(q in halo for q in path[k:]):
        clean = False
        break
    if not clean:
      continue
    if snapshots is not None:
      snaps = list(snapshots)
    else:
      snaps = sorted(random.sample(range(1, len(path)), n - 1))
    return h, w, n, sh, t0, d0, path, snaps
  raise ValueError("could not construct a scene for the requested parameters")


def generate(height=None, width=None, num_panels=None, bg=None, divider=None,
             color=None, shape=None, tip=None, direction=None, path=None,
             snapshots=None, num_eats=None):
  """Generates one input/output pair.

  Args:
    height: panel height (3-30); random 7-30 if None.
    width: panel width (3-30, num_panels*width + dividers <= 30).
    num_panels: number of snapshot panels, 1-6 (1 means no dividers).
    bg: background colour.
    divider: divider column colour (distinct from bg/colour when used).
    color: colour of the shape and the dots.
    shape: local (forward, sideways) offsets with the tip at (0, 0) and
      forward <= 0. The shape must have exactly one symmetric tip.
    tip: starting tip cell (row, col).
    direction: starting facing direction (dy, dx).
    path: ordered dot cells eaten by the walk; these are all the dots. When
      given, height, width, shape, tip and direction are required, and the
      path is checked against the walk rule.
    num_eats: exact number of dots eaten, 2..20, in random mode.
    snapshots: increasing step counts shown in panels 2..n. These fix
      num_panels to len(snapshots) + 1.
  """
  if num_eats is not None and (not isinstance(num_eats,int) or not 2 <= num_eats <= 20):
    raise ValueError("num_eats must be an integer in 2..20")
  if path is not None and num_eats is not None:
    raise ValueError("num_eats applies only to randomly sampled paths")
  for v in (height, width):
    if v is not None and not 3 <= v <= 30:
      raise ValueError("panel sides must be in 3..30")
  sh = _check_shape(shape) if shape is not None else None
  d0 = None
  if direction is not None:
    d0 = tuple(direction)
    if d0 not in _DIRS:
      raise ValueError("direction must be an axis unit vector")
  t0 = tuple(tip) if tip is not None else None
  snaps = None
  if snapshots is not None:
    snaps = [int(s) for s in snapshots]
    if any(s < 1 for s in snaps) or snaps != sorted(set(snaps)):
      raise ValueError("snapshots must be strictly increasing and >= 1")
    if num_panels is not None and num_panels != len(snaps) + 1:
      raise ValueError("num_panels must equal len(snapshots) + 1")
    num_panels = len(snaps) + 1
  if num_panels is not None and not 1 <= num_panels <= 6:
    raise ValueError("num_panels must be in 1..6")
  if (num_panels is not None and width is not None and
      num_panels * width + num_panels - 1 > 30):
    raise ValueError("total width exceeds 30")
  if path is None:
    h, w, n, sh, t0, d0, path, snaps = _sample_scene(
        height, width, num_panels, sh, t0, d0, snaps, num_eats)
  else:
    if None in (height, width, sh, t0, d0):
      raise ValueError("explicit path needs height, width, shape, tip, direction")
    h, w = height, width
    path = [tuple(q) for q in path]
    if not path or not _inside(path, h, w) or len(set(path)) != len(path):
      raise ValueError("path cells must be distinct and inside the panel")
    if set(path) & set(_place(sh, t0, d0)):
      raise ValueError("dots overlap the starting shape")
    res = _walk(t0, d0, path, h, w)
    if res is None or res[0] != path or res[1]:
      raise ValueError("path is not the walk produced by the rule")
    n = num_panels if num_panels is not None else 1
    if n * w + n - 1 > 30:
      raise ValueError("total width exceeds 30")
    if snaps is None:
      if n - 1 > len(path) - 1:
        raise ValueError("not enough steps for the requested panels")
      snaps = sorted(random.sample(range(1, len(path)), n - 1))
    elif snaps and snaps[-1] >= len(path):
      raise ValueError("snapshot step beyond the walk length")
  for value in (bg,color,divider):
    if value is not None and (not isinstance(value,int) or value not in range(10)):
      raise ValueError("colours must be integers in 0..9")
  if bg is None:
    bg = random.randint(0, 9)
  if color is None:
    color = random.choice([c for c in range(10) if c != bg])
  if color == bg:
    raise ValueError("color must differ from bg")
  if divider is None:
    divider = random.choice([c for c in range(10) if c not in (bg, color)])
  if n > 1 and divider in (bg, color):
    raise ValueError("divider must differ from bg and color")
  dirs = _directions(t0, path)
  if not _inside(_place(sh,t0,d0),h,w) or any(not _inside(_place(sh,q,d),h,w) for q,d in zip(path,dirs)):
    raise ValueError("shape leaves panel during the walk")
  panels = []
  for k in [0] + snaps:
    if k == 0:
      panels.append(_render(h, w, bg, color, sh, t0, d0, path))
    else:
      panels.append(_render(h, w, bg, color, sh, path[k - 1], dirs[k - 1],
                            path[k:]))
  grid_in = []
  for r in range(h):
    row = []
    for i, pan in enumerate(panels):
      if i:
        row.append(divider)
      row.extend(pan[r])
    grid_in.append(row)
  grid_out = _render(h, w, bg, color, sh, path[-1], dirs[-1], [])
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  vee = [(0, 0), (-1, -1), (-1, 1)]
  tee = [(0, 0), (-1, -1), (-1, 0), (-1, 1)]
  arrow = [(0, 0), (-1, 0), (-2, -1), (-2, 1)]
  bird = [(0, 0), (-1, -1), (-1, 0), (-1, 1), (-2, -1), (-2, 1)]
  train = [
      generate(height=10, width=8, num_panels=3, bg=1, divider=3, color=4,
               shape=vee, tip=(2, 5), direction=(0, -1),
               path=[(2, 3), (5, 3), (5, 6), (8, 6), (8, 1), (1, 1)],
               snapshots=[2, 4]),
      generate(height=8, width=6, num_panels=4, bg=0, divider=2, color=3,
               shape=tee, tip=(5, 1), direction=(-1, 0),
               path=[(1, 1), (1, 4), (4, 4), (6, 4)], snapshots=[1, 2, 3]),
      generate(height=12, width=12, num_panels=2, bg=5, divider=4, color=6,
               shape=arrow, tip=(2, 3), direction=(0, 1),
               path=[(2, 6), (2, 10), (5, 10), (5, 7), (5, 4), (5, 2),
                     (9, 2), (9, 5), (7, 5), (0, 5)],
               snapshots=[5]),
  ]
  test = [
      generate(height=15, width=15, num_panels=1, bg=6, divider=0, color=8,
               shape=bird, tip=(5, 7), direction=(-1, 0),
               path=[(1, 7), (1, 12), (3, 12), (3, 9), (3, 3), (8, 3),
                     (8, 1), (13, 1), (13, 6), (13, 10), (6, 10), (6, 4)],
               snapshots=[]),
  ]
  return {"train": train, "test": test}
