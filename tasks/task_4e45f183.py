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

"""ARC task 4e45f183: send each panel's pattern to the panel named by its position.

The grid is a 3x3 arrangement of PxP panels separated by one-cell lines of 0.
Every fixture uses P = 5, which gives a 19x19 grid. Each panel holds one
pattern in a single foreground colour on a shared background colour. Take the
bounding box of a pattern in panel-local coordinates (0..P-1). Compare its
centre with the panel centre ((P-1)/2, (P-1)/2):
- the vertical result gives top, middle or bottom;
- the horizontal result gives left, middle or right.
These two results name the destination panel in the 3x3 arrangement. The
output copies the pattern into that panel at the same local cells. Every
other panel cell becomes background. Dividers are unchanged.

The latent scene has these parts:
- the panel size and the background and foreground colours;
- nine patterns, indexed by their destination panel;
- a permutation `sources` that says which input panel holds each pattern.
The input places pattern d in panel sources[d]. The output places pattern d
in panel d. Each pattern's bounding box is built to fall in the region its
destination index names. So the destinations always form a permutation, as
in all of the demonstrations.

Scope:
- Panel sizes run from 4 to 8, giving grids of 16 to 28. Every size other
  than 5 is a synthetic extension.
- There are two pattern styles. The first draws an independent random blob
  per region. The second takes one top-left corner motif and reflects or
  unions it into every region, as in train pair 2 and the test. A few panels
  are then replaced by free blobs.
- The total foreground count is bounded. This keeps the background colour
  strictly the most frequent colour in the grid, ahead of the divider zeros
  and the foreground.
"""

import random

import common

PANEL_SIZES = (4, 5, 5, 5, 6, 7, 8)
STYLES = ("random", "motif")


def _cat(lo, hi, p):
  """0/1/2 = bounding-box centre before / at / after the panel centre."""
  s = lo + hi - (p - 1)
  return 0 if s < 0 else (1 if s == 0 else 2)


def _ranges(cat, p):
  """All (lo, hi) index ranges in 0..p-1 whose centre falls in `cat`."""
  return [(a, b) for a in range(p) for b in range(a, p)
          if _cat(a, b, p) == cat]


def _region(cells, p):
  ys = [y for y, _ in cells]
  xs = [x for _, x in cells]
  return _cat(min(ys), max(ys), p) * 3 + _cat(min(xs), max(xs), p)


def _limits(p):
  """Foreground budget keeping background the strict majority colour."""
  side = 3 * p + 4
  panel_cells = 9 * p * p
  divider_cells = side * side - panel_cells
  budget = min(panel_cells - divider_cells - 1, (panel_cells - 1) // 2)
  return budget, (2 * p * p) // 3


def _fill_box(y0, y1, x0, x1, dens):
  """Random cells inside a box that touch all four box edges."""
  cells = set()
  for y in range(y0, y1 + 1):
    for x in range(x0, x1 + 1):
      if random.random() < dens:
        cells.add((y, x))
  edges = (
      [(y0, x) for x in range(x0, x1 + 1)],
      [(y1, x) for x in range(x0, x1 + 1)],
      [(y, x0) for y in range(y0, y1 + 1)],
      [(y, x1) for y in range(y0, y1 + 1)],
  )
  for edge in edges:
    if not any(c in cells for c in edge):
      cells.add(random.choice(edge))
  return cells


def _random_pattern(d, p, cap):
  """Random blob of at most `cap` (>= 2) cells whose box lies in region d."""
  vr, hr = divmod(d, 3)
  for _ in range(60):
    y0, y1 = random.choice(_ranges(vr, p))
    x0, x1 = random.choice(_ranges(hr, p))
    cells = _fill_box(y0, y1, x0, x1, random.uniform(0.25, 0.65))
    # Mirroring a centred axis keeps the same bounding box.
    if hr == 1 and random.random() < 0.6:
      cells |= {(y, p - 1 - x) for (y, x) in cells}
    if vr == 1 and random.random() < 0.6:
      cells |= {(p - 1 - y, x) for (y, x) in cells}
    if len(cells) <= cap:
      return sorted(cells)
  # Sparse version: two opposite box corners plus a few random extras.
  y0, y1 = random.choice(_ranges(vr, p))
  x0, x1 = random.choice(_ranges(hr, p))
  if random.random() < 0.5:
    cells = {(y0, x0), (y1, x1)}
  else:
    cells = {(y0, x1), (y1, x0)}
  target = len(cells) + random.randint(0, max(0, cap - len(cells)))
  box = [(y, x) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
  random.shuffle(box)
  for c in box:
    if len(cells) >= target:
      break
    cells.add(c)
  return sorted(cells)


def _random_patterns(p, budget, cap):
  pats = [None] * 9
  order = list(range(9))
  random.shuffle(order)
  for i, d in enumerate(order):
    room = budget - 2 * (8 - i)  # reserve two cells per remaining pattern
    pats[d] = _random_pattern(d, p, max(2, min(cap, room)))
    budget -= len(pats[d])
  return pats


def _reflect(cat, v, p):
  if cat == 0:
    return (v,)
  if cat == 2:
    return (p - 1 - v,)
  return (v, p - 1 - v)


def _motif_patterns(p, budget, cap):
  """Reflect one top-left motif into each region; swap some panels for blobs."""
  for _ in range(40):
    y0, y1 = random.choice(_ranges(0, p))
    x0, x1 = random.choice(_ranges(0, p))
    motif = _fill_box(y0, y1, x0, x1, random.uniform(0.3, 0.7))
    pats = []
    for d in range(9):
      vr, hr = divmod(d, 3)
      pats.append(sorted({(ty, tx) for (y, x) in motif
                          for ty in _reflect(vr, y, p)
                          for tx in _reflect(hr, x, p)}))
    for d in range(9):
      if random.random() < 0.25:
        pats[d] = _random_pattern(d, p, max(2, min(cap, len(pats[d]))))
    if sum(len(c) for c in pats) <= budget:
      return pats
  return None


def _parse(pattern, p):
  if pattern and isinstance(pattern[0], str):
    if len(pattern) != p or any(len(row) != p for row in pattern):
      raise ValueError("string patterns must be %dx%d" % (p, p))
    if any(ch not in ".#" for row in pattern for ch in row):
      raise ValueError("string patterns may contain only dot and hash")
    return sorted((y, x) for y, row in enumerate(pattern)
                  for x, ch in enumerate(row) if ch == "#")
  cells = sorted(set(tuple(c) for c in pattern))
  for (y, x) in cells:
    if not (0 <= y < p and 0 <= x < p):
      raise ValueError("pattern cell outside the panel")
  return cells


def generate(bg=None, fg=None, patterns=None, sources=None, panel_size=None,
             style=None):
  """Build one input/output pair.

  Args:
    bg: background colour of the panels (1..9). Must differ from fg.
    fg: pattern colour (1..9).
    patterns: list of 9 patterns indexed by destination panel (row-major).
      Each is either P strings of '.'/'#' or a list of (row, col) local
      cells. Pattern d's bounding-box centre must lie in region d.
      This cannot be combined with `style`.
    sources: permutation of 0..8. sources[d] is the input panel that holds
      pattern d. When it is random, it is never the identity.
    panel_size: side P of each panel (4..8). The grid is 3P+4. If omitted,
      it is inferred from string patterns, defaults to 5 for cell-list
      patterns, and is otherwise sampled.
    style: "random" (independent blobs) or "motif" (one reflected corner
      motif plus some blobs). Used only when patterns is None.
  """
  if style is not None and style not in STYLES:
    raise ValueError("style must be one of %s" % (STYLES,))
  if patterns is not None and style is not None:
    raise ValueError("style only applies to randomly sampled patterns")
  if panel_size is None:
    if patterns is not None:
      first = patterns[0] if len(patterns) else None
      if first and isinstance(first[0], str):
        panel_size = len(first)
      else:
        panel_size = 5
    else:
      panel_size = random.choice(PANEL_SIZES)
  p = panel_size
  if not isinstance(p, int) or p < 4 or 3 * p + 4 > 30:
    raise ValueError("panel_size must be an integer in 4..8")

  if bg is None and fg is None:
    bg, fg = random.sample(range(1, 10), 2)
  elif bg is None:
    bg = random.choice([c for c in range(1, 10) if c != fg])
  elif fg is None:
    fg = random.choice([c for c in range(1, 10) if c != bg])
  if bg == fg or not (1 <= bg <= 9) or not (1 <= fg <= 9):
    raise ValueError("bg and fg must be distinct colours in 1..9")

  budget, cap = _limits(p)
  if patterns is None:
    if style is None:
      style = random.choice(STYLES)
    pats = None
    if style == "motif":
      for _ in range(25):
        pats = _motif_patterns(p, budget, cap)
        if pats is not None:
          break
      if pats is None:
        raise ValueError("could not build motif patterns within foreground budget")
    else:
      pats = _random_patterns(p, budget, cap)
  else:
    if len(patterns) != 9:
      raise ValueError("need nine patterns")
    pats = [_parse(q, p) for q in patterns]
  for d, cells in enumerate(pats):
    if not cells or _region(cells, p) != d:
      raise ValueError("pattern %d does not lie in region %d" % (d, d))
  if sum(len(c) for c in pats) > budget:
    raise ValueError("too many foreground cells; background must dominate")

  identity = list(range(9))
  if sources is None:
    sources = identity[:]
    random.shuffle(sources)
    if sources == identity:
      i, j = random.sample(range(9), 2)
      sources[i], sources[j] = sources[j], sources[i]
  else:
    sources = list(sources)
    if sorted(sources) != identity:
      raise ValueError("sources must be a permutation of 0..8")

  side = 3 * p + 4
  offs = (1, p + 2, 2 * p + 3)

  def blank():
    g = common.grid(side, side, 0)
    for oy in offs:
      for ox in offs:
        for y in range(p):
          for x in range(p):
            g[oy + y][ox + x] = bg
    return g

  inp = blank()
  out = blank()
  for d, cells in enumerate(pats):
    sy, sx = divmod(sources[d], 3)
    ty, tx = divmod(d, 3)
    for (y, x) in cells:
      inp[offs[sy] + y][offs[sx] + x] = fg
      out[offs[ty] + y][offs[tx] + x] = fg
  return {"input": inp, "output": out}


def validate():
  """Rebuild the canonical fixtures through explicit latent arguments."""
  b = "....."
  train = [
      generate(bg=3, fg=2, patterns=[
          ["#....", ".#...", b, b, b],
          ["..#..", "..#..", b, b, b],
          ["....#", "...#.", b, b, b],
          [b, b, "##...", b, b],
          ["#...#", ".#.#.", b, ".#.#.", "#...#"],
          [b, b, "...##", b, b],
          [b, b, b, ".#...", "#...."],
          [b, b, b, "..#..", "..#.."],
          [b, b, b, "...#.", "....#"],
      ], sources=[0, 8, 3, 1, 6, 5, 4, 7, 2]),
      generate(bg=1, fg=8, patterns=[
          ["##...", "#....", b, b, b],
          ["##.##", "#...#", b, b, b],
          ["...##", "....#", b, b, b],
          ["##...", "#....", b, "#....", "##..."],
          ["##.##", "#...#", b, "#...#", "##.##"],
          ["...##", "....#", b, "....#", "...##"],
          [b, b, b, "#....", "##..."],
          [b, b, b, "#...#", "##.##"],
          [b, b, b, "....#", "...##"],
      ], sources=[1, 3, 8, 5, 0, 4, 2, 6, 7]),
      generate(bg=8, fg=6, patterns=[
          ["##...", "##...", b, b, b],
          ["#####", b, b, b, b],
          ["...##", "...##", b, b, b],
          ["#...."] * 5,
          ["##.##", "##.##", b, "##.##", "##.##"],
          ["....#"] * 5,
          [b, b, b, "##...", "##..."],
          [b, b, b, b, "#####"],
          [b, b, b, "...##", "...##"],
      ], sources=[7, 0, 5, 6, 4, 2, 3, 8, 1]),
  ]
  test = [
      generate(bg=4, fg=1, patterns=[
          ["##...", "#....", b, b, b],
          [".###.", "..#..", b, b, b],
          ["...##", "....#", b, b, b],
          [b, "#....", "##...", "#....", b],
          ["##.##", "#...#", b, "#...#", "##.##"],
          [b, "....#", "...##", "....#", b],
          [b, b, b, "#....", "##..."],
          [b, b, b, "..#..", ".###."],
          [b, b, b, "....#", "...##"],
      ], sources=[0, 4, 3, 6, 5, 8, 7, 2, 1]),
  ]
  return {"train": train, "test": test}
