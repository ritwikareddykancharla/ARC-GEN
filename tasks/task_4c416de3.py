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

"""ARC-GEN style generator for task 4c416de3.

Rule: the scene is a non-zero background holding rectangular outlines
("frames") of colour 0. Some frames are cut off by the grid border. A frame
corner may carry a coloured marker on its inner diagonal at depth D. One
corner (sometimes two) is already fully decorated, and that decoration is the
template. Its deepest diagonal cell is the marker at (D, D). It may also cover
the corner cell, the first cell of each frame arm, and cells just outside the
corner. The output stamps the template at every marked corner that is not yet
decorated. Each stamp is mirrored to that corner's orientation and drawn in
that corner's marker colour. Unmarked corners are left unchanged.

Scope: random grids are 14..30 per side, or 13..30 when a size is requested.
The fixtures are 19..23, so sizes outside that range are synthetic extensions.
There are 1..3 frames with sides 2D+3..14, and frames may be clipped by the
border. Templates are random, symmetric about the diagonal and 8-connected,
inside the window [-2, 3] x [-2, 3]. D is 1 or 2 at random; D = 3 is
available on request. Marker colours are random and may repeat. Distractors
include unmarked corners, corners whose arms are cut by the border, and a
second corner that is already decorated. Explicit latent parameters
reconstruct the canonical fixtures.
"""

import random

import common


def _corners(rect):
  """Corners of a frame as (y, x, dy, dx), where (dy, dx) points inward."""
  t, l, b, r = rect
  return [(t, l, 1, 1), (t, r, 1, -1), (b, l, -1, 1), (b, r, -1, -1)]


def _inside(y, x, height, width):
  return 0 <= y < height and 0 <= x < width


def _frame_cells(rect, height, width):
  t, l, b, r = rect
  cells = set()
  for x in range(l, r + 1):
    for y in (t, b):
      if _inside(y, x, height, width):
        cells.add((y, x))
  for y in range(t, b + 1):
    for x in (l, r):
      if _inside(y, x, height, width):
        cells.add((y, x))
  return cells


def _footprint(y, x, dy, dx, template):
  return [(y + u * dy, x + v * dx) for (u, v) in template]


def _paint(grid, cells, color, height, width):
  for (yy, xx) in cells:
    if _inside(yy, xx, height, width):
      grid[yy][xx] = color


def _depth(template):
  return max(u for (u, v) in template if u == v)


def _check_template(template):
  """Validates a template and returns it as a sorted list of (u, v)."""
  try:
    cells = set((int(u), int(v)) for (u, v) in template)
  except (TypeError, ValueError):
    raise ValueError("template must be a list of (u, v) pairs")
  if len(cells) < 2:
    raise ValueError("template needs at least two cells")
  for (u, v) in cells:
    if not (-2 <= u <= 3 and -2 <= v <= 3):
      raise ValueError("template cell %r is outside [-2, 3] x [-2, 3]" %
                       ((u, v),))
    if (u == 0 and v >= 2) or (v == 0 and u >= 2):
      raise ValueError("template may cover at most one cell of each arm")
  diag = [u for (u, v) in cells if u == v]
  if not diag or max(diag) < 1:
    raise ValueError("template needs a marker cell (D, D) with D >= 1")
  return sorted(cells)


def _detectable(corner, height, width):
  """True if the bare-arm corner signature lies fully inside the grid."""
  y, x, dy, dx = corner
  probes = [(y, x), (y + dy, x + dx), (y + 2 * dy, x), (y + 3 * dy, x),
            (y, x + 2 * dx), (y, x + 3 * dx)]
  return all(_inside(a, b, height, width) for (a, b) in probes)


def _render(width, height, background, frames, template, marks, decorated):
  """Draws the input from latent parameters and stamps the output."""
  if not isinstance(width, int) or not isinstance(height, int):
    raise ValueError("width and height must be integers")
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("width and height must lie in 1..30")
  if background not in range(1, 10):
    raise ValueError("background must be a colour in 1..9")
  template = _check_template(template)
  depth = _depth(template)
  grid = common.grid(width, height, background)
  orient = {}
  for frame in frames:
    rect = tuple(int(z) for z in frame)
    if len(rect) != 4 or rect[2] - rect[0] < 4 or rect[3] - rect[1] < 4:
      raise ValueError("frames are (top, left, bottom, right), sides >= 5")
    _paint(grid, _frame_cells(rect, height, width), 0, height, width)
    for (y, x, dy, dx) in _corners(rect):
      orient[(y, x)] = (dy, dx)
  colour_of = {}
  for (y, x, color) in marks:
    if (y, x) not in orient or not _inside(y, x, height, width):
      raise ValueError("mark %r is not a visible frame corner" % ((y, x),))
    if color not in range(1, 10) or color == background:
      raise ValueError("marker colours must be 1..9 and not background")
    if (y, x) in colour_of:
      raise ValueError("corner %r is marked twice" % ((y, x),))
    colour_of[(y, x)] = color
  deco = set((int(p[0]), int(p[1])) for p in decorated)
  if not deco:
    raise ValueError("at least one decorated template corner is required")
  if not deco <= set(colour_of):
    raise ValueError("decorated corners must also be marked")
  for (y, x), color in colour_of.items():
    dy, dx = orient[(y, x)]
    if (y, x) in deco:
      cells = _footprint(y, x, dy, dx, template)
    else:
      cells = [(y + depth * dy, x + depth * dx)]
    _paint(grid, cells, color, height, width)
  output = [row[:] for row in grid]
  for (y, x), color in colour_of.items():
    if (y, x) not in deco:
      dy, dx = orient[(y, x)]
      _paint(output, _footprint(y, x, dy, dx, template), color, height, width)
  return {"input": grid, "output": output}


def _make_template(depth):
  """Random diagonal-symmetric 8-connected decoration with marker (D, D)."""
  pool = []
  for u in range(-2, 4):
    for v in range(-2, 4):
      if (u == 0 and v >= 2) or (v == 0 and u >= 2):
        continue  # frame arm cells beyond distance 1 stay bare
      if u == v and u > depth:
        continue  # the marker is the deepest diagonal cell
      pool.append((u, v))
  for _ in range(60):
    target = random.randint(3, 9)
    cells = {(depth, depth)}
    for _ in range(14):
      if len(cells) >= target:
        break
      cands = [p for p in pool if p not in cells and any(
          abs(p[0] - a) <= 1 and abs(p[1] - b) <= 1 for (a, b) in cells)]
      if not cands:
        break
      weights = [1.0 / (1 + abs(u) + abs(v)) ** 1.5 for (u, v) in cands]
      u, v = random.choices(cands, weights=weights)[0]
      cells.add((u, v))
      cells.add((v, u))
    if len(cells) < 3 or len(cells) > 10:
      continue
    if not any(min(u, v) <= 0 for (u, v) in cells):
      continue
    return sorted(cells)
  return None


def _rects_close(a, b):
  return (a[0] - 2 <= b[2] and b[0] - 2 <= a[2] and
          a[1] - 2 <= b[3] and b[1] - 2 <= a[3])


def _near(cells_a, cells_b):
  for (y, x) in cells_a:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        if (y + a, x + b) in cells_b:
          return True
  return False


def _signature_corners(g, height, width):
  """Cells that look like frame corners (bare arms 2-3 out, filled diagonal)."""
  def get(y, x):
    return g[y][x] if _inside(y, x, height, width) else -1
  found = set()
  for y in range(height):
    for x in range(width):
      for dy in (1, -1):
        for dx in (1, -1):
          if (get(y + 2 * dy, x) == 0 and get(y + 3 * dy, x) == 0 and
              get(y, x + 2 * dx) == 0 and get(y, x + 3 * dx) == 0 and
              get(y + dy, x + dx) not in (0, -1)):
            found.add((y, x, dy, dx))
  return found


def _window_counts(g, height, width, bg, y, x, dy, dx):
  counts = {}
  for u in range(-2, 4):
    for v in range(-2, 4):
      yy, xx = y + u * dy, x + v * dx
      if _inside(yy, xx, height, width):
        k = g[yy][xx]
        if k != 0 and k != bg:
          counts.setdefault(k, set()).add((u, v))
  return counts


def _try_scene(W, H, bg, tmpl, nframes):
  """One attempt at a random scene; returns None if a constraint fails."""
  depth = _depth(tmpl)
  lo = 2 * depth + 3
  hi_h, hi_w = min(14, H - 2), min(14, W - 2)
  frames = []
  for i in range(nframes):
    lo_i = lo + 1 if i == 0 else lo
    if hi_h < lo_i or hi_w < lo_i:
      return None
    rect = None
    for _ in range(40):
      h = random.randint(lo_i, hi_h)
      w = random.randint(lo_i, hi_w)
      if random.random() < 0.3:
        t = random.randint(-(h - 4), H - 4)
        l = random.randint(-(w - 4), W - 4)
      else:
        t = random.randint(1, H - h - 1)
        l = random.randint(1, W - w - 1)
      cand = (t, l, t + h - 1, l + w - 1)
      if not any(_rects_close(cand, f) for f in frames):
        rect = cand
        break
    if rect is None:
      return None
    frames.append(rect)

  def usable(c):
    return _detectable(c, H, W) and all(
        _inside(a, b, H, W) for (a, b) in _footprint(c[0], c[1], c[2], c[3],
                                                     tmpl))

  visible = [(idx, c) for idx, rect in enumerate(frames)
             for c in _corners(rect) if _inside(c[0], c[1], H, W)]
  first = [c for (idx, c) in visible if idx == 0 and usable(c)]
  if not first:
    return None
  tc = random.choice(first)
  palette = [k for k in range(1, 10) if k != bg]
  marks = [(0, tc, random.choice(palette))]
  prints = [set(_footprint(tc[0], tc[1], tc[2], tc[3], tmpl))]
  others = [(idx, c) for (idx, c) in visible if c != tc and usable(c)]
  random.shuffle(others)
  for (idx, c) in others:
    if random.random() >= 0.85:
      continue  # unmarked distractor corner
    cset = set(_footprint(c[0], c[1], c[2], c[3], tmpl))
    if any(_near(cset, p) for p in prints):
      continue  # would collide with another stamp; leave unmarked
    marks.append((idx, c, random.choice(palette)))
    prints.append(cset)
  if len(marks) < 2:
    return None
  decorated = {(tc[0], tc[1])}
  if len(marks) >= 3 and random.random() < 0.25:
    extra = random.choice(marks[1:])[1]
    decorated.add((extra[0], extra[1]))
  groups = [_frame_cells(rect, H, W) for rect in frames]
  for (idx, c, color), cset in zip(marks, prints):
    groups[idx] = groups[idx] | cset
  for i in range(len(groups)):
    for j in range(i + 1, len(groups)):
      if _near(groups[i], groups[j]):
        return None
  mark_list = [(c[0], c[1], color) for (idx, c, color) in marks]
  pair = _render(W, H, bg, frames, tmpl, mark_list, sorted(decorated))
  g = pair["input"]
  detect = set(c for (idx, c) in visible if _detectable(c, H, W))
  if _signature_corners(g, H, W) != detect:
    return None
  colour_of = dict(((c[0], c[1]), color) for (idx, c, color) in marks)
  tset = set(tmpl)
  for (y, x, dy, dx) in detect:
    counts = _window_counts(g, H, W, bg, y, x, dy, dx)
    if (y, x) in decorated:
      if counts.get(colour_of[(y, x)], set()) != tset:
        return None
      continue
    if any(len(s) >= len(tset) for s in counts.values()):
      return None
    if (y, x) not in colour_of:
      yy, xx = y + depth * dy, x + depth * dx
      if _inside(yy, xx, H, W) and g[yy][xx] != bg:
        return None
  return pair


def _single_frame_scene(W, H, bg, tmpl):
  """Randomised one-frame scene that is valid by construction.

  A frame with sides >= 9 and every corner at least 2 cells from the border
  keeps all footprints inside the grid and at least 2 cells apart, and keeps
  every window [-2, 3]^2 free of other footprints. Requires W, H >= 13.
  """
  sh = random.randint(9, min(14, H - 4))
  sw = random.randint(9, min(14, W - 4))
  t = random.randint(2, H - 2 - sh)
  l = random.randint(2, W - 2 - sw)
  rect = (t, l, t + sh - 1, l + sw - 1)
  corners = _corners(rect)
  tc = random.choice(corners)
  others = [c for c in corners if c != tc]
  marked = [c for c in others if random.random() < 0.85]
  if not marked:
    marked = [random.choice(others)]
  palette = [k for k in range(1, 10) if k != bg]
  marks = [(tc[0], tc[1], random.choice(palette))]
  marks += [(c[0], c[1], random.choice(palette)) for c in marked]
  return _render(W, H, bg, [rect], tmpl, marks, [(tc[0], tc[1])])


def _size(value, name):
  if value is None:
    return random.randint(14, 30)
  if not isinstance(value, int) or not 13 <= value <= 30:
    raise ValueError("%s must be an integer in 13..30 for random scenes" %
                     name)
  return value


def generate(width=None, height=None, background=None, frames=None,
             template=None, marks=None, decorated=None, depth=None,
             num_frames=None):
  """Returns an input/output pair for task 4c416de3.

  Args:
    width: grid width. Random 14..30 if None. Must be 13..30 when given for
      a random scene, and 1..30 for an explicit scene.
    height: grid height, with the same ranges as width.
    background: background colour 1..9 (random if None).
    frames: list of (top, left, bottom, right) rectangles of colour 0, with
      sides >= 5. They may extend beyond the grid. Passing frames, marks or
      decorated selects an explicit scene. An explicit scene then requires
      width, height, background, frames, template, marks and decorated.
    template: list of (u, v) decoration offsets in corner coordinates. u runs
      inward along rows and v inward along columns. The cell (D, D) with the
      largest diagonal index D >= 1 is the marker. Optional for random scenes;
      there it must have at least 3 cells.
    marks: list of (y, x, colour) giving the marker colour of each frame
      corner. Corners that are not listed are unmarked.
    decorated: list of (y, x) marked corners that are already decorated in
      the input.
    depth: marker depth D in 1..3 for random scenes (random 1..2 if None).
      Must agree with template if both are given.
    num_frames: number of frames 1..3 for random scenes (random if None).
  """
  if frames is not None or marks is not None or decorated is not None:
    needed = (("width", width), ("height", height),
              ("background", background), ("frames", frames),
              ("template", template), ("marks", marks),
              ("decorated", decorated))
    missing = [name for (name, value) in needed if value is None]
    if missing:
      raise ValueError("explicit scene is missing: " + ", ".join(missing))
    if num_frames is not None and num_frames != len(frames):
      raise ValueError("num_frames disagrees with frames")
    if depth is not None and depth != _depth(_check_template(template)):
      raise ValueError("depth disagrees with template")
    return _render(width, height, background, frames, template, marks,
                   decorated)
  W = _size(width, "width")
  H = _size(height, "height")
  if background is None:
    bg = random.randint(1, 9)
  elif background in range(1, 10):
    bg = background
  else:
    raise ValueError("background must be a colour in 1..9")
  if num_frames is not None and num_frames not in (1, 2, 3):
    raise ValueError("num_frames must be 1, 2 or 3")
  fixed = None
  if template is not None:
    fixed = _check_template(template)
    if len(fixed) < 3:
      raise ValueError("random scenes need a template of at least 3 cells")
    if depth is not None and depth != _depth(fixed):
      raise ValueError("depth disagrees with template")
    d = _depth(fixed)
  elif depth is None:
    d = random.choice([1, 2])
  elif depth in (1, 2, 3):
    d = depth
  else:
    raise ValueError("depth must be 1, 2 or 3")
  for _ in range(400):
    tmpl = fixed if fixed is not None else _make_template(d)
    if tmpl is None:
      continue
    n = num_frames
    if n is None:
      n = random.choices([1, 2, 3], weights=[2, 5, 3])[0]
    pair = _try_scene(W, H, bg, tmpl, n)
    if pair is not None:
      return pair
  if num_frames not in (None, 1):
    raise ValueError("could not place %d frames in a %dx%d grid" %
                     (num_frames, W, H))
  tmpl = fixed
  for _ in range(400):
    if tmpl is not None:
      break
    tmpl = _make_template(d)
  if tmpl is None:
    raise RuntimeError("could not sample a template of depth %d" % d)
  return _single_frame_scene(W, H, bg, tmpl)


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=21, height=21, background=1,
               frames=[(3, 3, 10, 10), (17, 13, 24, 24)],
               template=[(-1, -1), (-1, 0), (0, -1), (0, 0), (1, 1), (2, 2)],
               marks=[(3, 3, 3), (3, 10, 8), (10, 3, 4), (10, 10, 2),
                      (17, 13, 4)],
               decorated=[(3, 10)]),
      generate(width=23, height=23, background=8,
               frames=[(3, 5, 9, 11), (15, 7, 19, 11)],
               template=[(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)],
               marks=[(3, 5, 1), (3, 11, 4), (9, 5, 6), (9, 11, 3),
                      (15, 7, 2), (15, 11, 7), (19, 7, 3), (19, 11, 4)],
               decorated=[(3, 5), (9, 11)]),
      generate(width=21, height=21, background=2,
               frames=[(2, 2, 6, 6), (-2, 16, 5, 22), (12, 4, 18, 10)],
               template=[(-1, 0), (0, -1), (0, 0), (1, 1)],
               marks=[(2, 2, 1), (2, 6, 3), (6, 6, 4), (5, 16, 9),
                      (12, 4, 8), (12, 10, 9), (18, 4, 3), (18, 10, 8)],
               decorated=[(6, 6)]),
  ]
  test = [
      generate(width=22, height=19, background=3,
               frames=[(2, 2, 7, 7), (5, 13, 12, 20), (14, -2, 21, 6)],
               template=[(-1, 0), (0, -1), (0, 0), (1, 1), (1, 2), (2, 1)],
               marks=[(2, 2, 4), (7, 7, 1), (5, 13, 2), (5, 20, 6),
                      (12, 20, 8), (14, 6, 5)],
               decorated=[(5, 13)]),
  ]
  return {"train": train, "test": test}
