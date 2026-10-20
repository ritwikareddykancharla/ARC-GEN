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

"""ARC-GEN style generator for task edb79dae.

Rule: the input holds three kinds of objects on a background colour.
  * Legend tiles (3x4) shaped  a a b b / a a a b / a a b b, meaning
    "colour a becomes colour b".
  * One hollowed k x k shape template per legend source colour, lying
    outside the frame.
  * A colour-5 frame whose interior is a lattice of k x k cells (one
    background cell of margin and one cell of gap). Some lattice cells hold
    solid k x k squares of legend source colours.
The output is the crop of the colour-5 frame in which every solid square of
colour c is redrawn as c's template (filled cells in the legend target of
c, holes in background).

Scope: random background (any colour except 5), square size k in 3..5,
lattice 2..4 by 2..4, 2..5 legend pairs with distinct targets (targets may
themselves be source colours, as in the test pair), random non-overlapping
placement of tiles, templates and frame with a one-cell gap, empty lattice
cells, random 4-connected hollow templates whose bounding box is the full
k x k. Fixtures are rebuilt from explicit latent arguments.
"""

import random

import common


def _connected(mask, k):
  cells = [(r, c) for r in range(k) for c in range(k) if mask[r][c]]
  if not cells:
    return False
  seen = {cells[0]}
  stack = [cells[0]]
  while stack:
    r, c = stack.pop()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      nr, nc = r + dr, c + dc
      if 0 <= nr < k and 0 <= nc < k and mask[nr][nc] and (nr, nc) not in seen:
        seen.add((nr, nc))
        stack.append((nr, nc))
  return len(seen) == len(cells)


def _random_mask(k, used):
  """Random hollow k x k template whose bounding box is the full square."""
  for _ in range(300):
    p = random.uniform(0.55, 0.82)
    m = [[random.random() < p for _ in range(k)] for _ in range(k)]
    if not any(m[0]) or not any(m[k - 1]):
      continue
    if not any(m[r][0] for r in range(k)):
      continue
    if not any(m[r][k - 1] for r in range(k)):
      continue
    total = sum(sum(row) for row in m)
    if total == k * k or total * 2 < k * k:
      continue
    if not _connected(m, k):
      continue
    key = tuple("".join("#" if v else "." for v in row) for row in m)
    if key in used:
      continue
    return list(key)
  # Fallback: full square with one interior hole at a varying position.
  for r in range(1, k - 1):
    for c in range(1, k - 1):
      rows = [["#"] * k for _ in range(k)]
      rows[r][c] = "."
      key = tuple("".join(row) for row in rows)
      if key not in used:
        return list(key)
  return ["#" * k] * (k - 1) + ["#" * (k - 1) + "."]


def _free(rects, r, c, h, w):
  for (R, C, H, W) in rects:
    if r < R + H + 1 and R < r + h + 1 and c < C + W + 1 and C < c + w + 1:
      return False
  return True


def _sample_scene(requested_width=None, requested_height=None, requested_bg=None, requested_k=None):
  for _ in range(150):
    bg = requested_bg if requested_bg is not None else random.choice([c for c in range(10) if c != 5])
    palette = [c for c in range(10) if c not in (5, bg)]
    k = requested_k if requested_k is not None else random.choice([3, 3, 4, 4, 5])
    nmax = {3: 4, 4: 4, 5: 3}[k]
    nr = random.randint(2, nmax)
    nc = random.randint(2, nmax)
    n_src = random.randint(2, min(5, nr * nc))
    sources = random.sample(palette, n_src)
    targets = []
    for s in sources:
      opts = [c for c in palette if c != s and c not in targets]
      targets.append(random.choice(opts))
    fh = nr * (k + 1) + 3
    fw = nc * (k + 1) + 3
    height = requested_height if requested_height is not None else random.randint(min(30, fh + 4), 30)
    width = requested_width if requested_width is not None else random.randint(min(30, fw + 4), 30)
    if height < fh or width < fw:
      continue
    top = random.randint(0, height - fh)
    left = random.randint(0, width - fw)
    rects = [(top, left, fh, fw)]
    items = [("L", i) for i in range(n_src)] + [("T", i) for i in range(n_src)]
    random.shuffle(items)
    legend = [None] * n_src
    tpos = [None] * n_src
    ok = True
    for kind, i in items:
      h, w = (3, 4) if kind == "L" else (k, k)
      if h > height or w > width:
        ok = False
        break
      placed = False
      for _ in range(300):
        r = random.randint(0, height - h)
        c = random.randint(0, width - w)
        if _free(rects, r, c, h, w):
          rects.append((r, c, h, w))
          if kind == "L":
            legend[i] = (r, c, sources[i], targets[i])
          else:
            tpos[i] = (r, c)
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    positions = [(i, j) for i in range(nr) for j in range(nc)]
    random.shuffle(positions)
    cells = [[None] * nc for _ in range(nr)]
    for idx, s in enumerate(sources):
      i, j = positions[idx]
      cells[i][j] = s
    for (i, j) in positions[n_src:]:
      if random.random() < 0.7:
        cells[i][j] = random.choice(sources)
    used = set()
    templates = []
    for idx, s in enumerate(sources):
      m = _random_mask(k, used)
      used.add(tuple(m))
      templates.append((tpos[idx][0], tpos[idx][1], s, m))
    return dict(width=width, height=height, bg=bg, k=k,
                frame=(top, left, nr, nc), cells=cells,
                legend=legend, templates=templates)
  raise RuntimeError("could not pack legend, templates and frame in requested grid")


def generate(width=None, height=None, bg=None, k=None, frame=None,
             cells=None, legend=None, templates=None):
  """Build one input/output pair.

  Args:
    width, height: grid size of the input.
    bg: background colour (never 5).
    k: side length of the squares and templates.
    frame: (top, left, n_rows, n_cols) of the colour-5 frame; the frame is
      n*(k+1)+3 cells per side, squares sit at offset 2 + i*(k+1).
    cells: n_rows x n_cols list of source colours or None (empty cell).
    legend: list of (row, col, a, b) tiles meaning a -> b.
    templates: list of (row, col, colour, mask) with mask a list of k
      strings using '#' for filled and '.' for holes.
  All arguments None -> a fresh random scene.
  """
  if any(v is not None and not 1 <= v <= 30 for v in (width, height)):
    raise ValueError("grid sides must be 1..30")
  if bg is not None and (bg not in range(10) or bg == 5):
    raise ValueError("background must be an ARC colour other than 5")
  if k is not None and k not in (3, 4, 5):
    raise ValueError("template size must be 3..5")
  if legend is None:
    if any(v is not None for v in (frame, cells, templates)):
      raise ValueError("explicit frame or templates require a complete legend")
    s = _sample_scene(width, height, bg, k)
    width, height, bg, k = s["width"], s["height"], s["bg"], s["k"]
    frame, cells = s["frame"], s["cells"]
    legend, templates = s["legend"], s["templates"]
  top, left, nr, nc = frame
  mapping = {a: b for (_, _, a, b) in legend}
  masks = {col: m for (_, _, col, m) in templates}
  fh = nr * (k + 1) + 3
  fw = nc * (k + 1) + 3

  def blank_frame():
    g = common.grid(fw, fh, bg)
    for r in range(fh):
      for c in range(fw):
        if r in (0, fh - 1) or c in (0, fw - 1):
          g[r][c] = 5
    return g

  fin = blank_frame()
  out = blank_frame()
  for i in range(nr):
    for j in range(nc):
      col = cells[i][j]
      if col is None:
        continue
      y = 2 + i * (k + 1)
      x = 2 + j * (k + 1)
      m = masks[col]
      for dr in range(k):
        for dc in range(k):
          fin[y + dr][x + dc] = col
          out[y + dr][x + dc] = mapping[col] if m[dr][dc] == "#" else bg

  grid = common.grid(width, height, bg)
  for r in range(fh):
    for c in range(fw):
      grid[top + r][left + c] = fin[r][c]
  for (r, c, a, b) in legend:
    pat = [[a, a, b, b], [a, a, a, b], [a, a, b, b]]
    for dr in range(3):
      for dc in range(4):
        grid[r + dr][c + dc] = pat[dr][dc]
  for (r, c, col, m) in templates:
    for dr in range(k):
      for dc in range(k):
        if m[dr][dc] == "#":
          grid[r + dr][c + dc] = col
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=24, height=23, bg=8, k=3, frame=(8, 3, 3, 4),
               cells=[[3, 1, 3, 1], [3, 1, None, 3], [None, 3, 1, 1]],
               legend=[(0, 0, 1, 4), (4, 0, 3, 2)],
               templates=[(1, 6, 1, ["#.#", "###", ".#."]),
                          (1, 11, 3, ["#.#", "###", "###"])]),
      generate(width=23, height=22, bg=1, k=4, frame=(8, 5, 2, 3),
               cells=[[2, 6, 3], [3, 2, 6]],
               legend=[(0, 0, 2, 4), (4, 0, 3, 8), (8, 0, 6, 7)],
               templates=[(1, 6, 2, ["####", "####", "#.##", "#.##"]),
                          (1, 11, 3, ["####", ".##.", "####", "#..#"]),
                          (1, 17, 6, ["####", "##..", "##..", "####"])]),
  ]
  test = [
      generate(width=30, height=30, bg=4, k=5, frame=(9, 0, 3, 3),
               cells=[[3, None, 9], [3, 2, 1], [None, 8, 2]],
               legend=[(0, 0, 3, 9), (0, 5, 9, 2), (4, 0, 1, 6),
                       (4, 5, 8, 7), (0, 25, 2, 1)],
               templates=[
                   (1, 11, 3, ["##..#", "#...#", "#.###", "#####", "##..#"]),
                   (1, 18, 8, ["##..#", "##..#", "#....", "##..#", "#####"]),
                   (7, 23, 9, ["#####", "#....", "#####", "..##.", "#####"]),
                   (13, 23, 2, ["#####", "#####", "#...#", "#...#", "#.###"]),
                   (20, 23, 1, ["#....", "#####", "##..#", "#####", "#...."]),
               ]),
  ]
  return {"train": train, "test": test}
