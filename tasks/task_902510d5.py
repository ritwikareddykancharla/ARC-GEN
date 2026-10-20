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

"""ARC-GEN style generator for task 902510d5.

Rule: the input holds one large single-colour figure made of diagonal
strokes. It is the unique largest 8-connected group of non-background cells.
The input also holds scattered noise pixels, and exactly one of them sits in
a grid corner (the marker). The output keeps the figure and erases all
noise, including noise that shares the figure's colour. It then draws a
filled right triangle in the marked corner, with its legs along the two
edges that meet there. The leg length n is the number of non-corner noise
pixels. The triangle colour is the strict most frequent colour among those
pixels. The marker's own colour never counts. The row on the corner's edge
has n cells, and each row further from that edge has one fewer.

Scope: random grids are 6..20 cells per side by default, and the width and
height controls accept 6..30. Sizes above the fixtures' 15 are a synthetic
extension, since the rule does not fix the size. The background is black (0).

The random figure is grown from connected diagonal strokes with occasional
orthogonal steps. It has at least 5 cells and contains no filled 2x2 block. Above side 15,
the target size spans roughly 5%..12.5% of the grid area; this avoids
merely putting the same tiny figure on a larger canvas.
It never covers a grid corner, the marker's neighbourhood or the triangle
area. The triangle may touch the figure, as it does in the fixtures.

Random scenes have 1..min(9, min(width, height) - 3) non-corner noise
pixels, 2.. by default. The cap of side-3 is deliberate: it keeps room for
the figure. Noise never touches the figure or the marker. At most one pair
of noise pixels touches, either orthogonally (as in the test input) or
diagonally (as in train pair 2). The noise colours always have a strict
mode. Figure-coloured strays may determine that mode, a consistent
synthetic extension of the fixtures where such strays contribute to the count.

Some hard cases are sampled on purpose:
- noise pixels share the figure colour;
- the marker colour equals the mode colour;
- the marker colour equals a runner-up colour, so that counting the marker
  would create a tie.

Explicit scenes accept sides 1..30. Only well-definedness is checked:
- the background is the strict plurality colour;
- exactly one corner is occupied;
- the figure is the unique largest 8-connected group;
- the noise colours have a strict mode;
- the triangle does not overlap the figure;
- n is at most min(width, height).
The stylistic figure invariants (at least 5 cells, no 2x2 block) apply only
to random scenes. All integer controls reject bools and non-integers.
"""

import collections
import random

import common

_CORNERS = ("tl", "tr", "bl", "br")
_DIAG = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
_ORTH = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _require_int(name, v):
  if not _is_int(v):
    raise ValueError(name + " must be an int")


def _corner_pos(corner, height, width):
  return {"tl": (0, 0), "tr": (0, width - 1),
          "bl": (height - 1, 0), "br": (height - 1, width - 1)}[corner]


def _triangle(corner, height, width, n):
  cy, cx = _corner_pos(corner, height, width)
  dy = 1 if cy == 0 else -1
  dx = 1 if cx == 0 else -1
  cells = []
  for d in range(n):
    y = cy + dy * d
    for k in range(n - d):
      x = cx + dx * k
      if 0 <= y < height and 0 <= x < width:
        cells.append((y, x))
  return cells


def _neigh(r, c):
  return [(r + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]


def _strict_mode(colors):
  counts = collections.Counter(colors).most_common()
  if not counts:
    return None
  if len(counts) > 1 and counts[0][1] == counts[1][1]:
    return None
  return counts[0][0]


def _components(grid, height, width):
  seen = set()
  comps = []
  for r in range(height):
    for c in range(width):
      if grid[r][c] == 0 or (r, c) in seen:
        continue
      stack = [(r, c)]
      seen.add((r, c))
      comp = []
      while stack:
        y, x = stack.pop()
        comp.append((y, x))
        for (a, b) in _neigh(y, x):
          if (0 <= a < height and 0 <= b < width and grid[a][b] != 0
              and (a, b) not in seen):
            seen.add((a, b))
            stack.append((a, b))
      comps.append(comp)
  return comps


def _check_scene(width, height, figure, figure_color, corner, corner_color,
                 noise):
  """Raises ValueError if the scene is ambiguous or malformed."""
  for name, v in (("width", width), ("height", height),
                  ("figure_color", figure_color),
                  ("corner_color", corner_color)):
    _require_int(name, v)
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid size out of range")
  if corner not in _CORNERS:
    raise ValueError("bad corner")
  if not (1 <= figure_color <= 9 and 1 <= corner_color <= 9):
    raise ValueError("bad colour")
  if not figure:
    raise ValueError("figure must be non-empty")
  if not noise:
    raise ValueError("need at least one non-corner noise pixel")
  for p in figure:
    if len(p) != 2 or not all(_is_int(v) for v in p):
      raise ValueError("figure cells must be (row, col) ints")
  for p in noise:
    if len(p) != 3 or not all(_is_int(v) for v in p):
      raise ValueError("noise cells must be (row, col, color) ints")
  n = len(noise)
  if n > min(width, height):
    raise ValueError("triangle leg longer than the grid side")
  grid = common.grid(width, height, 0)
  cells = [(r, c, figure_color) for (r, c) in figure] + list(noise)
  cells.append(_corner_pos(corner, height, width) + (corner_color,))
  for (r, c, col) in cells:
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError("cell out of bounds")
    if not 1 <= col <= 9:
      raise ValueError("bad colour")
    if grid[r][c] != 0:
      raise ValueError("overlapping cells")
    grid[r][c] = col
  for k in _CORNERS:
    if k != corner:
      r, c = _corner_pos(k, height, width)
      if grid[r][c] != 0 and (r, c) != _corner_pos(corner, height, width):
        raise ValueError("more than one corner occupied")
  counts = collections.Counter(v for row in grid for v in row)
  zeros = counts.get(0, 0)
  if any(v >= zeros for col, v in counts.items() if col != 0):
    raise ValueError("background is not the strict plurality colour")
  if set(_triangle(corner, height, width, n)) & set(figure):
    raise ValueError("triangle would overwrite the figure")
  comps = sorted(_components(grid, height, width), key=len, reverse=True)
  if set(comps[0]) != set(figure):
    raise ValueError("figure is not the largest connected group")
  if len(comps) > 1 and len(comps[1]) >= len(comps[0]):
    raise ValueError("largest group is not unique")
  if _strict_mode([col for (_, _, col) in noise]) is None:
    raise ValueError("noise colour mode is tied")


def _has_block(cells):
  s = set(cells)
  return any((r + 1, c) in s and (r, c + 1) in s and (r + 1, c + 1) in s
             for (r, c) in s)


def _make_figure(height, width, forbidden):
  area = height * width
  limit = max(6, area // 8)
  minimum = max(5, area // 20) if max(height, width) > 15 else 5
  for _ in range(60):
    r = random.randint(1, height - 2)
    c = random.randint(1, width - 2)
    if (r, c) in forbidden:
      continue
    cells = [(r, c)]
    seen = {(r, c)}
    target = random.randint(minimum, limit)
    for _ in range(max(24, 4 * target)):
      if len(cells) >= target:
        break
      sr, sc = random.choice(cells)
      d = random.choice(_DIAG) if random.random() < 0.85 else random.choice(_ORTH)
      for _ in range(random.randint(2, 5)):
        sr, sc = sr + d[0], sc + d[1]
        if not (0 <= sr < height and 0 <= sc < width):
          break
        if (sr, sc) in forbidden:
          break
        if (sr, sc) not in seen:
          candidate = seen | {(sr, sc)}
          if _has_block(candidate):
            break
          seen.add((sr, sc))
          cells.append((sr, sc))
          if len(cells) >= target:
            break
    if len(cells) >= target and not _has_block(cells):
      return cells
  return None


def _noise_colors(n, main=None):
  """Returns n colours with a strict mode, plus that mode."""
  if main is None:
    main = random.randint(1, 9)
  if n == 1:
    return [main], main
  k = random.randint(2, n)
  cols = [main] * k
  counts = {}
  pool = [x for x in range(1, 10) if x != main]
  rest = n - k
  if rest >= k - 1 and random.random() < 0.5:
    x = random.choice(pool)
    cols.extend([x] * (k - 1))
    counts[x] = k - 1
    rest -= k - 1
  for _ in range(rest):
    options = [x for x in pool if counts.get(x, 0) < k - 1]
    x = random.choice(options)
    counts[x] = counts.get(x, 0) + 1
    cols.append(x)
  random.shuffle(cols)
  return cols, main


def _pick_figure_color(given, cols, mode):
  if given is not None:
    return given
  if random.random() < 0.4:
    others = sorted(set(x for x in cols if x != mode))
    if others and random.random() < 0.7:
      return random.choice(others)
    return random.choice(sorted(set(cols)))
  return random.randint(1, 9)


def _pick_corner_color(given, cols, mode):
  if given is not None:
    return given
  counts = collections.Counter(cols)
  top = counts[mode]
  runners = sorted(x for x, v in counts.items() if x != mode and v == top - 1)
  r = random.random()
  if runners and r < 0.45:
    return random.choice(runners)
  if r < 0.6:
    return mode
  return random.randint(1, 9)


def _place_noise(height, width, n, blocked):
  """Places n isolated noise cells; optionally one touching pair.

  The pair partner may be any of the 8 neighbours, so both orthogonal and
  diagonal noise contacts occur, as in the fixtures.
  """
  cand = [(r, c) for r in range(height) for c in range(width)
          if (r, c) not in blocked]
  random.shuffle(cand)
  chosen = []
  paired = False

  def near(cell, exclude):
    return any(abs(cell[0] - a) <= 1 and abs(cell[1] - b) <= 1
               for (a, b) in chosen if (a, b) != exclude)

  for (r, c) in cand:
    if len(chosen) >= n:
      break
    if near((r, c), None):
      continue
    chosen.append((r, c))
    if not paired and len(chosen) < n and random.random() < 0.3:
      opts = [(r + a, c + b) for (a, b) in _ORTH + _DIAG
              if 0 <= r + a < height and 0 <= c + b < width
              and (r + a, c + b) not in blocked
              and not near((r + a, c + b), (r, c))]
      if opts:
        chosen.append(random.choice(opts))
        paired = True
  return chosen if len(chosen) == n else None


def _sample_scene(width, height, corner, figure_color, corner_color,
                  num_noise, tri_color):
  for name, val in (("width", width), ("height", height)):
    if val is not None:
      _require_int(name, val)
      if not 6 <= val <= 30:
        raise ValueError(name + " must be in 6..30 for random scenes")
  if corner is not None and corner not in _CORNERS:
    raise ValueError("corner must be one of tl, tr, bl, br")
  for name, val in (("figure_color", figure_color),
                    ("corner_color", corner_color), ("tri_color", tri_color)):
    if val is not None:
      _require_int(name, val)
      if not 1 <= val <= 9:
        raise ValueError(name + " must be in 1..9")
  if num_noise is not None:
    _require_int("num_noise", num_noise)
    if not 1 <= num_noise <= 9:
      raise ValueError("num_noise must be in 1..9")
    if width is not None and num_noise > width - 3:
      raise ValueError("num_noise too large for width")
    if height is not None and num_noise > height - 3:
      raise ValueError("num_noise too large for height")
  for _ in range(400):
    h = height if height is not None else random.randint(6, 20)
    w = width if width is not None else random.randint(6, 20)
    max_n = min(9, min(h, w) - 3)
    if num_noise is not None:
      if num_noise > max_n:
        continue
      n = num_noise
    else:
      n = random.randint(2, max_n)
    k = corner if corner is not None else random.choice(_CORNERS)
    kpos = _corner_pos(k, h, w)
    corners = [_corner_pos(x, h, w) for x in _CORNERS]
    forbidden = set(_triangle(k, h, w, n))
    forbidden.update(corners)
    forbidden.update(_neigh(*kpos))
    figure = _make_figure(h, w, forbidden)
    if figure is None:
      continue
    blocked = set(corners)
    for (r, c) in figure:
      blocked.update(_neigh(r, c))
    blocked.update(_neigh(*kpos))
    pos = _place_noise(h, w, n, blocked)
    if pos is None:
      continue
    cols, mode = _noise_colors(n, tri_color)
    noise = [(r, c, col) for (r, c), col in zip(pos, cols)]
    fc = _pick_figure_color(figure_color, cols, mode)
    cc = _pick_corner_color(corner_color, cols, mode)
    try:
      _check_scene(w, h, figure, fc, k, cc, noise)
    except ValueError:
      continue
    return w, h, figure, fc, k, cc, noise
  raise RuntimeError("could not sample a scene with the requested controls")


def generate(width=None, height=None, figure=None, figure_color=None,
             corner=None, corner_color=None, noise=None, num_noise=None,
             tri_color=None):
  """Build one input/output pair.

  Explicit mode: give figure and noise, together with width, height,
  figure_color, corner and corner_color. A missing value raises ValueError,
  and the scene is checked for ambiguity. Random mode: leave figure and noise
  as None. Any of the other arguments then constrain the sampled scene.

  Args:
    width: grid width (6..30 in random mode, 1..30 in explicit mode).
    height: grid height (6..30 in random mode, 1..30 in explicit mode).
    figure: list of (row, col) cells of the main diagonal figure.
    figure_color: colour of the main figure (1..9).
    corner: one of 'tl', 'tr', 'bl', 'br'; the corner holding the marker.
    corner_color: colour of the corner marker pixel (1..9).
    noise: list of (row, col, color) non-corner noise pixels. Their count
      gives the triangle leg and their strict mode colour gives its colour.
    num_noise: requested number of non-corner noise pixels (the triangle
      leg); in random mode 1..min(9, min(width, height) - 3).
    tri_color: requested strict-mode noise colour (triangle colour).
  """
  if figure is not None or noise is not None:
    required = (("width", width), ("height", height), ("figure", figure),
                ("figure_color", figure_color), ("corner", corner),
                ("corner_color", corner_color), ("noise", noise))
    missing = [name for name, val in required if val is None]
    if missing:
      raise ValueError("explicit scene missing: " + ", ".join(missing))
    for name, cells in (("figure", figure), ("noise", noise)):
      if not isinstance(cells, (list, tuple)) or not all(
          isinstance(p, (list, tuple)) for p in cells):
        raise ValueError(name + " must be a list of coordinate tuples")
    figure = [tuple(p) for p in figure]
    noise = [tuple(p) for p in noise]
    _check_scene(width, height, figure, figure_color, corner, corner_color,
                 noise)
    if num_noise is not None:
      _require_int("num_noise", num_noise)
      if num_noise != len(noise):
        raise ValueError("num_noise disagrees with noise")
    if tri_color is not None:
      _require_int("tri_color", tri_color)
      if tri_color != _strict_mode([col for (_, _, col) in noise]):
        raise ValueError("tri_color disagrees with noise")
  else:
    (width, height, figure, figure_color, corner, corner_color,
     noise) = _sample_scene(width, height, corner, figure_color, corner_color,
                            num_noise, tri_color)
  grid = common.grid(width, height, 0)
  output = common.grid(width, height, 0)
  for (r, c) in figure:
    grid[r][c] = figure_color
    output[r][c] = figure_color
  for (r, c, col) in noise:
    grid[r][c] = col
  cy, cx = _corner_pos(corner, height, width)
  grid[cy][cx] = corner_color
  n = len(noise)
  tri = _strict_mode([col for (_, _, col) in noise])
  for (r, c) in _triangle(corner, height, width, n):
    output[r][c] = tri
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=9, height=6,
               figure=[(0, 6), (1, 5), (2, 4), (2, 6), (3, 7)], figure_color=2,
               corner="br", corner_color=3,
               noise=[(0, 1, 4), (4, 3, 4)]),
      generate(width=11, height=11,
               figure=[(2, 7), (3, 8), (4, 8), (4, 9), (5, 7), (5, 10), (6, 6)],
               figure_color=7, corner="bl", corner_color=8,
               noise=[(3, 4, 1), (4, 2, 2), (6, 3, 3), (8, 3, 7), (9, 4, 2)]),
      generate(width=14, height=15,
               figure=[(2, 8), (2, 9), (2, 10), (3, 7), (4, 6), (4, 7), (5, 5),
                       (5, 8), (6, 5), (6, 9), (7, 5), (7, 10), (8, 11),
                       (9, 12), (10, 13)],
               figure_color=8, corner="br", corner_color=6,
               noise=[(1, 13, 6), (4, 11, 6), (14, 3, 3), (14, 7, 6)]),
      generate(width=10, height=10,
               figure=[(3, 3), (4, 4), (4, 6), (5, 5), (6, 4)], figure_color=8,
               corner="tl", corner_color=9,
               noise=[(6, 8, 7), (7, 1, 7), (9, 1, 4), (9, 4, 8), (9, 8, 3)]),
  ]
  test = [
      generate(width=11, height=12,
               figure=[(5, 3), (6, 0), (6, 2), (7, 0), (7, 1), (8, 1), (8, 2)],
               figure_color=3, corner="tr", corner_color=2,
               noise=[(0, 1, 4), (0, 3, 7), (2, 0, 2), (3, 0, 8), (3, 2, 4)]),
  ]
  return {"train": train, "test": test}
