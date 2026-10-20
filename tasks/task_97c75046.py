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

"""ARC task 97c75046: roll a ball onto a staircase and slide it diagonally.

Rule: the background is 7. The grid holds one 4-connected staircase-like
object of colour 0 and a single 5 cell. The 5 lies on a row or column line
that runs into the 0-shape. It first moves straight toward the shape until the
next cell is a 0. It then picks the one sideways diagonal (forward plus one
side) whose cell is free and still 8-touches the shape. It keeps sliding along
that same diagonal while the next diagonal cell is inside the grid, is not
shape and still 8-touches the shape. The 5 is removed from its start cell and
drawn at its resting cell.

Scope and construction. Every scene is built in a canonical frame where the 5
falls downward. The shape is a set of vertical runs, at most one per column.
Random shapes have run tops that form a rising or falling staircase, a single
peak, or a single valley, with steps of 0, 1 or 2 rows. All runs cover a
common base row, so the shape is 4-connected. The 5 starts strictly above
every shape cell, at least two rows above the topmost 0. So it never 8-touches
the shape at the start, only the downward ray meets the shape, and it always
moves.

Ambiguity guards. Scenes are rejected, both random and explicit, in three
cases.
  * Both diagonal slides are legal on landing (side choice is unestablished).
  * A visited cell (landing, slide or rest) is not 4-adjacent to the shape.
    In the fixtures 8-contact and 4-contact always coincide.
  * A visited cell has a forward cell that is free and 4-adjacent to the
    shape. A rule that keeps falling while hugging a wall would then disagree,
    and no fixture settles that. This is the slide-off-a-tall-side-wall case.

Orientation. The canonical scene is optionally transposed and then flipped by
rows and/or columns. That covers all 8 dihedral orientations, so all four
approach directions and both slide handednesses occur.

IMPORTANT: height and width are CANONICAL-frame dimensions. When transpose is
True the emitted grid has width rows and height columns.

Random canonical sizes are 6..22 rows and 5..18 columns by default. Requested
sizes may be 5..30 rows and 3..30 columns. Both are synthetic extensions of
the fixture sizes.
"""

import common
import random


BG = 7
SHAPE = 0
BALL = 5


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_flag(name, v):
  if v is not None and not isinstance(v, bool):
    raise ValueError(name + " must be a bool or None")


def _check_size(name, v, lo, hi):
  if v is None:
    return
  if not _is_int(v):
    raise ValueError(name + " must be an int")
  if not lo <= v <= hi:
    raise ValueError("%s must be in %d..%d" % (name, lo, hi))


def _normalize_columns(columns):
  if not isinstance(columns, (list, tuple)):
    raise ValueError("columns must be a list")
  out = []
  for run in columns:
    if run is None:
      out.append(None)
      continue
    if (not isinstance(run, (list, tuple)) or len(run) != 2
        or not all(_is_int(v) for v in run)):
      raise ValueError("each column entry must be None or (top, bottom) ints")
    out.append((run[0], run[1]))
  return out


def _normalize_marker(marker):
  if (not isinstance(marker, (list, tuple)) or len(marker) != 2
      or not all(_is_int(v) for v in marker)):
    raise ValueError("marker must be a (row, col) pair of ints")
  return marker[0], marker[1]


def _shape_cells(height, width, columns):
  cells = [[False] * width for _ in range(height)]
  for c, run in enumerate(columns):
    if run is None:
      continue
    top, bottom = run
    for r in range(top, bottom + 1):
      cells[r][c] = True
  return cells


def _settle(shape, height, width, y, x):
  """Return (final_cell, visited_path) in the canonical frame.

  Returns None if the slide direction is ambiguous. The path contains the
  straight-run landing cell and every diagonal slide cell.
  """

  def inside(a, b):
    return 0 <= a < height and 0 <= b < width

  def touches(a, b):
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        if inside(a + dy, b + dx) and shape[a + dy][b + dx]:
          return True
    return False

  def valid(a, b):
    return inside(a, b) and not shape[a][b] and touches(a, b)

  while y + 1 < height and not shape[y + 1][x]:
    y += 1
  path = [(y, x)]
  options = [dx for dx in (1, -1) if valid(y + 1, x + dx)]
  if len(options) == 2:
    return None
  if options:
    dx = options[0]
    while valid(y + 1, x + dx):
      y += 1
      x += dx
      path.append((y, x))
  return (y, x), path


def _four_touch(shape, height, width, a, b):
  for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
    if 0 <= na < height and 0 <= nb < width and shape[na][nb]:
      return True
  return False


def _path_problem(shape, height, width, path):
  """Return why the path is ambiguous under competing readings, or None."""
  for a, b in path:
    if not _four_touch(shape, height, width, a, b):
      return "ball path leaves 4-contact with the shape (ambiguous)"
    if (a + 1 < height and not shape[a + 1][b]
        and _four_touch(shape, height, width, a + 1, b)):
      return "free forward cell hugging the shape (fall-vs-stop ambiguous)"
  return None


def _resolve(shape, height, width, y, x):
  result = _settle(shape, height, width, y, x)
  if result is None:
    return None, "ambiguous slide direction"
  problem = _path_problem(shape, height, width, result[1])
  if problem is not None:
    return None, problem
  return result[0], None


def _orient(g, transpose, flip_rows, flip_cols):
  if transpose:
    g = [list(row) for row in zip(*g)]
  if flip_rows:
    g = g[::-1]
  if flip_cols:
    g = [row[::-1] for row in g]
  return [list(row) for row in g]


def _scene_problem(height, width, columns, max_fraction=None):
  """Return a description of what is wrong with the shape, or None."""
  if not (1 <= height <= 30 and 1 <= width <= 30):
    return "grid size out of range"
  if len(columns) != width:
    return "columns must have one entry per canonical column"
  area = 0
  for run in columns:
    if run is None:
      continue
    top, bottom = run
    if not (0 <= top <= bottom < height):
      return "column run out of bounds"
    area += bottom - top + 1
  if area == 0:
    return "no shape cells"
  if height * width - area - 1 <= area:
    return "background 7 must be the majority colour"
  if max_fraction is not None and area > max_fraction * height * width:
    return "shape too large"
  shape = _shape_cells(height, width, columns)
  cells = [(r, c) for r in range(height) for c in range(width) if shape[r][c]]
  seen = {cells[0]}
  stack = [cells[0]]
  while stack:
    r, c = stack.pop()
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if (0 <= nr < height and 0 <= nc < width and shape[nr][nc]
          and (nr, nc) not in seen):
        seen.add((nr, nc))
        stack.append((nr, nc))
  if len(seen) != len(cells):
    return "shape must be 4-connected"
  return None


def _marker_limit(columns, x):
  """Largest legal start row in canonical column x, or -1 if none.

  The start row must be at least two rows above the topmost shape cell, so the
  start cell never 8-touches the shape.
  """
  if columns[x] is None:
    return -1
  return min(run[0] for run in columns if run is not None) - 2


def _sample_marker(shape, height, width, columns):
  good = []
  for x in range(width):
    limit = _marker_limit(columns, x)
    if limit < 0:
      continue
    final, _ = _resolve(shape, height, width, limit, x)
    if final is not None:
      good.append(x)
  if not good:
    return None
  x = random.choice(good)
  return random.randint(0, _marker_limit(columns, x)), x


def _rel_from_steps(style, steps, p):
  length = len(steps) + 1
  rel = [0] * length
  if style == "up":
    for i in range(length - 1):
      rel[i + 1] = rel[i] + steps[i]
  elif style == "down":
    for i in range(length - 2, -1, -1):
      rel[i] = rel[i + 1] + steps[i]
  else:
    for i in range(p - 1, -1, -1):
      rel[i] = rel[i + 1] + steps[i]
    for i in range(p, length - 1):
      rel[i + 1] = rel[i] + steps[i]
    if style == "valley":
      m = max(rel)
      rel = [m - v for v in rel]
  return rel


def _random_tops(length, height):
  max_span = height - 4
  if max_span < 1 or length < 2:
    return None
  style = random.choice(["up", "down", "peak", "valley"])
  p = random.randint(0, length - 1)
  steps = [random.choices([0, 1, 2], [2, 5, 1])[0]
           for _ in range(length - 1)]
  rel = _rel_from_steps(style, steps, p)
  # Shrink until it fits; terminates because the step total strictly drops.
  while max(rel) > max_span:
    nonzero = [i for i, s in enumerate(steps) if s > 0]
    steps[random.choice(nonzero)] -= 1
    rel = _rel_from_steps(style, steps, p)
  if max(rel) == 0:
    steps[random.randint(0, length - 2)] = 1
    rel = _rel_from_steps(style, steps, p)
  span = max(rel)
  base = random.randint(2, height - 2 - span)
  return [base + v for v in rel]


def _random_columns(height, width):
  length = random.randint(3, width)
  start = random.randint(0, width - length)
  tops = _random_tops(length, height)
  if tops is None:
    return None
  base = random.randint(max(tops), height - 1)
  to_edge = random.random() < 0.5
  columns = [None] * width
  for i, top in enumerate(tops):
    if to_edge:
      bottom = height - 1
    else:
      bottom = random.randint(base, min(height - 1, base + 2))
    columns[start + i] = (top, bottom)
  return columns


def _random_scene(height=None, width=None):
  _check_size("height", height, 5, 30)
  _check_size("width", width, 3, 30)
  for _ in range(2000):
    h = height if height is not None else random.randint(6, 22)
    w = width if width is not None else random.randint(5, 18)
    columns = _random_columns(h, w)
    if columns is None:
      continue
    if _scene_problem(h, w, columns, max_fraction=0.45) is not None:
      continue
    shape = _shape_cells(h, w, columns)
    marker = _sample_marker(shape, h, w, columns)
    if marker is None:
      continue
    return h, w, columns, marker
  raise ValueError("could not build a scene for the requested size")


def generate(height=None, width=None, columns=None, marker=None,
             transpose=None, flip_rows=None, flip_cols=None):
  """Build one input/output pair.

  Args:
    height: CANONICAL-frame row count (the 5 falls downward). If transpose
      ends up True, the emitted grid has this many columns. Random scenes
      accept 5..30; explicit columns accept 1..30 and require it.
    width: CANONICAL-frame column count. Random scenes accept 3..30. With
      explicit columns it defaults to len(columns) and must match it.
    columns: list with one entry per canonical column. Each entry is None or
      (top, bottom), the inclusive vertical run of 0 cells in that column.
      The shape must be 4-connected and smaller than the background.
    marker: (row, col) of the 5 in the canonical frame. It must lie in a
      shape column and at least two rows above the topmost shape cell. It is
      sampled if None; giving it requires explicit columns.
    transpose: bool or None (random); transpose the canonical grid first.
    flip_rows: bool or None (random); reverse the rows after transposing.
    flip_cols: bool or None (random); reverse the columns after transposing.
  """
  _check_flag("transpose", transpose)
  _check_flag("flip_rows", flip_rows)
  _check_flag("flip_cols", flip_cols)
  if columns is None:
    if marker is not None:
      raise ValueError("marker requires explicit columns")
    height, width, columns, marker = _random_scene(height, width)
  else:
    columns = _normalize_columns(columns)
    if height is None:
      raise ValueError("explicit columns require an explicit height")
    _check_size("height", height, 1, 30)
    _check_size("width", width, 1, 30)
    if width is None:
      width = len(columns)
    problem = _scene_problem(height, width, columns)
    if problem is not None:
      raise ValueError(problem)
  shape = _shape_cells(height, width, columns)
  if marker is None:
    marker = _sample_marker(shape, height, width, columns)
    if marker is None:
      raise ValueError("no unambiguous marker position for this shape")
  y0, x0 = _normalize_marker(marker)
  if not (0 <= x0 < width and 0 <= y0 <= _marker_limit(columns, x0)):
    raise ValueError("marker must be in a shape column, at least two rows "
                     "above every shape cell")
  final, problem = _resolve(shape, height, width, y0, x0)
  if problem is not None:
    raise ValueError(problem)
  if transpose is None:
    transpose = random.random() < 0.5
  if flip_rows is None:
    flip_rows = random.random() < 0.5
  if flip_cols is None:
    flip_cols = random.random() < 0.5
  grid_in = common.grid(width, height, BG)
  for r in range(height):
    for c in range(width):
      if shape[r][c]:
        grid_in[r][c] = SHAPE
  grid_out = [list(row) for row in grid_in]
  grid_in[y0][x0] = BALL
  grid_out[final[0]][final[1]] = BALL
  return {
      "input": _orient(grid_in, transpose, flip_rows, flip_cols),
      "output": _orient(grid_out, transpose, flip_rows, flip_cols),
  }


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=10, width=6,
               columns=[None, (8, 8), (7, 8), (7, 9), (6, 9), (5, 9)],
               marker=(2, 5), transpose=False, flip_rows=False,
               flip_cols=False),
      generate(height=8, width=6,
               columns=[None, None, None, (6, 6), (5, 6), (4, 6)],
               marker=(1, 5), transpose=True, flip_rows=False,
               flip_cols=False),
      generate(height=12, width=8,
               columns=[(6, 10), (6, 10), (7, 9), (7, 9), (8, 8), (8, 8),
                        None, None],
               marker=(0, 0), transpose=False, flip_rows=True,
               flip_cols=False),
  ]
  test = [
      generate(height=16, width=10,
               columns=[None, None, (12, 12), (11, 12), (10, 12), (10, 12),
                        (9, 12), (8, 12), (7, 13), (6, 13)],
               marker=(3, 9), transpose=True, flip_rows=False,
               flip_cols=True),
  ]
  return {"train": train, "test": test}
