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

"""ARC task 2037f2c7: mark the cells a damaged copy is missing.

Rule: the input holds two copies of one multicoloured figure on black. One
copy is intact. The other is the same figure, translated, with some cells
erased to black. Overlay the damaged copy on the intact one. Each cell that
is present in the intact figure but missing from the damaged copy becomes 8.
The output is the band of figure rows from the first damaged row to the last
damaged row, at the full figure width. Every other cell is 0.

Scope: the generator builds a random, left-right symmetric, 8-connected
figure from stacked layers. A layer is a centred block, a mirrored pair of
side bars or a full-width bar. An optional mirrored corner can be cut away.
Figures are 4..12 wide and 5..20 tall, with 3..5 colours taken from
{1..7, 9}. The figure is placed twice, either side by side or stacked, with
at least one blank row or column between the copies. The damage is a band
of 1..4 consecutive rows, with erasures in the first and last rows of the
band. The generator rejects any damage that lets the damaged copy fit the
template at more than one translation. Black must cover more than half of
the input grid, so black is clearly the background colour.
"""

import random

import common


PALETTE = [1, 2, 3, 4, 5, 6, 7, 9]


def _components(cells):
  """Returns the sizes of the 8-connected components of a cell set."""
  cells = set(cells)
  seen = set()
  sizes = []
  for start in cells:
    if start in seen:
      continue
    seen.add(start)
    stack = [start]
    n = 0
    while stack:
      r, c = stack.pop()
      n += 1
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          q = (r + dr, c + dc)
          if q in cells and q not in seen:
            seen.add(q)
            stack.append(q)
    sizes.append(n)
  return sizes


def _connected(fig):
  cells = [(r, c) for r, row in enumerate(fig) for c, v in enumerate(row) if v]
  return bool(cells) and len(_components(cells)) == 1


def _make_figure(fw, fh):
  """Builds a symmetric layered figure of exactly fh rows by fw columns."""
  minw = 1 if fw % 2 else 2
  par_widths = [w for w in range(minw, fw + 1, 2)]
  for _ in range(200):
    colors = random.sample(PALETTE, random.randint(3, 5))
    fig = [[0] * fw for _ in range(fh)]

    def rect(r0, r1, c0, c1, col):
      for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
          fig[r][c] = col
          fig[r][fw - 1 - c] = col

    spine_ws = [w for w in par_widths if w <= fw - 2] or [minw]
    sw = random.choice(spine_ws)
    s0 = (fw - sw) // 2
    rect(0, fh - 1, s0, s0 + sw - 1, colors[0])
    br = random.randint(0, fh - 1)
    rect(br, min(fh - 1, br + random.randint(0, 1)), 0, fw - 1, colors[1])
    for _ in range(random.randint(3, 6)):
      col = random.choice(colors)
      kind = random.choice(['center', 'center', 'pair', 'row'])
      r0 = random.randint(0, fh - 1)
      r1 = min(fh - 1, r0 + random.randint(0, max(1, fh // 2)))
      if kind == 'center':
        w = random.choice(par_widths)
        c0 = (fw - w) // 2
        c1 = c0 + w - 1
      elif kind == 'pair':
        half = (fw + 1) // 2
        c0 = random.randint(0, half - 1)
        c1 = min(half - 1, c0 + random.randint(0, 1))
      else:
        c0, c1 = 0, fw - 1
        r1 = min(fh - 1, r0 + random.randint(0, 1))
      rect(r0, r1, c0, c1, col)
    if s0 > 0 and random.random() < 0.6:
      k = random.randint(1, 2)
      cw = random.randint(1, s0)
      rows = range(0, k) if random.random() < 0.5 else range(fh - k, fh)
      for r in rows:
        for c in range(cw):
          fig[r][c] = 0
          fig[r][fw - 1 - c] = 0
    if any(not any(row) for row in fig):
      continue
    if not any(fig[r][0] for r in range(fh)):
      continue
    if len(set(v for row in fig for v in row if v)) < 3:
      continue
    if not _connected(fig):
      continue
    return fig
  return None


def _alignment_count(fig, kept):
  """Counts the translations at which the kept cells agree with the template."""
  fh, fw = len(fig), len(fig[0])
  rs = [r for r, _ in kept]
  cs = [c for _, c in kept]
  dy0, dy1, dx0, dx1 = min(rs), max(rs), min(cs), max(cs)
  count = 0
  for oy in range(dy1 - fh + 1, dy0 + 1):
    for ox in range(dx1 - fw + 1, dx0 + 1):
      if all(fig[r - oy][c - ox] == v for (r, c), v in kept.items()):
        count += 1
  return count


def _make_damage(fig):
  fh, fw = len(fig), len(fig[0])
  total = sum(1 for row in fig for v in row if v)
  for _ in range(100):
    d = random.randint(1, max(1, min(4, fh - 2)))
    s = random.randint(0, fh - d)
    p = random.uniform(0.3, 0.8)
    erased = set()
    for r in range(s, s + d):
      for c in range(fw):
        if fig[r][c] and random.random() < p:
          erased.add((r, c))
    for r in (s, s + d - 1):
      if not any(rr == r for rr, _ in erased):
        erased.add((r, random.choice([c for c in range(fw) if fig[r][c]])))
    kept = {(r, c): fig[r][c] for r in range(fh) for c in range(fw)
            if fig[r][c] and (r, c) not in erased}
    if len(kept) < max(3, total // 2):
      continue
    if _alignment_count(fig, kept) != 1:
      continue
    return erased
  return None


def _layout(fh, fw, gh, gw):
  modes = []
  if 2 * fh + 1 <= 30:
    modes.append('v')
  if 2 * fw + 1 <= 30:
    modes.append('h')
  if not modes:
    return None
  for _ in range(100):
    mode = random.choice(modes)
    if mode == 'h':
      h = gh if gh is not None else random.randint(fh, min(30, fh + 12))
      w = gw if gw is not None else random.randint(2 * fw + 1, min(30, 2 * fw + 9))
      if h < fh or w < 2 * fw + 1:
        continue
      a = random.randint(0, w - 2 * fw - 1)
      b = random.randint(a + fw + 1, w - fw)
      p1 = (random.randint(0, h - fh), a)
      p2 = (random.randint(0, h - fh), b)
    else:
      h = gh if gh is not None else random.randint(2 * fh + 1, min(30, 2 * fh + 7))
      w = gw if gw is not None else random.randint(fw, min(30, fw + 14))
      if h < 2 * fh + 1 or w < fw:
        continue
      a = random.randint(0, h - 2 * fh - 1)
      b = random.randint(a + fh + 1, h - fh)
      p1 = (a, random.randint(0, w - fw))
      p2 = (b, random.randint(0, w - fw))
    if random.random() < 0.5:
      p1, p2 = p2, p1
    return h, w, p1, p2
  return None


def generate(width=None, height=None, figure=None, intact_pos=None,
             damaged_pos=None, erased=None, fig_width=None, fig_height=None):
  """Returns an input/output pair for this task.

  Args:
    width: grid width; sampled if None.
    height: grid height; sampled if None.
    figure: the intact figure as a list of rows, cropped to its bounding box
      (0 = empty); sampled if None.
    intact_pos: (row, col) of the intact copy's top-left corner.
    damaged_pos: (row, col) of the damaged copy's top-left corner.
    erased: (row, col) cells, relative to the figure, that the damaged copy
      is missing; sampled if None.
    fig_width: figure width, used only when figure is None.
    fig_height: figure height, used only when figure is None.
  """
  if (intact_pos is None) != (damaged_pos is None):
    raise ValueError('both copy positions must be supplied together')
  if any(v is not None and not 1 <= v <= 30 for v in (width,height)):
    raise ValueError('canvas dimensions must be 1..30')
  if figure is None:
    if fig_width is not None and not 4 <= fig_width <= 14:
      raise ValueError('random figure width must be 4..14')
    if fig_height is not None and not 5 <= fig_height <= 24:
      raise ValueError('random figure height must be 5..24')
  for _ in range(300):
    if figure is None:
      fw = fig_width if fig_width is not None else random.randint(4, 12)
      fh = fig_height if fig_height is not None else random.randint(5, 20)
      fig = _make_figure(fw, fh)
      if fig is None:
        continue
    else:
      fig = [list(row) for row in figure]
    fh, fw = len(fig), len(fig[0])
    if erased is None:
      er = _make_damage(fig)
      if er is None:
        continue
    else:
      er = set(tuple(e) for e in erased)
    if not er:
      continue
    sampled_layout = intact_pos is None or damaged_pos is None
    if sampled_layout:
      lay = _layout(fh, fw, height, width)
      if lay is None:
        continue
      gh, gw, pi, pd = lay
    else:
      gh, gw = height, width
      pi, pd = tuple(intact_pos), tuple(damaged_pos)
    grid = common.grid(gw, gh, 0)
    intact_cells = []
    damaged_cells = []
    for r in range(fh):
      for c in range(fw):
        v = fig[r][c]
        if not v:
          continue
        grid[pi[0] + r][pi[1] + c] = v
        intact_cells.append((pi[0] + r, pi[1] + c))
        if (r, c) not in er:
          grid[pd[0] + r][pd[1] + c] = v
          damaged_cells.append((pd[0] + r, pd[1] + c))
    if sampled_layout:
      # Black must be the clear majority so it is the background colour.
      zeros = sum(row.count(0) for row in grid)
      if zeros * 2 <= gh * gw:
        continue
      # The intact copy must be the unique largest 8-connected object.
      big = len(intact_cells)
      if any(s >= big for s in _components(damaged_cells)):
        continue
    lo = min(r for r, _ in er)
    hi = max(r for r, _ in er)
    output = [[8 if (r, c) in er else 0 for c in range(fw)]
              for r in range(lo, hi + 1)]
    return {"input": grid, "output": output}
  raise RuntimeError("could not construct a valid scene")


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  f1 = [[0, 0, 4, 4, 4, 4, 0, 0],
        [1, 1, 4, 6, 6, 4, 1, 1],
        [3, 3, 3, 3, 3, 3, 3, 3],
        [1, 3, 4, 6, 6, 4, 3, 1],
        [1, 3, 4, 6, 6, 4, 3, 1],
        [1, 3, 4, 6, 6, 4, 3, 1],
        [1, 3, 4, 6, 6, 4, 3, 1],
        [1, 1, 4, 6, 6, 4, 1, 1],
        [2, 4, 4, 7, 7, 4, 4, 2],
        [2, 4, 4, 7, 7, 4, 4, 2],
        [2, 0, 0, 7, 7, 0, 0, 2]]
  e1 = [(4, 1), (4, 6), (4, 7), (5, 0), (5, 1), (5, 2), (5, 3), (5, 5),
        (5, 6), (5, 7), (6, 2), (6, 7), (7, 7)]
  f2 = ([[0, 0, 4, 4, 4, 0, 0], [3, 3, 4, 6, 4, 3, 3]] +
        [[3, 2, 4, 6, 4, 2, 3] for _ in range(11)] +
        [[3, 3, 4, 6, 4, 3, 3], [0, 0, 4, 4, 4, 0, 0]])
  e2 = [(9, 0), (9, 6), (10, 0), (10, 1), (10, 5), (10, 6), (11, 0), (11, 6)]
  f3 = [[3, 3, 3, 3, 3, 3],
        [4, 4, 4, 4, 4, 4],
        [0, 3, 3, 3, 3, 0],
        [2, 3, 7, 7, 3, 2],
        [2, 3, 7, 7, 3, 2],
        [2, 3, 7, 7, 3, 2],
        [0, 3, 7, 7, 3, 0],
        [0, 3, 3, 3, 3, 0]]
  e3 = [(5, 0), (5, 1), (5, 2), (5, 4), (5, 5), (6, 2)]
  f4 = [[0, 1, 1, 1, 0, 0, 1, 1, 1, 0],
        [0, 0, 4, 4, 6, 6, 4, 4, 0, 0],
        [3, 1, 4, 2, 6, 6, 2, 4, 1, 3],
        [3, 1, 4, 2, 6, 6, 2, 4, 1, 3],
        [3, 1, 1, 2, 6, 6, 2, 1, 1, 3],
        [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 3, 3, 3, 3, 3, 3, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0]]
  e4 = [(3, 0), (3, 1), (3, 6), (3, 7), (3, 8), (3, 9),
        (4, 0), (4, 1), (4, 8), (4, 9)]
  train = [
      generate(width=25, height=25, figure=f1, intact_pos=(9, 15),
               damaged_pos=(2, 3), erased=e1),
      generate(width=25, height=23, figure=f2, intact_pos=(0, 12),
               damaged_pos=(5, 3), erased=e2),
      generate(width=22, height=22, figure=f3, intact_pos=(3, 3),
               damaged_pos=(12, 14), erased=e3),
  ]
  test = [
      generate(width=25, height=24, figure=f4, intact_pos=(6, 1),
               damaged_pos=(2, 14), erased=e4),
  ]
  return {"train": train, "test": test}
