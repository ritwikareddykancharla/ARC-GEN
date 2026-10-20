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

"""ARC-GEN style generator for task bf32578f.

Rule: the input holds one open bracket of a single colour on a black (0)
background. The bracket hugs the left side of its bounding box and opens to
the right. To build the output:
  1. Erase the bracket strokes.
  2. Fill every cell inside the bracket. These are the cells of the bounding
     box that lie to the right of the rightmost stroke cell in their row.
  3. Mirror that filling across the bounding box's right edge, using
     mx = 2*x1 + 1 - x.
The result is a left/right symmetric blob of the bracket colour.

Shape model: a bracket is vertically symmetric and 8-connected. It is
described by `offsets`, the left-edge columns of its rows ordered from the
middle row(s) outward. These must be non-decreasing and start at 0. `even`
selects one middle row (odd height 2k-1) or two middle rows (even height 2k).
If consecutive offsets step by s > 1, the inner row gets a horizontal run of
s cells, which keeps the shape 8-connected (as in the test fixture). `cap`
extends the outermost rows to the right, which gives the flat `[` shape.

Supported bounds:
  * 2 <= len(offsets) <= 15, so bracket height is 3..29 (odd) or 4..30
    (even).
  * Explicit x1 = offsets[-1] + cap <= 29 before geometry allocation.
    The actual fit additionally requires 2*x1 - b_min + 1 available columns.
    Random proposals use x1 <= 14, a sufficient but not necessary fit bound;
    wider explicitly supplied stroke runs may also fit.
  * Explicit values outside these bounds are rejected with ValueError before
    any geometry is built.

Random sampling scales with the canvas. Height and span are drawn up to the
full available budget (up to 15 half-rows and x1 up to 14 on 30x30). The step
profile is either regular (an even slope, like the fixtures) or a random
composition (irregular stepped chevrons). Cap is usually 0, sometimes 1..3,
and occasionally anything up to the width budget. Both parities are sampled.

Native versus extension: the fixtures use 6..10 square grids with brackets
5..6 rows tall and 3..4 columns wide. Grids from 3 to 30 per side,
non-square grids, large brackets and irregular step profiles are synthetic
extensions of the same mechanism.

Fixed in every sample, as in all demonstrations: background 0, exactly one
object, right-opening orientation, monotone (non-concave) offsets. The
mirrored blob is always fully inside the grid (it may touch the right
border), so clipped mirrors are out of scope.
"""

import random

import common

_MAX_HALF = 15  # maximum len(offsets)
_MAX_X1 = 29    # bounded explicit coordinates; actual mirror fit checked below


def _is_int(v):
  """True for genuine (non-bool) Python ints."""
  return isinstance(v, int) and not isinstance(v, bool)


def _normalise_offsets(offsets):
  """Validates offsets once and returns a fresh list (or raises ValueError)."""
  if not isinstance(offsets, (list, tuple)):
    raise ValueError("offsets must be a list or tuple of ints")
  offs = list(offsets)
  if len(offs) < 2 or len(offs) > _MAX_HALF:
    raise ValueError("offsets must have 2..%d entries" % _MAX_HALF)
  for o in offs:
    if not _is_int(o):
      raise ValueError("offsets must contain only ints")
  if offs[0] != 0:
    raise ValueError("offsets must start at 0")
  for p, q in zip(offs, offs[1:]):
    if q < p:
      raise ValueError("offsets must be non-decreasing")
  if offs[-1] > _MAX_X1:
    raise ValueError("offsets[-1] must be at most %d" % _MAX_X1)
  return offs


def _check_args(width, height, offsets, even, cap, left, top, colour):
  """Rejects malformed explicit parameters; returns normalised offsets."""
  for name, v in (("width", width), ("height", height), ("cap", cap),
                  ("left", left), ("top", top), ("colour", colour)):
    if v is not None and not _is_int(v):
      raise ValueError(name + " must be an int")
  if even is not None and type(even) is not bool:
    raise ValueError("even must be a bool")
  if width is not None and not 1 <= width <= 30:
    raise ValueError("width must be in 1..30")
  if height is not None and not 1 <= height <= 30:
    raise ValueError("height must be in 1..30")
  if cap is not None and not 0 <= cap <= _MAX_X1:
    raise ValueError("cap must be in 0..%d" % _MAX_X1)
  if left is not None and not 0 <= left <= 29:
    raise ValueError("left must be in 0..29")
  if top is not None and not 0 <= top <= 29:
    raise ValueError("top must be in 0..29")
  if colour is not None and not 1 <= colour <= 9:
    raise ValueError("colour must be in 1..9")
  offs = None
  if offsets is not None:
    offs = _normalise_offsets(offsets)
    if cap is not None and offs[-1] + cap > _MAX_X1:
      raise ValueError("offsets[-1] + cap must be at most %d" % _MAX_X1)
  return offs


def _rows(offsets, even, cap):
  """Returns per-row (start, end) stroke runs, top to bottom, relative to x0."""
  k = len(offsets)
  runs = []
  for i in range(k):
    a = offsets[i]
    if i + 1 < k:
      b = max(a, offsets[i + 1] - 1)
    else:
      b = a + cap
    runs.append((a, b))
  if even:
    order = list(range(k - 1, -1, -1)) + list(range(k))
  else:
    order = list(range(k - 1, 0, -1)) + list(range(k))
  return [runs[i] for i in order]


def _scene(offsets, even, cap):
  """Builds the bracket geometry (bounded inputs), or None if it is empty."""
  runs = _rows(offsets, even, cap)
  x1 = max(b for _, b in runs)
  open_ends = [b for _, b in runs if b < x1]
  if not open_ends:
    return None
  need_w = 2 * x1 - min(open_ends) + 1
  fills = []
  for r, (_, b) in enumerate(runs):
    for x in range(b + 1, x1 + 1):
      fills.append((r, x))
  strokes = sum(b - a + 1 for a, b in runs)
  return {"runs": runs, "x1": x1, "fills": fills, "need_w": need_w,
          "need_h": len(runs), "strokes": strokes}


def _sample_shape(wb, hb, even, cap):
  """Samples (even, cap, offsets) whose bracket and mirror fit wb x hb."""
  evs = []
  if even is not True and hb >= 3:
    evs.append(False)
  if even is not False and hb >= 4:
    evs.append(True)
  ev = random.choice(evs)
  kmax = min(_MAX_HALF, hb // 2 if ev else (hb + 1) // 2)
  if random.random() < 0.4:
    k = random.randint(2, min(kmax, 4))
  else:
    k = random.randint(2, kmax)
  x1max = min(_MAX_X1, (wb - 1) // 2)
  if cap is not None:
    cp = cap
  else:
    r = random.random()
    if r < 0.55:
      cp = 0
    elif r < 0.85:
      cp = random.randint(1, min(3, x1max))
    else:
      cp = random.randint(0, x1max)
  dmin = 1 if cp == 0 else 0
  dmax = x1max - cp
  if dmin > dmax:
    return None
  if random.random() < 0.5:
    d = random.randint(dmin, dmax)
  else:
    d = random.randint(dmin, min(dmax, 2 * (k - 1)))
  n = k - 1
  if random.random() < 0.5:
    # Regular slope: equal steps, remainder spread over random steps.
    steps = [d // n] * n
    for i in random.sample(range(n), d % n):
      steps[i] += 1
  else:
    cuts = sorted(random.randint(0, d) for _ in range(n - 1))
    marks = [0] + cuts + [d]
    steps = [marks[i + 1] - marks[i] for i in range(n)]
  offs = [0]
  for s in steps:
    offs.append(offs[-1] + s)
  return ev, cp, offs


def _pick_size(fixed, need):
  """Picks a grid side length of at least need (and at least 3)."""
  if fixed is not None:
    return fixed
  lo = max(3, need)
  if random.random() < 0.25:
    hi = 30
  else:
    hi = min(30, lo + random.randint(0, 6))
  return random.randint(lo, hi)


def generate(width=None, height=None, offsets=None, even=None, cap=None,
             left=None, top=None, colour=None):
  """Generates one bracket-filling example.

  Args:
    width: grid width (int, 1..30). Random if None.
    height: grid height (int, 1..30). Random if None.
    offsets: list or tuple of 2..15 ints, the left-edge columns of the bracket
      rows ordered from the middle row(s) outward. Must start at 0, be
      non-decreasing and end at most 29. Random if None.
    even: bool. True if the bracket has two middle rows (even height). Random
      if None.
    cap: extra length (int, 0..29) of the flat cap on the outermost rows.
      offsets[-1] + cap must be at most 29; the mirrored output must also fit. Random if None.
    left: column (0..29) of the bracket bounding box's left edge. Random if
      None.
    top: row (0..29) of the bracket bounding box's top edge. Random if None.
    colour: bracket colour (int, 1..9). Random if None.

  Raises:
    ValueError: if the parameters are malformed or admit no valid scene.
  """
  offs_fixed = _check_args(width, height, offsets, even, cap, left, top,
                           colour)
  wmax = width if width is not None else 30
  hmax = height if height is not None else 30
  lx = left if left is not None else 0
  ty = top if top is not None else 0
  wb = wmax - lx
  hb = hmax - ty
  combos = None
  if offs_fixed is not None:
    combos = []
    evs = [even] if even is not None else [False, True]
    if cap is not None:
      caps = [cap]
    else:
      caps = [c for c in range(4) if offs_fixed[-1] + c <= _MAX_X1]
    for ev in evs:
      for cp in caps:
        sc = _scene(offs_fixed, ev, cp)
        if sc is None or sc["need_w"] > wb or sc["need_h"] > hb:
          continue
        if 2 * sc["strokes"] >= wmax * hmax:
          continue
        combos.append((ev, cp))
    if not combos:
      raise ValueError("fixed offsets admit no enclosing bracket that fits")
  else:
    if wb < 3 or hb < 3:
      raise ValueError("grid too small for any bracket and its mirror")
    if even is True and hb < 4:
      raise ValueError("even brackets need at least 4 rows")
    if cap is not None and 2 * max(cap, 1) + 1 > wb:
      raise ValueError("cap too long for the available width")
    if width is not None and height is not None:
      min_rows = 4 if even is True else 3
      min_strokes = min_rows + 2 * (cap if cap is not None else 0)
      if 2 * min_strokes >= width * height:
        raise ValueError("grid too small for a background-majority scene")
  for _ in range(300):
    if combos is not None:
      ev, cp = random.choice(combos)
      offs = list(offs_fixed)
    else:
      shape = _sample_shape(wb, hb, even, cap)
      if shape is None:
        continue
      ev, cp, offs = shape
    sc = _scene(offs, ev, cp)
    if sc is None or sc["need_w"] > wb or sc["need_h"] > hb:
      continue
    W = _pick_size(width, sc["need_w"] + lx)
    H = _pick_size(height, sc["need_h"] + ty)
    if 2 * sc["strokes"] >= W * H:
      continue
    x0 = left if left is not None else random.randint(0, W - sc["need_w"])
    y0 = top if top is not None else random.randint(0, H - sc["need_h"])
    col = colour if colour is not None else random.randint(1, 9)
    x1 = sc["x1"]
    grid = common.grid(W, H, 0)
    out = common.grid(W, H, 0)
    for r, (a, b) in enumerate(sc["runs"]):
      for x in range(a, b + 1):
        grid[y0 + r][x0 + x] = col
    for r, x in sc["fills"]:
      out[y0 + r][x0 + x] = col
      out[y0 + r][x0 + 2 * x1 + 1 - x] = col
    return {"input": grid, "output": out}
  raise ValueError("constraints admit no valid scene within 300 attempts")


def validate():
  """Reconstructs the canonical fixtures from latent parameters."""
  train = [
      generate(width=6, height=6, offsets=[0, 0, 0], even=False, cap=2,
               left=0, top=0, colour=8),
      generate(width=10, height=10, offsets=[0, 1, 2], even=True, cap=0,
               left=2, top=3, colour=7),
      generate(width=6, height=6, offsets=[0, 1, 2], even=False, cap=0,
               left=0, top=1, colour=6),
  ]
  test = [
      generate(width=8, height=8, offsets=[0, 1, 3], even=True, cap=0,
               left=0, top=1, colour=1),
  ]
  return {"train": train, "test": test}
