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

"""ARC-GEN style generator for task f18ec8cc (curated teaching copy).

Rule: the input is a left-to-right sequence of full-height vertical colour
bands. A few single-cell dots, coloured like other bands, are scattered inside
the bands. The output cuts out the first (leftmost) band and appends it at the
right end. The remaining bands slide left and keep their order. Each band
moves as a rigid strip and carries its dots, so the grid size is unchanged.

Scope of random generation: 3-6 bands by default (2-9 when requested
explicitly), each 3-8 columns wide, total width at most 30, height 5-14.
Band colours are distinct non-zero colours. Dots use the colour of another
band and sit only in interior columns of a band. Each column holds fewer dots
than half its height, so the band colour stays the strict majority of every
column. Dots come either as independent scatter or as a "row motif" (as in
demonstration 2 and test 2): each motif row uses a distinct band colour and
carries that colour as a dot in at least two other bands. Two-band pairs are
not sampled by default because rotation and reversal coincide for them.
Band counts above 4, widths of 8 and heights outside 7-9 are synthetic
extensions of the demonstrated range.

This follows the curated teaching copy, in which the output of demonstration 1
is corrected per the open upstream PR arcprize/ARC-AGI-2#37 (the first two
output bands are swapped). validate() reproduces those teaching fixtures.
"""

import random

import common


MIN_W = 3
MAX_W = 8
MAX_TOTAL = 30
MAX_BANDS = 9


def _host(starts, c):
  """Returns the index of the band containing column c."""
  return max(i for i in range(len(starts)) if starts[i] <= c)


def _check_dots(dots, colors, starts, height, width):
  """Raises ValueError if the dots break bounds, palette or majorities."""
  seen = set()
  per_col = {}
  for r, c, col in dots:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError("dot out of bounds: %r" % ((r, c, col),))
    if col not in colors:
      raise ValueError("dot colour must be one of the band colours")
    if (r, c) in seen:
      raise ValueError("duplicate dot position: %r" % ((r, c),))
    seen.add((r, c))
    if col == colors[_host(starts, c)]:
      raise ValueError("dot colour equals its host band colour")
    per_col[c] = per_col.get(c, 0) + 1
  for c, k in per_col.items():
    if 2 * k >= height:
      raise ValueError("column %d: band colour is not a strict majority" % c)


def generate(num_bands=None, widths=None, colors=None, height=None,
             dots=None, row_motif=None):
  """Generates one input/output pair.

  Args:
    num_bands: number of bands (3-6 when sampled; 2-9 accepted explicitly).
      Must agree with the lengths of widths/colors if those are given.
    widths: list of band widths, left to right (positive, total at most 30).
    colors: list of distinct band colours 1-9, same length as widths.
    height: grid height (1-30; 5-14 when sampled).
    dots: list of (row, col, colour) dots in input coordinates. Each colour
      must be another band's colour and each column must keep its band
      colour as a strict majority.
    row_motif: when dots are sampled, True forces the shared-row motif and
      False forces independent scatter (ValueError if either is impossible).
      Incompatible with explicit dots.
  """
  sizes = [len(x) for x in (widths, colors) if x is not None]
  if num_bands is not None:
    sizes.append(num_bands)
  if sizes and any(s != sizes[0] for s in sizes):
    raise ValueError("num_bands, widths and colors disagree on band count")
  n = sizes[0] if sizes else random.randint(3, 6)
  if not 2 <= n <= MAX_BANDS:
    raise ValueError("band count must be 2-9 (distinct non-zero colours)")
  if dots is not None and row_motif is not None:
    raise ValueError("row_motif only applies when dots are sampled")

  if widths is None:
    if n * MIN_W > MAX_TOTAL:
      raise ValueError("too many bands to fit in 30 columns")
    widths = []
    used = 0
    for i in range(n):
      hi = min(MAX_W, MAX_TOTAL - used - MIN_W * (n - i - 1))
      w = random.randint(MIN_W, hi)
      widths.append(w)
      used += w
    random.shuffle(widths)
  widths = list(widths)
  if any(w < 1 for w in widths) or sum(widths) > MAX_TOTAL:
    raise ValueError("band widths must be positive with total at most 30")

  if colors is None:
    colors = random.sample(range(1, 10), n)
  colors = list(colors)
  if any(not 1 <= c <= 9 for c in colors):
    raise ValueError("band colours must be 1-9")
  if len(set(colors)) != n:
    raise ValueError("band colours must be distinct")

  if height is None:
    height = random.randint(5, 14)
  if not 1 <= height <= 30:
    raise ValueError("height must be 1-30")

  width = sum(widths)
  starts = []
  x = 0
  for w in widths:
    starts.append(x)
    x += w

  if dots is None:
    dots = []
    used = set()
    per_col = {}
    limit = (height - 1) // 2
    eligible = [b for b in range(n) if widths[b] >= 3]

    def try_add(r, b, c):
      col = random.randint(starts[b] + 1, starts[b] + widths[b] - 2)
      if per_col.get(col, 0) >= limit or (r, col) in used:
        return
      used.add((r, col))
      per_col[col] = per_col.get(col, 0) + 1
      dots.append((r, col, c))

    def hosts_for(c):
      return [b for b in eligible if colors[b] != c]

    motif_colors = [c for c in colors if len(hosts_for(c)) >= 2]
    motif_ok = limit >= 1 and bool(motif_colors)
    scatter_ok = limit >= 1 and bool(eligible)
    if row_motif and not motif_ok:
      raise ValueError("row_motif=True needs height >= 3 and a colour that "
                       "can be placed in two interior band columns")
    if row_motif is False and not scatter_ok:
      raise ValueError("row_motif=False needs height >= 3 and a band of "
                       "width >= 3 to host scattered dots")
    if row_motif is None:
      motif = motif_ok and random.random() < 0.3
    else:
      motif = bool(row_motif)

    if motif:
      # k <= limit and each row adds at most one dot per band, so no column
      # can exceed its dot limit; every motif row gets >= 2 dots.
      k = random.randint(1, min(limit, 4, len(motif_colors)))
      rows = random.sample(range(height), k)
      row_cols = random.sample(motif_colors, k)
      for r, c in zip(rows, row_cols):
        hosts = hosts_for(c)
        chosen = [b for b in hosts if random.random() >= 0.2]
        if len(chosen) < 2:
          chosen = random.sample(hosts, 2)
        for b in chosen:
          try_add(r, b, c)
    elif scatter_ok:
      for b in eligible:
        others = [c for c in colors if c != colors[b]]
        for _ in range(random.randint(0, min(3, max(1, height // 3)))):
          try_add(random.randrange(height), b, random.choice(others))
      if not dots:
        b = random.choice(eligible)
        others = [c for c in colors if c != colors[b]]
        try_add(random.randrange(height), b, random.choice(others))
  dots = [tuple(d) for d in dots]
  _check_dots(dots, colors, starts, height, width)

  grid = common.grid(width, height, 0)
  for b in range(n):
    for r in range(height):
      for c in range(starts[b], starts[b] + widths[b]):
        grid[r][c] = colors[b]
  for r, c, col in dots:
    grid[r][c] = col

  # Output from latent parameters: bands in order 1..n-1, then band 0.
  order = list(range(1, n)) + [0]
  new_start = {}
  cx = 0
  for b in order:
    new_start[b] = cx
    cx += widths[b]
  output = common.grid(width, height, 0)
  for b in order:
    for r in range(height):
      for dx in range(widths[b]):
        output[r][new_start[b] + dx] = colors[b]
  for r, c, col in dots:
    b = _host(starts, c)
    output[r][c - starts[b] + new_start[b]] = col
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the curated teaching fixtures from latent parameters."""
  train = [
      generate(widths=[5, 6, 3], colors=[5, 7, 9], height=9,
               dots=[(5, 2, 9), (5, 7, 9), (6, 2, 7), (6, 12, 7), (7, 9, 5),
                     (7, 12, 5)]),
      generate(widths=[3, 3, 3, 3], colors=[8, 9, 1, 3], height=7,
               dots=[(0, 1, 9), (0, 7, 9), (0, 10, 9), (2, 4, 8), (2, 7, 8),
                     (2, 10, 8), (4, 1, 3), (4, 4, 3), (4, 7, 3), (6, 1, 1),
                     (6, 4, 1), (6, 10, 1)]),
      generate(widths=[5, 4, 4], colors=[8, 2, 1], height=8,
               dots=[(1, 3, 1), (2, 3, 2), (4, 7, 8), (4, 10, 8), (5, 6, 1),
                     (5, 11, 2)]),
      generate(widths=[3, 3, 4], colors=[5, 7, 1], height=8,
               dots=[(1, 1, 1), (3, 4, 5), (3, 7, 7), (4, 1, 7), (4, 4, 1),
                     (6, 8, 5)]),
  ]
  test = [
      generate(widths=[3, 3, 7], colors=[9, 4, 1], height=8,
               dots=[(2, 4, 9), (2, 9, 9), (3, 1, 1), (3, 4, 1), (4, 1, 4),
                     (4, 9, 4)]),
      generate(widths=[4, 3, 5, 3], colors=[1, 7, 8, 3], height=7,
               dots=[(2, 1, 3), (2, 5, 3), (2, 10, 3), (3, 1, 7), (3, 10, 7),
                     (3, 13, 7), (4, 1, 8), (4, 5, 8), (4, 13, 8), (5, 5, 1),
                     (5, 10, 1), (5, 13, 1)]),
  ]
  return {"train": train, "test": test}
