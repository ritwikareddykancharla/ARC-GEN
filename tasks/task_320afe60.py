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

"""ARC-GEN style generator for task 320afe60.

Rule: the background is yellow (4) and holds several blue (1) objects. Each
object sits in its own horizontal band of rows, and bands are separated by
blank rows. Every object slides horizontally without changing shape.
  * A "closed" object goes to the left grid edge and becomes red (2). A closed
    object is a solid block, or a ring whose hole is sealed.
  * An "open" object goes to the right grid edge and becomes green (3). An open
    object is a frame with a gap, or a C/U shape with one side missing, so
    background can enter its cavity.
Openness is defined by the orthogonal-convex hull: an object is open exactly
when some cell that the hull adds is connected to the outside background.

Scope: the grid size, the number of objects, and their shapes and positions
are all sampled. Shapes are built from latent parameters:
  * solid blocks;
  * rectangular frames with walls of thickness 1 or 2;
  * optional cut corners;
  * optional bumps on closed frames;
  * an opening, made either by removing one wall side or by a through-gap in
    one side.
The background and the colours 1, 2 and 3 are fixed, as in the task.
"""

import random

import common

BG = 4
FG = 1
LEFT_COLOR = 2
RIGHT_COLOR = 3


def _cells_of(pattern):
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == "1"]


def _to_pattern(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  h = max(r for r, _ in cells) - r0 + 1
  w = max(c for _, c in cells) - c0 + 1
  rows = [["."] * w for _ in range(h)]
  for r, c in cells:
    rows[r - r0][c - c0] = "1"
  return ["".join(row) for row in rows]


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if (nr, nc) in cells and (nr, nc) not in seen:
        seen.add((nr, nc))
        stack.append((nr, nc))
  return len(seen) == len(cells)


def _is_open(pattern):
  """Hull-gap test on one isolated shape (used to sanity-check constructions)."""
  h, w = len(pattern), len(pattern[0])
  shape = set((r + 1, c + 1) for r, c in _cells_of(pattern))
  hull = set(shape)
  changed = True
  while changed:
    changed = False
    for r in range(1, h + 1):
      xs = [c for c in range(1, w + 1) if (r, c) in hull]
      if xs:
        for c in range(xs[0], xs[-1] + 1):
          if (r, c) not in hull:
            hull.add((r, c))
            changed = True
    for c in range(1, w + 1):
      ys = [r for r in range(1, h + 1) if (r, c) in hull]
      if ys:
        for r in range(ys[0], ys[-1] + 1):
          if (r, c) not in hull:
            hull.add((r, c))
            changed = True
  outside = {(0, 0)}
  stack = [(0, 0)]
  while stack:
    r, c = stack.pop()
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if 0 <= nr < h + 2 and 0 <= nc < w + 2 and (nr, nc) not in shape \
          and (nr, nc) not in outside:
        outside.add((nr, nc))
        stack.append((nr, nc))
  return any(cell in outside for cell in hull - shape)


def _make_frame(kind, maxh, maxw):
  hh, hw = random.randint(1, 3), random.randint(1, 4)
  th = {s: random.choice([1, 1, 1, 2]) for s in "tblr"}
  gap = None
  if kind == "open":
    side = random.choice("tblr")
    if random.random() < 0.4:
      th[side] = 0
    else:
      ext = hw if side in "tb" else hh
      length = random.randint(1, ext)
      gap = (side, random.randint(0, ext - length), length)
  oh = th["t"] + hh + th["b"]
  ow = th["l"] + hw + th["r"]
  if oh > maxh or ow > maxw:
    return None
  cells = set()
  for r in range(oh):
    for c in range(ow):
      in_hole = (th["t"] <= r < th["t"] + hh) and (th["l"] <= c < th["l"] + hw)
      if not in_hole:
        cells.add((r, c))
  if gap is not None:
    side, a, length = gap
    for k in range(a, a + length):
      if side == "t":
        for r in range(th["t"]):
          cells.discard((r, th["l"] + k))
      elif side == "b":
        for r in range(th["t"] + hh, oh):
          cells.discard((r, th["l"] + k))
      elif side == "l":
        for c in range(th["l"]):
          cells.discard((th["t"] + k, c))
      else:
        for c in range(th["l"] + hw, ow):
          cells.discard((th["t"] + k, c))
  corners = {(0, 0): "tl", (0, ow - 1): "tr", (oh - 1, 0): "bl",
             (oh - 1, ow - 1): "br"}
  for pos, sides in corners.items():
    if th[sides[0]] >= 1 and th[sides[1]] >= 1 and random.random() < 0.2:
      cells.discard(pos)
  if kind == "closed" and ow >= 3 and oh + 1 <= maxh and random.random() < 0.25:
    length = random.randint(1, ow - 2)
    a = random.randint(1, ow - 1 - length)
    row = -1 if random.random() < 0.5 else oh
    for c in range(a, a + length):
      cells.add((row, c))
  return cells


def _make_shape(kind, maxh, maxw):
  for _ in range(60):
    if kind == "closed" and random.random() < 0.3:
      h = random.randint(1, min(4, maxh))
      w = random.randint(1, min(5, maxw))
      if h * w < 2:
        continue
      cells = set((r, c) for r in range(h) for c in range(w))
    else:
      cells = _make_frame(kind, maxh, maxw)
      if cells is None:
        continue
    if not _connected(cells):
      continue
    pattern = _to_pattern(cells)
    if len(pattern) > maxh or len(pattern[0]) > maxw:
      continue
    if _is_open(pattern) == (kind == "open"):
      return pattern
  raise RuntimeError("Could not construct requested open/closed shape")


def _sample_scene(width, height):
  for _ in range(100):
    W = width if width is not None else random.randint(10, 30)
    H = height if height is not None else random.randint(10, 30)
    n = random.randint(2, max(2, min(6, H // 4)))
    kinds = ["open", "closed"] + [random.choice(["open", "closed"])
                                  for _ in range(n - 2)]
    random.shuffle(kinds)
    shapes = [_make_shape(k, 7, min(W, 9)) for k in kinds]
    total = sum(len(p) for p in shapes) + n - 1
    if total > H:
      continue
    extra = H - total
    slots = [0] * (n + 1)
    for _ in range(extra):
      slots[random.randint(0, n)] += 1
    objects, row = [], slots[0]
    for i, (k, p) in enumerate(zip(kinds, shapes)):
      col = random.randint(0, W - len(p[0]))
      objects.append((row, col, p, "right" if k == "open" else "left"))
      row += len(p) + 1 + slots[i + 1]
    return W, H, objects
  raise RuntimeError("Could not fit open/closed objects in requested grid")


def generate(width=None, height=None, objects=None):
  """Generate one input/output pair.

  Args:
    width: grid width (columns). Sampled from 10..30 if None.
    height: grid height (rows). Sampled from 10..30 if None.
    objects: optional list of (row, col, pattern, side) tuples, where:
      * row, col give the top-left corner of the bounding box in the input;
      * pattern is a list of equal-length strings of '1' and '.';
      * side is 'left' (closed shape, recoloured 2) or 'right' (open shape,
        recoloured 3).
      If None, a fresh random scene is constructed.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Dimensions must be integers in 1..30")
  if objects is None:
    if any(d is not None and d < 10 for d in (width,height)):
      raise ValueError("Random dimensions must be in 10..30")
    width, height, objects = _sample_scene(width, height)
  if width is None or height is None or not objects:
    raise ValueError("Explicit objects require dimensions and nonempty objects")
  bands = []
  for row,col,pattern,side in objects:
    if side not in ('left','right') or not pattern or not pattern[0] or any(len(r) != len(pattern[0]) or any(c not in '.1' for c in r) for r in pattern):
      raise ValueError("Invalid object pattern or side")
    h,w = len(pattern),len(pattern[0])
    if not (0 <= row <= height-h and 0 <= col <= width-w):
      raise ValueError("Object outside grid")
    if not _connected(_cells_of(pattern)) or _is_open(pattern) != (side=='right'):
      raise ValueError("Object must be connected and side must match openness")
    if any(not (row+h < a or b < row) for a,b in bands):
      raise ValueError("Objects require separate row bands")
    bands.append((row,row+h))
  grid_in = common.grid(width, height, BG)
  grid_out = common.grid(width, height, BG)
  for row, col, pattern, side in objects:
    w = len(pattern[0])
    if side == "left":
      dx, color = -col, LEFT_COLOR
    else:
      dx, color = width - (col + w), RIGHT_COLOR
    for r, c in _cells_of(pattern):
      grid_in[row + r][col + c] = FG
      grid_out[row + r][col + c + dx] = color
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical train and test pairs from explicit latent parameters."""
  train = [
      generate(width=22, height=22, objects=[
          (2, 5, ["11111", "11..1", "11111"], "left"),
          (6, 2, ["11", "11"], "left"),
          (9, 6, ["11111", "11111", "1...1", "11.11"], "right"),
          (15, 7, ["1111", "1...", "1111"], "right"),
      ]),
      generate(width=21, height=22, objects=[
          (2, 3, ["11.1", "1..1", "1..1", "1..1", "1111"], "right"),
          (8, 6, ["11111", "1...1", "111.1", "111.1"], "right"),
          (14, 3, ["....11", "111111", "11...1", "11...1", "111111"], "left"),
      ]),
      generate(width=19, height=22, objects=[
          (0, 9, ["1111", "1111"], "left"),
          (3, 2, ["1111", "11.1", "1111"], "left"),
          (8, 5, ["11111", "11..1", "11...", "11111"], "right"),
          (14, 8, ["111", "1.1", "111"], "left"),
          (18, 12, ["111", "..1", "111"], "right"),
      ]),
  ]
  test = [
      generate(width=26, height=22, objects=[
          (2, 5, ["111111", "11...1", "11...1", "11...1", "111..1",
                  "..1111"], "left"),
          (12, 6, ["111.11111", "1.....111", "1.....111", "111111111"],
           "right"),
          (18, 13, ["111", "1.1"], "right"),
      ]),
      generate(width=24, height=22, objects=[
          (1, 2, ["1111", "1..1", "1...", "1111"], "right"),
          (7, 5, ["1111", "11.1", "11.1", "11.1"], "right"),
          (14, 6, [".11111", "11..11", "11..11", "11..11", ".11111"], "left"),
          (20, 4, ["11", "11"], "left"),
      ]),
  ]
  return {"train": train, "test": test}
