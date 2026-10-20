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

"""Generator for ARC task f5c89df1 (anchored shape stamping).

Rule: the input holds three kinds of cells.
  * One 8-connected shape coloured 8.
  * Exactly one 3 cell, the shape's anchor, inside the shape or touching its
    edge.
  * One or more 2 cells, the targets.
The output starts as a blank (0) canvas. For every 2, a copy of the 8-cells
is stamped, translated by (target - anchor). The original shape, the anchor
and the targets are all erased. The anchor cell counts as background in each
copy, overlapping copies simply stay 8, and stamped cells that fall outside
the grid are dropped.

Scope: the canonical fixtures are all 13x13 and never clip. Random scenes
use grids of 8..22 per side. This is a synthetic extension: the rule does
not depend on the grid size, and explicit sizes of 1..30 are accepted.

Shapes are random 8-connected blobs grown next to the anchor. They are
optionally mirrored left/right and/or up/down about the anchor. A random
shape is kept only if all of the following hold, as in every fixture:
  * it is a single 8-connected component,
  * at least one 8 is 4-adjacent to the 3,
  * the 3 lies inside the shape's bounding box.

Each scene has 1..4 targets by default, or 1..8 via num_targets. With some
probability the targets are clustered so that their stamps overlap, as in
train pair 2. Random targets are placed so that:
  * every stamp fits fully inside the grid,
  * no target sits on the shape or the anchor,
  * no target sits in a hole enclosed by the shape.
Clipping can therefore only appear when targets or the anchor are supplied
explicitly. Even then, every target's stamp must keep at least one in-grid
cell, so each target leaves visible evidence of the rule.

The colours 0 / 8 / 3 / 2 are intrinsic to the task and stay fixed. The
background 0 is always the strict majority colour of the input.
"""

import random
import common


_NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
               (1, 1)]
_ORTHO = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _is_int(value):
  """Returns True for genuine ints (bools are rejected).

  Args:
    value: any value
  """
  return isinstance(value, int) and not isinstance(value, bool)


def _as_cell(value, name):
  """Converts a 2-element int sequence to a tuple, or raises ValueError.

  Args:
    value: candidate (row, col) or (dy, dx) pair
    name: label used in the error message
  """
  if (not isinstance(value, (list, tuple)) or len(value) != 2 or
      not all(_is_int(v) for v in value)):
    raise ValueError(name + " must be a pair of ints")
  return (value[0], value[1])


def _is_connected(cells):
  """Returns True if the given cells form exactly one 8-connected component.

  Args:
    cells: iterable of (row, col) or (dy, dx) tuples
  """
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in _NEIGHBOURS:
      n = (y + dy, x + dx)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _check_shape(shape):
  """Raises ValueError unless the shape offsets are a valid anchored shape.

  Args:
    shape: list of (dy, dx) offsets of the 8-cells relative to the anchor
  """
  if not shape or len(set(shape)) != len(shape) or (0, 0) in shape:
    raise ValueError("shape must be non-empty, distinct, and exclude (0, 0)")
  if not _is_connected(shape):
    raise ValueError("shape cells must form one 8-connected component")
  if not any(max(abs(dy), abs(dx)) == 1 for dy, dx in shape):
    raise ValueError("anchor must touch the shape")


def _enclosed_holes(occupied):
  """Returns the empty cells that the occupied cells enclose (4-connectivity).

  Args:
    occupied: set of absolute (row, col) cells of the shape and the anchor
  """
  r0 = min(r for r, _ in occupied) - 1
  r1 = max(r for r, _ in occupied) + 1
  c0 = min(c for _, c in occupied) - 1
  c1 = max(c for _, c in occupied) + 1
  start = (r0, c0)
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in _ORTHO:
      n = (y + dy, x + dx)
      if (r0 <= n[0] <= r1 and c0 <= n[1] <= c1 and n not in occupied and
          n not in seen):
        seen.add(n)
        stack.append(n)
  holes = set()
  for r in range(r0 + 1, r1):
    for c in range(c0 + 1, c1):
      if (r, c) not in occupied and (r, c) not in seen:
        holes.add((r, c))
  return holes


def _grow_shape(box_h, box_w, n_cells):
  """Grows an 8-connected set of offsets next to (0, 0), excluding (0, 0).

  Args:
    box_h: height of the bounding box (which contains the anchor) the blob
      may occupy
    box_w: width of the bounding box the blob may occupy
    n_cells: desired number of shape cells (excluding the anchor)
  """
  ay0 = random.randint(0, box_h - 1)
  ax0 = random.randint(0, box_w - 1)

  def inside(dy, dx):
    return (-ay0 <= dy <= box_h - 1 - ay0 and
            -ax0 <= dx <= box_w - 1 - ax0 and (dy, dx) != (0, 0))

  # Seed with an orthogonal neighbour so the 3 has a 4-adjacent 8.
  seeds = [n for n in _ORTHO if inside(*n)]
  cells = {random.choice(seeds)}
  for _ in range(400):
    if len(cells) >= n_cells:
      break
    dy, dx = random.choice(sorted(cells))
    sy, sx = random.choice(_NEIGHBOURS)
    ny, nx = dy + sy, dx + sx
    if (ny, nx) in cells or not inside(ny, nx):
      continue
    cells.add((ny, nx))
  return cells


def _sample_shape():
  """Samples shape offsets relative to the anchor, or returns None."""
  for _ in range(100):
    box_h = random.randint(3, 6)
    box_w = random.randint(3, 6)
    n_cells = random.randint(3, min(14, box_h * box_w - 1))
    cells = _grow_shape(box_h, box_w, n_cells)
    if random.random() < 0.5:
      cells |= {(dy, -dx) for (dy, dx) in cells}
    if random.random() < 0.3:
      cells |= {(-dy, dx) for (dy, dx) in cells}
    cells.discard((0, 0))
    if len(cells) < 3 or not _is_connected(cells):
      continue
    if not any(abs(dy) + abs(dx) == 1 for dy, dx in cells):
      continue
    if not (min(dy for dy, _ in cells) <= 0 <= max(dy for dy, _ in cells) and
            min(dx for _, dx in cells) <= 0 <= max(dx for _, dx in cells)):
      continue
    return sorted(cells)
  return None


def _check_scene(width, height, anchor, shape, targets):
  """Raises ValueError if the explicit scene parameters are inconsistent.

  Args:
    width: grid width
    height: grid height
    anchor: (row, col) of the 3 cell
    shape: list of (dy, dx) offsets of the 8-cells relative to the anchor
    targets: list of (row, col) positions of the 2 cells
  """
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid size must be within 1..30")
  _check_shape(shape)
  ay, ax = anchor
  if not (0 <= ay < height and 0 <= ax < width):
    raise ValueError("anchor out of bounds")
  occupied = {(ay, ax)}
  for dy, dx in shape:
    if not (0 <= ay + dy < height and 0 <= ax + dx < width):
      raise ValueError("shape cell out of bounds")
    occupied.add((ay + dy, ax + dx))
  if not targets or len(set(targets)) != len(targets):
    raise ValueError("targets must be non-empty and distinct")
  for ty, tx in targets:
    if not (0 <= ty < height and 0 <= tx < width):
      raise ValueError("target out of bounds")
    if (ty, tx) in occupied:
      raise ValueError("target overlaps the shape or the anchor")
    if not any(0 <= ty + dy < height and 0 <= tx + dx < width
               for dy, dx in shape):
      raise ValueError("a target's stamp is clipped away entirely")
  non_background = len(occupied) + len(targets)
  if 2 * non_background >= width * height:
    raise ValueError("background 0 must remain the strict majority colour")


def _build(width, height, anchor, shape, targets):
  """Builds the input and output grids from the explicit scene parameters.

  Args:
    width: grid width
    height: grid height
    anchor: (row, col) of the 3 cell
    shape: list of (dy, dx) offsets of the 8-cells relative to the anchor
    targets: list of (row, col) positions of the 2 cells
  """
  grid = common.grid(width, height, 0)
  output = common.grid(width, height, 0)
  ay, ax = anchor
  for dy, dx in shape:
    grid[ay + dy][ax + dx] = 8
  grid[ay][ax] = 3
  for ty, tx in targets:
    grid[ty][tx] = 2
  for ty, tx in targets:
    for dy, dx in shape:
      ny, nx = ty + dy, tx + dx
      if 0 <= ny < height and 0 <= nx < width:
        output[ny][nx] = 8
  return {"input": grid, "output": output}


def generate(width=None, height=None, anchor=None, shape=None, targets=None,
             num_targets=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the grid as an int (random 8..22 if None; 1..30
      allowed)
    height: the height of the grid as an int (random 8..22 if None; 1..30
      allowed)
    anchor: (row, col) of the single 3 cell (random if None)
    shape: list of (dy, dx) offsets of the 8-cells relative to the anchor.
      It must be one 8-connected component touching the anchor and must
      exclude (0, 0). A random blob is used if None.
    targets: list of (row, col) positions of the 2 cells (random if None).
      Explicit targets may clip at the border, but every stamp must keep at
      least one in-grid cell.
    num_targets: number of targets to sample, 1..8 (random 1..4 if None).
      It must equal len(targets) when both are given.
  """
  for name, value in (("width", width), ("height", height),
                      ("num_targets", num_targets)):
    if value is not None and not _is_int(value):
      raise ValueError(name + " must be an int")
  if width is None:
    width = random.randint(8, 22)
  if height is None:
    height = random.randint(8, 22)
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid size must be within 1..30")
  if num_targets is not None and not 1 <= num_targets <= 8:
    raise ValueError("num_targets must be within 1..8")
  if shape is not None:
    if not isinstance(shape, (list, tuple)):
      raise ValueError("shape must be a list of offsets")
    shape = [_as_cell(c, "shape offset") for c in shape]
    _check_shape(shape)
  if anchor is not None:
    anchor = _as_cell(anchor, "anchor")
    if not (0 <= anchor[0] < height and 0 <= anchor[1] < width):
      raise ValueError("anchor out of bounds")
    if shape is not None:
      for dy, dx in shape:
        if not (0 <= anchor[0] + dy < height and 0 <= anchor[1] + dx < width):
          raise ValueError("shape cell out of bounds")
  if targets is not None:
    if not isinstance(targets, (list, tuple)):
      raise ValueError("targets must be a list of cells")
    targets = [_as_cell(t, "target") for t in targets]
    if not targets or len(set(targets)) != len(targets):
      raise ValueError("targets must be non-empty and distinct")
    for ty, tx in targets:
      if not (0 <= ty < height and 0 <= tx < width):
        raise ValueError("target out of bounds")
    if num_targets is not None and num_targets != len(targets):
      raise ValueError("num_targets does not match len(targets)")
    if anchor is not None and anchor in targets:
      raise ValueError("target overlaps the anchor")
  if anchor is not None and shape is not None and targets is not None:
    _check_scene(width, height, anchor, shape, targets)
    return _build(width, height, anchor, shape, targets)

  for _ in range(300):
    cur_shape = shape if shape is not None else _sample_shape()
    if not cur_shape:
      continue
    miny = min(min(dy for dy, _ in cur_shape), 0)
    maxy = max(max(dy for dy, _ in cur_shape), 0)
    minx = min(min(dx for _, dx in cur_shape), 0)
    maxx = max(max(dx for _, dx in cur_shape), 0)
    span_h = maxy - miny + 1
    span_w = maxx - minx + 1
    # Anchor / target positions for which a whole stamp fits in the grid.
    rows = list(range(-miny, height - maxy))
    cols = list(range(-minx, width - maxx))
    if not rows or not cols:
      continue
    if anchor is not None:
      cur_anchor = anchor
      if cur_anchor[0] not in rows or cur_anchor[1] not in cols:
        continue
    else:
      cur_anchor = (random.choice(rows), random.choice(cols))
    ay, ax = cur_anchor
    occupied = {(ay + dy, ax + dx) for dy, dx in cur_shape} | {(ay, ax)}
    if targets is not None:
      cur_targets = targets
      if any(t in occupied for t in cur_targets):
        continue
    else:
      holes = _enclosed_holes(occupied)
      candidates = [(r, c) for r in rows for c in cols
                    if (r, c) not in occupied and (r, c) not in holes]
      if num_targets is not None:
        k = num_targets
      else:
        k = random.choices([1, 2, 3, 4], weights=[3, 4, 2, 2])[0]
      if len(candidates) < k:
        continue
      if k >= 2 and random.random() < 0.4:
        # Cluster targets so that their stamps overlap (as in train pair 2).
        first = random.choice(candidates)
        near = [p for p in candidates if p != first and
                abs(p[0] - first[0]) < span_h and
                abs(p[1] - first[1]) < span_w]
        if len(near) < k - 1:
          continue
        cur_targets = [first] + random.sample(near, k - 1)
      else:
        cur_targets = random.sample(candidates, k)
    try:
      _check_scene(width, height, cur_anchor, cur_shape, cur_targets)
    except ValueError:
      continue
    return _build(width, height, cur_anchor, cur_shape, cur_targets)
  raise ValueError("could not construct a valid scene from the given "
                   "parameters")


def validate():
  """Validates the generator against the canonical fixtures."""
  train = [
      generate(width=13, height=13, anchor=(5, 6),
               shape=[(-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -2), (0, 2),
                      (1, -1), (1, 0), (1, 1), (2, 0)],
               targets=[(5, 3), (5, 9)]),
      generate(width=13, height=13, anchor=(4, 5),
               shape=[(-1, 0), (0, -1), (0, 1), (1, 0)],
               targets=[(3, 4), (3, 6), (5, 4), (5, 6)]),
      generate(width=13, height=13, anchor=(9, 4),
               shape=[(-3, 0), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
                      (-1, -2), (-1, -1), (-1, 1), (-1, 2), (0, -2), (0, -1),
                      (0, 1), (0, 2)],
               targets=[(5, 4)]),
  ]
  test = [
      generate(width=13, height=13, anchor=(6, 5),
               shape=[(-2, -1), (-2, 1), (-1, -2), (-1, -1), (-1, 1), (-1, 2),
                      (0, -1), (0, 1), (1, 0)],
               targets=[(3, 2), (3, 8)]),
  ]
  return {"train": train, "test": test}
