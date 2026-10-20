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

"""ARC task 9aaea919: marker bars recolour or extend stacked plus columns.

Rule: the grid holds a row of columns built from identical 3x5 plus-ish
shapes (".XXX." / "XXXXX" / ".XXX."). Column slots are 6 cells apart. The
bottom shape of every column sits on rows h-5..h-3. A column is a stack of
one or more copies with a 4-row pitch. The bottom row holds 5-wide marker
bars, and each bar lies directly under a column.
  * A colour-2 bar recolours its whole column to 5. The height does not
    change.
  * A colour-3 bar stacks extra copies of its column's shape on top and
    keeps the column's colour. The number of added copies is the total
    height of all 2-marked columns. The canonical test pair has two
    2-markers, and their heights are summed. The train pairs never show two
    2-markers, so summing is an extrapolation that agrees with the test
    answer.
  * All marker bars are erased to background in the output.

Scope: the native fixtures are 30x30 with four columns at x = 3, 9, 15, 21.
The generator samples these scene variables:
  * the background colour;
  * distinct column colours;
  * column heights;
  * the number and placement of 2-markers and 3-markers.
Unmarked columns act as distractors.

Random sampling draws 1-3 2-markers and 1-2 3-markers.

The height sampler is biased toward disambiguating scenes:
  * the summed 2-height usually exceeds 1;
  * a 3-column's height usually differs from the extension.
This separates "add the 2-height" from "add one", "add the marker count" and
"double the column".

As a synthetic extension the generator also samples:
  * the number of columns (2-5 when explicit, 3-5 by default, or2 when width/offset leaves room for only two);
  * the grid width (span..30, biased to 30);
  * the left offset (anywhere the columns fit);
  * the grid height (9-30).
The shape, the 6-cell column spacing, the 4-row stack pitch and the
bottom-row marker placement stay fixed. Every extended stack stays inside
the grid. Stack heights use the full capacity supported by the canvas.
Multiple3-marked columns each receiving the full sum, and three or more
2-markers, are synthetic extrapolations of the archived rule rather than
behaviour uniquely established by the native examples. Explicit heights
bypass the usual disambiguation bias. Low-capacity scenes may necessarily
fail to distinguish additive shortcuts on their own.
"""

import itertools
import random

import common

SHAPE = [".XXX.", "XXXXX", ".XXX."]
SPACING = 6
PITCH = 4
MAX_SIZE = 30
MIN_HEIGHT = 9


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_int(name, v):
  if v is not None and not _is_int(v):
    raise ValueError(name + " must be an integer")


def _max_stack(height):
  """Largest stack whose top shape still starts at row 0 or below."""
  return (height - 5) // PITCH + 1


def _stamp(g, x0, top, color):
  for dy, row in enumerate(SHAPE):
    for dx, ch in enumerate(row):
      if ch == "X":
        g[top + dy][x0 + dx] = color


def _draw_column(g, x0, count, color):
  bottom_top = len(g) - 5
  for k in range(count):
    _stamp(g, x0, bottom_top - PITCH * k, color)


def _total(heights, markers):
  return sum(h for h, m in zip(heights, markers) if m == 2)


def _required(heights, markers):
  """Stack capacity needed for the input and the extended output."""
  total = _total(heights, markers)
  need = max(heights)
  for h, m in zip(heights, markers):
    if m == 3:
      need = max(need, h + total)
  return need


def _fits(heights, markers, ms):
  if markers.count(2) < 1 or markers.count(3) < 1:
    return False
  if any(h < 1 for h in heights):
    return False
  return _required(heights, markers) <= ms


def _resolve_count(num_columns, colors, heights, markers, width, left):
  counts = set()
  for seq in (colors, heights, markers):
    if seq is not None:
      counts.add(len(seq))
  if num_columns is not None:
    counts.add(num_columns)
  if len(counts) > 1:
    raise ValueError("inconsistent column counts")
  if counts:
    n = counts.pop()
  else:
    available = (width if width is not None else MAX_SIZE) - (left or 0)
    candidates = [n for n in (3, 4, 4, 4, 5) if SPACING*n-1 <= available]
    if not candidates and SPACING*2-1 <= available:
      candidates = [2]
    if not candidates:
      raise ValueError("width and left cannot accommodate two columns")
    n = random.choice(candidates)
  if not 2 <= n <= 5:
    raise ValueError("between 2 and 5 columns are supported")
  return n


def _sample_markers(n, cap):
  n2 = min(random.choice([1, 1, 1, 2, 2, 3]), n - 1, cap - 1)
  n3 = min(random.choice([1, 1, 2]), n - n2)
  idx = random.sample(range(n), n2 + n3)
  markers = [None] * n
  for i in idx[:n2]:
    markers[i] = 2
  for i in idx[n2:]:
    markers[i] = 3
  return markers


def _markers_for_heights(heights, cap):
  """Choose a marker layout for explicit heights, like _sample_markers."""
  n = len(heights)
  valid = []
  for combo in itertools.product((None, 2, 3), repeat=n):
    combo = list(combo)
    if combo.count(2) and combo.count(3) and _required(heights,
                                                       combo) <= cap:
      valid.append(combo)
  if not valid:
    raise ValueError("no marker layout fits the given heights")
  pool = [c for c in valid if c.count(2) <= 3 and c.count(3) <= 2] or valid
  if n >= 3:
    with_none = [c for c in pool if None in c]
    if with_none and random.random() < 0.85:
      pool = with_none
  return random.choice(pool)


def _sample_heights(markers, ms):
  """Sample heights so that every extended 3-column fits in ms shapes."""
  two = [i for i, m in enumerate(markers) if m == 2]
  budget = ms - 1  # every 3-column needs at least one shape of its own
  if len(two) > budget:
    raise ValueError("grid too short for the requested markers")
  # Usually make the summed extension exceed both 1 and the marker count.
  want_big = budget > len(two) and random.random() < 0.8
  hs = [1] * len(two)
  for _ in range(100):
    trial = [random.randint(1, budget) for _ in two]
    if sum(trial) > budget:
      continue
    if want_big and max(trial) < 2:
      continue
    hs = trial
    break
  total = sum(hs)
  heights = [0] * len(markers)
  for i, h in zip(two, hs):
    heights[i] = h
  for i, m in enumerate(markers):
    if m == 3:
      top = ms - total
      choices = [v for v in range(1, top + 1) if v != total]
      if choices and random.random() < 0.75:
        heights[i] = random.choice(choices)
      else:
        heights[i] = random.randint(1, top)
    elif m is None:
      heights[i] = random.randint(1, ms)
  return heights


def generate(width=None, height=None, num_columns=None, left=None, bg=None,
             colors=None, heights=None, markers=None):
  """Build one input/output pair.

  Args:
    width: grid width. It must be at least left + 6*n - 1 and at most 30.
      Native fixtures use 30. When free, it is sampled from span..30 with a
      bias toward 30.
    height: grid height in 9..30. Native fixtures use 30. A stack holds at
      most (height - 5) // 4 + 1 shapes.
    num_columns: number of columns n, from 2 to 5. Native fixtures use 4.
    left: x of the first column. Column i starts at left + 6*i. Native
      fixtures use 3. When free, it is uniform over every fitting offset.
    bg: background colour. It is never 2, 3 or 5.
    colors: n distinct column colours. None of them is bg or 5. Colours 2
      and 3 are allowed, as in native train 3.
    heights: n stack heights (number of shapes, integer >= 1 each).
    markers: n entries, each None, 2 or 3, giving the bar under each column.
      At least one 2 and one 3 are required. Beyond that, explicit counts
      are limited only by the grid capacity.

  Partial parameters are completed by sampling. Incompatible or non-integer
  values raise ValueError.
  """
  for name, v in (("width", width), ("height", height),
                  ("num_columns", num_columns), ("left", left), ("bg", bg)):
    _check_int(name, v)
  if colors is not None:
    if not isinstance(colors, (list, tuple)):
      raise ValueError("colors must be a list or tuple")
    colors = list(colors)
    for c in colors:
      if not _is_int(c):
        raise ValueError("colors entries must be integers")
  if heights is not None:
    if not isinstance(heights, (list, tuple)):
      raise ValueError("heights must be a list or tuple")
    heights = list(heights)
    for h in heights:
      if not _is_int(h):
        raise ValueError("heights entries must be integers")
  if markers is not None:
    if not isinstance(markers, (list, tuple)):
      raise ValueError("markers must be a list or tuple")
    markers = list(markers)
    for m in markers:
      if m is not None and not (_is_int(m) and m in (2, 3)):
        raise ValueError("markers must be None, 2 or 3")

  n = _resolve_count(num_columns, colors, heights, markers, width, left)
  if height is not None and not MIN_HEIGHT <= height <= MAX_SIZE:
    raise ValueError("height must be in 9..30")
  cap = _max_stack(height if height is not None else MAX_SIZE)

  if markers is not None:
    if markers.count(2) < 1 or markers.count(3) < 1:
      raise ValueError("need at least one 2-marker and one 3-marker")

  if heights is not None:
    if any(h < 1 for h in heights):
      raise ValueError("heights must be at least 1")
    if markers is None:
      markers = _markers_for_heights(heights, cap)
    need = _required(heights, markers)
  else:
    if markers is None:
      markers = _sample_markers(n, cap)
    need = markers.count(2) + 1

  if height is None:
    lo = max(MIN_HEIGHT, 5 + PITCH * (need - 1))
    if lo > MAX_SIZE:
      raise ValueError("stacks cannot fit in a 30-row grid")
    height = MAX_SIZE if random.random() < 0.4 else random.randint(
        lo, MAX_SIZE)
  ms = _max_stack(height)
  if heights is None:
    heights = _sample_heights(markers, ms)
  if not _fits(heights, markers, ms):
    raise ValueError("stacks or extensions do not fit in the grid")

  span = SPACING * n - 1
  if width is not None and not span <= width <= MAX_SIZE:
    raise ValueError("width cannot hold the columns")
  if left is not None and left < 0:
    raise ValueError("left must be non-negative")
  if width is None:
    lo = span + (left if left is not None else 0)
    if lo > MAX_SIZE:
      raise ValueError("columns run past the right edge")
    width = MAX_SIZE if random.random() < 0.5 else random.randint(
        lo, MAX_SIZE)
  if left is None:
    left = random.randint(0, width - span)
  if left + span > width:
    raise ValueError("columns run past the right edge")

  if bg is not None and (bg in (2, 3, 5) or not 0 <= bg <= 9):
    raise ValueError("bg must be a colour other than 2, 3 and 5")
  if bg is None:
    pool = [c for c in range(10)
            if c not in (2, 3, 5) and (colors is None or c not in colors)]
    if not pool:
      raise ValueError("no background colour available")
    bg = random.choice(pool)
  if colors is None:
    colors = random.sample([c for c in range(10) if c not in (bg, 5)], n)
  else:
    if len(set(colors)) != n:
      raise ValueError("column colours must be distinct")
    if any(c in (bg, 5) or not 0 <= c <= 9 for c in colors):
      raise ValueError("column colours must differ from bg and 5")

  total = _total(heights, markers)
  grid_in = common.grid(width, height, bg)
  grid_out = common.grid(width, height, bg)
  for i in range(n):
    x0 = left + SPACING * i
    _draw_column(grid_in, x0, heights[i], colors[i])
    if markers[i] is not None:
      for dx in range(5):
        grid_in[height - 1][x0 + dx] = markers[i]
    if markers[i] == 2:
      _draw_column(grid_out, x0, heights[i], 5)
    elif markers[i] == 3:
      _draw_column(grid_out, x0, heights[i] + total, colors[i])
    else:
      _draw_column(grid_out, x0, heights[i], colors[i])
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  native = {"width": 30, "height": 30, "left": 3}
  train = [
      generate(bg=7, colors=[9, 0, 1, 4], heights=[2, 1, 1, 3],
               markers=[2, None, 3, None], **native),
      generate(bg=1, colors=[0, 8, 4, 6], heights=[3, 2, 2, 1],
               markers=[3, None, None, 2], **native),
      generate(bg=6, colors=[7, 2, 3, 0], heights=[1, 3, 3, 1],
               markers=[None, 3, 2, None], **native),
  ]
  test = [
      generate(bg=4, colors=[1, 9, 6, 8], heights=[1, 1, 1, 1],
               markers=[2, 2, None, 3], **native),
  ]
  return {"train": train, "test": test}
