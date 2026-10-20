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

"""ARC task 984d8a3e: move left-colour cells over to flatten the right edge.

Each row reads left to right as three colour runs:
  * a left-colour run of length L touching the left edge (L may be 0),
  * a middle-colour run that is at least one cell wide,
  * a right-colour run that touches the right edge and starts at column rs.
    rs may equal the width, which means the row has no right run.
Let m be the smallest rs over all rows. In each row, k = min(L, rs - m)
left-colour cells move. They are taken off the left run, and the middle run
slides left by k while keeping its width. The k cells are placed directly
against the right run. The right run itself does not change.

Scope: the generator samples the grid size, three distinct colours and a
per-row (L, rs) profile. The profile is built directly; there is no
rejection loop. Each sampled pair contains these designated rows:
  * an anchor row with rs == m (always),
  * a partial-move row with L > rs - m >= 1 (always),
  * a full-move row that leaves a gap, 1 <= L < rs - m. This row appears
    when height >= 3 and the band of right-edge offsets is at least 2 wide,
    which holds for every width >= 5,
  * optionally a blocked row (L == 0, rs > m), when height >= 4,
  * optionally a row with no right run (rs == width), when height >= 5,
  * optionally an exact-fill row (L == rs - m >= 1), when height >= 6.
All other rows are free random rows.

A bounded, randomized repair step makes the left colour a strict majority
of column 0 and the right colour a strict majority of the last column.
This keeps the colour roles identifiable. The repair step never touches the
protected designated rows. Grid sizes other than the fixture sizes (10x10
and 17x17), including non-square grids, are synthetic extensions. The rule
itself does not depend on the size. Random left-run caps and right-edge
spreads scale with the requested width rather than fixed small limits.
The minimal width-4 sampler necessarily has a fixed partial-move profile
(2, 3) and cannot express a full-move row leaving a gap. Explicit profiles
can express width-3 scenes; every accepted profile must be nonidentity and
have identifiable border colours. An anchor row without the left colour
is allowed: this follows the archived rule over all rows, but that distinction
is a synthetic extension not uniquely established by the canonical examples.
"""

import random


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _check_colors(colors):
  if (len(colors) != 3 or any(not _is_int(c) for c in colors) or
      len(set(colors)) != 3 or any(not 0 <= c <= 9 for c in colors)):
    raise ValueError("colors must be three distinct ints in 0..9")


def _check_rows(width, rows):
  """Checks a row profile for bounds, identifiability and non-identity."""
  if not _is_int(width):
    raise ValueError("width must be an int")
  if not 1 <= width <= 30 or not 1 <= len(rows) <= 30:
    raise ValueError("grid sides must be in 1..30")
  for row in rows:
    if len(row) != 2 or not _is_int(row[0]) or not _is_int(row[1]):
      raise ValueError("each row must be a pair of ints (L, rs)")
    left, rs = row
    if left < 0 or rs > width or rs - left < 1:
      raise ValueError("each row needs 0 <= L < rs <= width")
  height = len(rows)
  with_left = sum(1 for left, _ in rows if left > 0)
  with_right = sum(1 for _, rs in rows if rs < width)
  if 2 * with_left <= height or 2 * with_right <= height:
    raise ValueError("left/right colours must be strict column majorities")
  m = min(rs for _, rs in rows)
  if not any(min(left, rs - m) > 0 for left, rs in rows):
    raise ValueError("profile produces an identity pair (no row moves)")


def _render(width, rows, lc, mc, rc):
  """Builds the input and output grids row by row from the latent profile."""
  m = min(rs for _, rs in rows)
  grid_in, grid_out = [], []
  for left, rs in rows:
    grid_in.append([lc] * left + [mc] * (rs - left) + [rc] * (width - rs))
    k = max(0, min(left, rs - m))
    grid_out.append([lc] * (left - k) + [mc] * (rs - left) + [lc] * k +
                    [rc] * (width - rs))
  return grid_in, grid_out


def _sample_rows(width, height):
  """Constructs a valid (L, rs) profile directly (bounded, no rejection)."""
  if width >= 5:
    m = random.randint(2, width - 3)
  else:
    m = 2
  smax = width - 1 - m
  spread = random.randint(min(2, smax), smax)
  cap = random.randint(2, width - 2)
  p_none = random.choice([0.0, 0.1, 0.2])
  p_zero = random.choice([0.0, 0.1, 0.2])

  def pick_left(rs):
    return random.randint(1, max(1, min(rs - 1, cap)))

  rows = []
  for _ in range(height):
    rs = width if random.random() < p_none else random.randint(m, m + spread)
    left = 0 if random.random() < p_zero else pick_left(rs)
    rows.append((left, rs))

  # Designated rows. The anchor and partial rows are always present.
  d = random.randint(1, min(spread, cap - 1))
  partial = (random.randint(d + 1, min(m + d - 1, cap)), m + d)
  roles = [("anchor", (random.randint(0, min(m - 1, cap)), m)),
           ("partial", partial)]
  if height >= 3 and spread >= 2:
    d = random.randint(2, spread)
    roles.append(("fullgap", (random.randint(1, min(d - 1, cap)), m + d)))
  if height >= 4 and random.random() < 0.5:
    roles.append(("blocked", (0, random.randint(m + 1, m + spread))))
  if height >= 5 and random.random() < 0.4:
    roles.append(("noright", (pick_left(width), width)))
  if height >= 6 and random.random() < 0.5:
    d = random.randint(1, min(spread, cap))
    roles.append(("exact", (d, m + d)))
  slots = random.sample(range(height), len(roles))
  protected = set()
  for slot, (name, row) in zip(slots, roles):
    rows[slot] = row
    if name != "anchor":
      protected.add(slot)

  # Randomized repair: the left colour must be a strict majority of column 0.
  # At most one protected row has L == 0 (blocked, height >= 4), so repairing
  # every unprotected zero row always suffices.
  zero_rows = [i for i, (left, _) in enumerate(rows)
               if left == 0 and i not in protected]
  random.shuffle(zero_rows)
  nonzero = sum(1 for left, _ in rows if left > 0)
  while 2 * nonzero <= height and zero_rows:
    i = zero_rows.pop()
    rows[i] = (pick_left(rows[i][1]), rows[i][1])
    nonzero += 1
  # Randomized repair: the right colour must be a strict majority of the last
  # column. At most one protected row has rs == width (height >= 5).
  none_rows = [i for i, (_, r) in enumerate(rows)
               if r == width and i not in protected]
  random.shuffle(none_rows)
  with_right = sum(1 for _, r in rows if r < width)
  while 2 * with_right <= height and none_rows:
    i = none_rows.pop()
    new_rs = random.randint(m, m + spread)
    left = rows[i][0]
    if left > 0:
      left = min(left, new_rs - 1)
    rows[i] = (left, new_rs)
    with_right += 1
  return rows


def generate(width=None, height=None, colors=None, rows=None):
  """Generate an input/output pair.

  Args:
    width: grid width (int). If None, it is sampled from 6..30. Explicit
      values 4..30 are allowed for sampling. Required when rows is given.
    height: grid height (int). If None, it is sampled from 5..30. Explicit
      values 2..30 are allowed. If rows is given, height must be None or
      equal to len(rows).
    colors: (left, middle, right) colours, three distinct ints in 0..9.
      If None, they are sampled.
    rows: list of (L, rs) int pairs, one per row. L is the left-run length
      and rs is the column where the right run starts (rs == width means
      the row has no right run). The profile must make the left and right
      colours strict majorities of the first and last columns, and at least
      one row must move.
  """
  if colors is None:
    colors = tuple(random.sample(range(10), 3))
  if not isinstance(colors, (list, tuple)):
    raise ValueError("colors must be a list or tuple")
  colors = tuple(colors)
  _check_colors(colors)
  lc, mc, rc = colors
  if height is not None and not _is_int(height):
    raise ValueError("height must be an int")
  if width is not None and not _is_int(width):
    raise ValueError("width must be an int")
  if rows is not None:
    if width is None:
      raise ValueError("width is required when rows is given")
    if not isinstance(rows, (list, tuple)) or any(not isinstance(r, (list, tuple)) for r in rows):
      raise ValueError("rows must be a list or tuple of row pairs")
    rows = [tuple(r) for r in rows]
    if height is not None and height != len(rows):
      raise ValueError("height disagrees with len(rows)")
  else:
    if width is None:
      width = random.randint(6, 30)
    if height is None:
      height = random.randint(5, 30)
    if not 4 <= width <= 30 or not 2 <= height <= 30:
      raise ValueError("sampling needs width in 4..30 and height in 2..30")
    rows = _sample_rows(width, height)
  _check_rows(width, rows)
  grid_in, grid_out = _render(width, rows, lc, mc, rc)
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(width=10, colors=(1, 3, 0),
               rows=[(1, 6), (3, 8), (3, 7), (2, 6), (2, 6), (1, 8), (1, 8),
                     (4, 10), (3, 8), (2, 7)]),
      generate(width=10, colors=(3, 7, 9),
               rows=[(5, 10), (3, 9), (2, 8), (0, 7), (0, 7), (1, 6), (2, 7),
                     (3, 7), (0, 7), (2, 6)]),
  ]
  test = [
      generate(width=17, colors=(5, 7, 6),
               rows=[(2, 9), (3, 10), (3, 9), (6, 9), (4, 11), (3, 11),
                     (3, 11), (3, 10), (4, 9), (3, 10), (2, 11), (1, 12),
                     (2, 13), (3, 14), (4, 13), (4, 12), (3, 13)]),
  ]
  return {"train": train, "test": test}
