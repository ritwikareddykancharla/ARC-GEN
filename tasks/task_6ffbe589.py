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

"""ARC-GEN style generator for task 6ffbe589.

Rule: the input holds one large square nested figure. The figure is made of
single-colour layers. The rest of the grid holds a few tiny loose pieces, at
most one per colour, and these pieces form a legend. The output is the
figure's bounding box, cropped out. Inside the box, the cells of each colour
are rotated clockwise about the box centre as one rigid layer. The number of
quarter turns equals the cell count of that colour's legend piece. A colour
with no legend piece stays where it is.

Scope: the background is always 0. The figure box is square, because a
quarter turn has to map the box onto itself, so this is intrinsic. By default
the box side is 8..13 and there are 2..4 layers. Explicit smaller input grids
may shrink the box below 8. Each layer occupies its own
contiguous band of Chebyshev ring depths, so a rotated layer can never
collide with another layer. Layer styles are frame-with-bumps, checkerboard,
dashed and dense-random.

Legend pieces are random orthogonal polyominoes with 1..9 cells; some colours
deliberately get no piece. Counts 4 and 8 make a complete cycle, while 5..9
exercise wrap-around. Optional distinct_turns requires all four orientations
of every nonzero-turn legend layer to differ.

Grid height and width are sampled independently in max(16, n+5)..24. The
fixtures are 20x20; other sizes are synthetic extensions. Each legend piece
is kept at Chebyshev distance >= 3 from the figure box and >= 2 from every
other piece, so the figure / legend split is never ambiguous.
"""

import collections
import random

import common


_DEFAULT_SIZES = (1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 9)


def _depth(r, c, n):
  return min(r, c, n - 1 - r, n - 1 - c)


def _rot_cw(cells, n, k):
  out = set()
  for r, c in cells:
    for _ in range(k):
      r, c = c, n - 1 - r
    out.add((r, c))
  return out


def _render_output(fig, leg_sizes):
  """Rotate every colour layer of the cropped figure by its legend count."""
  n = len(fig)
  out = [[0] * n for _ in range(n)]
  cols = sorted({v for row in fig for v in row if v})
  order = [c for c in cols if leg_sizes.get(c, 0) % 4 == 0]
  order += [c for c in cols if leg_sizes.get(c, 0) % 4]
  for col in order:
    cells = {(r, c) for r in range(n) for c in range(n) if fig[r][c] == col}
    for r, c in _rot_cw(cells, n, leg_sizes.get(col, 0) % 4):
      out[r][c] = col
  return out


def _cluster_count(cells):
  """8-connected components, merged when within Chebyshev distance 2."""
  cells = set(cells)
  seen, comps = set(), []
  for start in sorted(cells):
    if start in seen:
      continue
    seen.add(start)
    stack, comp = [start], []
    while stack:
      r, c = stack.pop()
      comp.append((r, c))
      for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
          q = (r + dr, c + dc)
          if q in cells and q not in seen:
            seen.add(q)
            stack.append(q)
    comps.append(comp)
  par = list(range(len(comps)))

  def find(i):
    while par[i] != i:
      i = par[i]
    return i

  for i in range(len(comps)):
    for j in range(i + 1, len(comps)):
      if find(i) == find(j):
        continue
      if any(max(abs(a - c), abs(b - d)) <= 2
             for a, b in comps[i] for c, d in comps[j]):
        par[find(i)] = find(j)
  return len({find(i) for i in range(len(comps))})


def _random_figure(n, colors):
  """Concentric bands of ring depths, one colour per band, outermost first."""
  depths = (n + 1) // 2
  cuts = sorted(random.sample(range(1, depths), len(colors) - 1))
  bounds = [0] + cuts + [depths]
  fig = [[0] * n for _ in range(n)]
  for i, col in enumerate(colors):
    a, b = bounds[i], bounds[i + 1]
    band = [(r, c) for r in range(n) for c in range(n)
            if a <= _depth(r, c, n) < b]
    style = random.choice(["frame", "frame", "checker", "dashed", "dense"])
    if style == "frame":
      f = random.randrange(a, b)
      p = random.uniform(0.15, 0.35)
      for r, c in band:
        if _depth(r, c, n) == f or random.random() < p:
          fig[r][c] = col
    elif style == "checker":
      par = random.randint(0, 1)
      for r, c in band:
        if (r + c) % 2 == par:
          fig[r][c] = col
    elif style == "dashed":
      run = random.randint(2, 4)
      period = run + random.randint(1, 3)
      offset = random.randrange(period)
      for r, c in band:
        d = _depth(r, c, n)
        side = n - 2 * d
        y, x = r - d, c - d
        if y == 0:
          pos = x
        elif x == side - 1:
          pos = side - 1 + y
        elif y == side - 1:
          pos = 3 * (side - 1) - x
        else:
          pos = 4 * (side - 1) - y
        if (pos + offset) % period < run:
          fig[r][c] = col
    else:
      p = random.uniform(0.4, 0.7)
      for r, c in band:
        if random.random() < p:
          fig[r][c] = col
  return fig


def _shape(k):
  """Random orthogonally connected polyomino with k cells."""
  cells = {(0, 0)}
  while len(cells) < k:
    frontier = {(r + dr, c + dc) for r, c in cells
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))} - cells
    cells.add(random.choice(sorted(frontier)))
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return sorted((r - r0, c - c0) for r, c in cells)


def _place_legend(height, width, top, left, n, pieces):
  """Place pieces far from the box and from each other; None if impossible."""
  occupied, result = set(), []
  for col, shape in pieces:
    hs = max(r for r, _ in shape) + 1
    ws = max(c for _, c in shape) + 1
    options = []
    for r0 in range(height - hs + 1):
      for c0 in range(width - ws + 1):
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        if any(top - 3 < r < top + n + 2 and left - 3 < c < left + n + 2
               for r, c in cells):
          continue
        if any((r + a, c + b) in occupied for r, c in cells
               for a in (-1, 0, 1) for b in (-1, 0, 1)):
          continue
        options.append(cells)
    if not options:
      return None
    cells = random.choice(options)
    occupied.update(cells)
    result.append((col, cells))
  return result


def _assemble(width, height, fig, top, left, placed):
  n = len(fig)
  grid = common.grid(width, height, 0)
  for r in range(n):
    for c in range(n):
      if fig[r][c]:
        grid[top + r][left + c] = fig[r][c]
  for col, cells in placed:
    for r, c in cells:
      grid[r][c] = col
  leg_sizes = {col: len(cells) for col, cells in placed}
  return grid, _render_output(fig, leg_sizes)


def generate(size=None, width=None, height=None, box_size=None,
             num_layers=None, colors=None, legend_sizes=None, figure=None,
             top=None, left=None, legend=None, distinct_turns=False):
  """Returns an input/output pair for task 6ffbe589.

  Args:
    size: side of a square input grid. Sets both width and height.
    width: input grid width (random max(16, n+5)..24).
    height: input grid height (random max(16, n+5)..24).
    box_size: side n of the square nested figure (random 8..13).
    num_layers: number of colour layers (random 2..min(4, ring depths)).
    colors: layer colours, outermost band first (random distinct 1..9).
    legend_sizes: dict colour -> legend piece size. Colours that are absent
      or map to 0 get no piece. Sizes must be 1..9.
      This argument requires colors.
    figure: explicit figure as a list of digit strings (box rows), used for
      fixture replay together with size/top/left/legend.
    top: row of the figure box's top-left corner.
    left: column of the figure box's top-left corner.
    legend: list of (colour, [(row, col), ...]) absolute legend-piece cells
      (replay only).
    distinct_turns: require four distinct orientations for every layer with
      a nonzero-turn legend. Random mode only; may reject infeasible settings.
  """
  for name, value in (("size", size), ("width", width), ("height", height),
                      ("box_size", box_size), ("num_layers", num_layers),
                      ("top", top), ("left", left)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  if type(distinct_turns) is not bool:
    raise ValueError("distinct_turns must be a bool")
  if any(v is not None and v < 0 for v in (top, left)):
    raise ValueError("figure offsets must be nonnegative")
  if size is not None:
    if width not in (None, size) or height not in (None, size):
      raise ValueError("size conflicts with width/height")
    width = height = size
  for d in (width, height):
    if d is not None and not 1 <= d <= 30:
      raise ValueError("grid dimensions must be 1..30")

  if figure is not None:
    if (legend is None or top is None or left is None or width is None
        or height is None):
      raise ValueError("figure replay needs legend, top, left and grid size")
    if any(p is not None for p in (box_size, num_layers, colors,
                                   legend_sizes)) or distinct_turns:
      raise ValueError("random-scene controls cannot be used with figure")
    if (not figure or not all(isinstance(row, str) for row in figure)
        or any(ch not in '0123456789' for row in figure for ch in row)):
      raise ValueError("figure must contain digit strings")
    fig = [[int(ch) for ch in row] for row in figure]
    n = len(fig)
    if any(len(row) != n for row in fig):
      raise ValueError("figure must be square")
    if not (0 <= top <= height - n and 0 <= left <= width - n):
      raise ValueError("figure does not fit in the grid")
    placed = [(col, [tuple(x) for x in cells]) for col, cells in legend]
    if len({col for col, _ in placed}) != len(placed):
      raise ValueError("at most one legend piece per colour")
    occupied = set()
    palette = {v for row in fig for v in row if v}
    for col, cells in placed:
      if type(col) is not int or col not in palette or not cells:
        raise ValueError("legend colours must occur in the figure")
      points = set(cells)
      if len(points) != len(cells):
        raise ValueError("legend cells must be distinct")
      for r, c in cells:
        if (type(r) is not int or type(c) is not int
            or not 0 <= r < height or not 0 <= c < width):
          raise ValueError("legend cell out of bounds")
        if top - 3 < r < top + n + 2 and left - 3 < c < left + n + 2:
          raise ValueError("legend must be at least distance 3 from the figure box")
        if any((r + a, c + b) in occupied
               for a in (-1, 0, 1) for b in (-1, 0, 1)):
          raise ValueError("separate legend pieces must not touch")
      seen = {cells[0]}
      todo = [cells[0]]
      while todo:
        r, c = todo.pop()
        for a in (-1, 0, 1):
          for b in (-1, 0, 1):
            q = (r + a, c + b)
            if q in points and q not in seen:
              seen.add(q)
              todo.append(q)
      if seen != points:
        raise ValueError("each legend piece must be 8-connected")
      occupied.update(points)
    grid, out = _assemble(width, height, fig, top, left, placed)
    return {"input": grid, "output": out}
  if legend is not None:
    raise ValueError("legend cells are only accepted with an explicit figure")

  if colors is not None:
    colors = list(colors)
    if (len(set(colors)) != len(colors) or not colors
        or any(type(c) is not int or not 1 <= c <= 9 for c in colors)):
      raise ValueError("colors must be distinct values in 1..9")
    if num_layers is not None and num_layers != len(colors):
      raise ValueError("num_layers disagrees with len(colors)")
    num_layers = len(colors)
  if num_layers is not None and not 1 <= num_layers <= 9:
    raise ValueError("num_layers must be 1..9")
  if legend_sizes is not None:
    if colors is None:
      raise ValueError("legend_sizes requires colors")
    legend_sizes = dict(legend_sizes)
    if any(type(c) is not int or type(k) is not int or not 0 <= k <= 9
           for c, k in legend_sizes.items()):
      raise ValueError("legend counts must be integer values in 0..9")
    legend_sizes = {c: k for c, k in legend_sizes.items() if k}
    if any(c not in colors for c in legend_sizes):
      raise ValueError("legend_sizes keys must be layer colours")
    if not legend_sizes:
      raise ValueError("at least one colour needs a legend piece")

  min_n = 2 * num_layers - 1 if num_layers else 3
  if box_size is not None:
    if not 3 <= box_size <= 24 or box_size < min_n:
      raise ValueError("box_size out of range for the requested layers")
    n_lo = n_hi = box_size
    if any(d is not None and box_size > d for d in (width, height)):
      raise ValueError("box_size exceeds the input grid")
    if width is not None and height is not None and max(width, height) < box_size + 3:
      raise ValueError("no space for a legend separated from the box")
    if (colors is not None and legend_sizes is not None
        and box_size == 2 * len(colors) - 1
        and legend_sizes.get(colors[-1], 0) % 4
        and (distinct_turns or set(legend_sizes) == {colors[-1]})):
      raise ValueError("centre-only layer cannot make a visible rotation")
    if ((top is not None and height is not None and top + box_size > height)
        or (left is not None and width is not None and left + box_size > width)):
      raise ValueError("figure offset and box_size exceed the grid")
  else:
    n_hi = max(13, min_n)
    dims = [d for d in (width, height) if d is not None]
    if dims:
      n_hi = min(n_hi, min(dims) - 4)
    n_lo = max(min_n, min(8, n_hi))
    if n_lo > n_hi:
      raise ValueError("grid too small for the requested figure")

  for _ in range(2000):
    n = random.randint(n_lo, n_hi)
    depths = (n + 1) // 2
    if colors is not None:
      cols = list(colors)
    else:
      nl = num_layers if num_layers else random.randint(2, min(4, depths))
      cols = random.sample(range(1, 10), nl)
    if len(cols) > depths:
      continue
    fig = _random_figure(n, cols)
    cells = {(r, c) for r in range(n) for c in range(n) if fig[r][c]}
    if {fig[r][c] for r, c in cells} != set(cols):
      continue
    if not (any(fig[0]) and any(fig[n - 1]) and
            any(fig[r][0] for r in range(n)) and
            any(fig[r][n - 1] for r in range(n))):
      continue
    if _cluster_count(cells) != 1:
      continue
    if legend_sizes is not None:
      leg = dict(legend_sizes)
    else:
      leg = {col: random.choice(_DEFAULT_SIZES) for col in cols
             if random.random() < 0.75}
    visible = False
    distinct = True
    for col, k in leg.items():
      layer = {(r, c) for r, c in cells if fig[r][c] == col}
      if _rot_cw(layer, n, k % 4) != layer:
        visible = True
      if k % 4 and len({frozenset(_rot_cw(layer, n, turn))
                       for turn in range(4)}) != 4:
        distinct = False
    if (not leg or (not visible and any(k % 4 for k in leg.values()))
        or distinct_turns and not distinct):
      continue
    if sum(leg.values()) + 5 >= len(cells):
      continue
    lo = min(30, max(16, n + 5))
    hi = max(lo, 24)
    h = height if height is not None else random.randint(lo, hi)
    w = width if width is not None else random.randint(lo, hi)
    if n > h or n > w:
      continue
    t = top if top is not None else random.randint(0, h - n)
    l = left if left is not None else random.randint(0, w - n)
    if not (0 <= t <= h - n and 0 <= l <= w - n):
      continue
    pieces = [(col, _shape(k)) for col, k in leg.items()]
    random.shuffle(pieces)
    placed = _place_legend(h, w, t, l, n, pieces)
    if placed is None:
      continue
    grid, out = _assemble(w, h, fig, t, l, placed)
    counts = collections.Counter(v for row in grid for v in row)
    if any(counts[c] >= counts[0] for c in counts if c):
      continue
    return {"input": grid, "output": out}
  raise RuntimeError("could not build a valid scene for these parameters")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  p1 = ["0030300000000", "0333333333330", "3388088808030", "0380880888830",
        "0308006008030", "0388666608833", "0380060600830", "0388066668833",
        "0308006008030", "3388880888830", "0308088808030", "0333333333330",
        "0000033000000"]
  p2 = ["5050555505", "0003000000", "5003333005", "0330400305",
        "5030440330", "5030444305", "5030000305", "5003333005",
        "0000300000", "5055055505"]
  p3 = ["4040404040", "0404040404", "4000010040", "0401001104",
        "4001220140", "0410221004", "4001100040", "0400110004",
        "4040404040", "0404040404"]
  t1 = ["0000055500000", "0000555550000", "0000000000000", "0000033000000",
        "5503333330055", "0000300033055", "5503304033055", "0000300033055",
        "5503333330055", "0000000300000", "0000000000000", "0000505050000",
        "0000050500000"]
  train = [
      generate(size=20, figure=p1, top=0, left=6,
               legend=[(8, [(16, 1), (17, 1)]), (3, [(18, 5)]),
                       (6, [(18, 9), (18, 10)])]),
      generate(size=20, figure=p2, top=2, left=6,
               legend=[(3, [(15, 1)]), (4, [(16, 4)])]),
      generate(size=20, figure=p3, top=9, left=1,
               legend=[(1, [(2, 8), (2, 9), (2, 10)]), (4, [(3, 14)])]),
  ]
  test = [
      generate(size=20, figure=t1, top=6, left=7,
               legend=[(5, [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)]),
                       (4, [(1, 7)]), (3, [(2, 1), (2, 2)])]),
  ]
  return {"train": train, "test": test}
