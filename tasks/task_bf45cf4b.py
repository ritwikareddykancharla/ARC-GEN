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

"""Generator for ARC task bf45cf4b (stencil-driven tile stamping).

Rule: two objects sit on a uniform background.
  * The tile is a multicoloured rectangle whose outer ring is entirely
    non-background.
  * The stencil is drawn in a single colour and may be disconnected.
The output measures (stencil height x tile height) by (stencil width x tile
width) and starts filled with background. A copy of the tile is stamped into
block (r, c) wherever the stencil's bounding-box mask has a cell at (r, c).
The stencil colour never appears in the output.

Scope of random generation:
  * Most tiles are squares with sides 3..5, as in the fixtures. About a
    quarter are non-square rectangles with sides 3..5. Non-square tiles are a
    synthetic extension that the rule permits.
  * Tiles use 2-3 non-background colours. Most are mirror symmetric. Some
    square tiles are also diagonally symmetric, and some tiles are arbitrary.
  * A tile's interior may contain background holes, as in the first fixture.
  * Stencils are random 0/1 masks with 2..6 rows and columns. Each mask
    touches all four sides of its bounding box and has at least one empty
    cell. A mask may be disconnected.
  * The output is at most 30x30.
  * The tile and the stencil are separated by at least one full background
    row or column, so they never touch, even diagonally.
  * The background is always the strict plurality colour of the input: it
    outnumbers every other colour individually.
  * Random grid sides are 10..22 unless the caller supplies them. Sizes above
    the fixtures' 17 are a synthetic extension that the rule permits.
  * A caller-supplied width or height is honoured. Random tile and mask
    sizes are redrawn, with bounded retries, until they fit that size.

Explicit arguments:
  * Latent arguments reconstruct the fixtures exactly.
  * An explicit tile may be a rectangle with sides 1..30 whose ring is
    non-background. Its full-bounding-box, 8-connected component must use
    at least two colours and outrank other tile components by colour count,
    then cell count. Interior disconnected islands remain supported when
    that condition holds; ambiguous tile identification is rejected.
  * An explicit mask may be any 0/1 rectangle that touches all four sides.
    This includes full masks and masks with a dimension of 1. The transform
    handles these cases unambiguously.
  * The four placement arguments must be given together, and only together
    with an explicit tile and mask. Incompatible, partial or non-integer
    arguments (including booleans) raise ValueError.
"""

import collections
import random

import common


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _identifiable_tile(tile, bg):
  """The unique highest-ranked multicolour component spans the whole tile."""
  h, w = len(tile), len(tile[0])
  remaining = {(r, c) for r in range(h) for c in range(w)
               if tile[r][c] != bg}
  ranked = []
  while remaining:
    first = remaining.pop()
    cells, pending = {first}, [first]
    while pending:
      r, c = pending.pop()
      adjacent = {(r + dy, c + dx) for dy in (-1, 0, 1)
                  for dx in (-1, 0, 1)} & remaining
      remaining -= adjacent
      cells |= adjacent
      pending.extend(adjacent)
    colours = {tile[r][c] for r, c in cells}
    bounds = (min(r for r, c in cells), min(c for r, c in cells),
              max(r for r, c in cells), max(c for r, c in cells))
    ranked.append(((len(colours), len(cells)), bounds))
  ranked.sort(reverse=True)
  return bool(ranked) and ranked[0][0][0] >= 2 and (
      len(ranked) == 1 or ranked[0][0] > ranked[1][0]) and (
      ranked[0][1] == (0, 0, h - 1, w - 1))


def _make_tile(th, tw, bg, palette):
  """Builds a th x tw tile whose border ring is entirely non-background."""
  for _ in range(200):
    mode = random.random()
    colors = {}
    tile = []
    for r in range(th):
      row = []
      for c in range(tw):
        border = r in (0, th - 1) or c in (0, tw - 1)
        if mode < 0.8:
          key = (min(r, th - 1 - r), min(c, tw - 1 - c))
          if mode < 0.4 and th == tw:
            key = tuple(sorted(key))
        else:
          key = (r, c)
        if key not in colors:
          if border or random.random() < 0.7:
            colors[key] = random.choice(palette)
          else:
            colors[key] = bg
        row.append(colors[key])
      tile.append(row)
    used = set(v for row in tile for v in row if v != bg)
    if len(used) >= 2 and _identifiable_tile(tile, bg):
      return tile
  # Randomised constructive fallback: ring in one colour, centre cross in
  # another.
  a, b = random.sample(palette, 2)
  tile = [[a] * tw for _ in range(th)]
  for i in range(1, tw - 1):
    tile[th // 2][i] = b
  for i in range(1, th - 1):
    tile[i][tw // 2] = b
  return tile


def _make_mask(sh, sw):
  """Random mask touching all sides of its bounding box, with a hole."""
  for _ in range(300):
    p = random.uniform(0.45, 0.75)
    m = [[1 if random.random() < p else 0 for _ in range(sw)]
         for _ in range(sh)]
    if not any(m[0]) or not any(m[-1]):
      continue
    if not any(row[0] for row in m) or not any(row[-1] for row in m):
      continue
    total = sum(sum(row) for row in m)
    if total == sh * sw or total < 2:
      continue
    return m
  # Fallback: full box minus one random cell. Since sh, sw >= 2, the
  # bounding box is preserved.
  m = [[1] * sw for _ in range(sh)]
  m[random.randrange(sh)][random.randrange(sw)] = 0
  return m


def _gap(a0, a1, b0, b1):
  """True if inclusive intervals are separated by at least one cell."""
  return a1 + 1 < b0 or b1 + 1 < a0


def _check_color(name, v):
  if not _is_int(v) or not 0 <= v <= 9:
    raise ValueError(name + " must be an integer colour 0..9")


def _check_tile(tile, bg):
  if not isinstance(tile, list) or not tile or not isinstance(tile[0], list):
    raise ValueError("tile must be a non-empty list of rows")
  th = len(tile)
  if len(tile[0]) < 1:
    raise ValueError("tile must be non-empty")
  if any(not isinstance(row, list) or len(row) != len(tile[0])
         for row in tile):
    raise ValueError("tile must be a rectangle")
  tw = len(tile[0])
  if th > 30 or tw > 30:
    raise ValueError("tile sides must be within 1..30")
  for r in range(th):
    for c in range(tw):
      v = tile[r][c]
      _check_color("tile cell", v)
      if (r in (0, th - 1) or c in (0, tw - 1)) and v == bg:
        raise ValueError("tile border ring must be non-background")
  if len(set(v for row in tile for v in row if v != bg)) < 2:
    raise ValueError("tile needs at least two non-background colours")
  if not _identifiable_tile(tile, bg):
    raise ValueError("tile's full-box multicolour component must be identifiable")


def _check_mask(mask):
  if not isinstance(mask, list) or not mask or not isinstance(mask[0], list):
    raise ValueError("mask must be a non-empty list of rows")
  if len(mask[0]) < 1:
    raise ValueError("mask must be non-empty")
  if any(not isinstance(row, list) or len(row) != len(mask[0])
         for row in mask):
    raise ValueError("mask must be a rectangle")
  if any(not _is_int(v) or v not in (0, 1) for row in mask for v in row):
    raise ValueError("mask values must be the integers 0 or 1")
  if not any(mask[0]) or not any(mask[-1]):
    raise ValueError("mask must touch its top and bottom rows")
  if not any(row[0] for row in mask) or not any(row[-1] for row in mask):
    raise ValueError("mask must touch its left and right columns")


def _layout_options(th, tw, sh, sw, width, height):
  """Lists separated arrangements compatible with any given width/height."""
  options = []
  for orient in ("v", "h"):
    if orient == "v":
      nh, nw = th + sh + 1, max(tw, sw)
    else:
      nh, nw = max(th, sh), tw + sw + 1
    if nh > 30 or nw > 30:
      continue
    if height is not None and height < nh:
      continue
    if width is not None and width < nw:
      continue
    options.append((orient, nh, nw))
  return options


def _place(th, tw, sh, sw, width, height, options):
  """Chooses grid size and separated positions for one layout option."""
  orient, nh, nw = random.choice(options)
  if height is None:
    height = random.randint(max(10, nh), max(10, nh, 22))
  if width is None:
    width = random.randint(max(10, nw), max(10, nw, 22))
  first = random.random() < 0.5
  if orient == "v":
    extra = height - th - sh
    gap = random.randint(1, extra)
    top = random.randint(0, extra - gap)
    if first:
      tile_row, stencil_row = top, top + th + gap
    else:
      stencil_row, tile_row = top, top + sh + gap
    tile_col = random.randint(0, width - tw)
    stencil_col = random.randint(0, width - sw)
  else:
    extra = width - tw - sw
    gap = random.randint(1, extra)
    left = random.randint(0, extra - gap)
    if first:
      tile_col, stencil_col = left, left + tw + gap
    else:
      stencil_col, tile_col = left, left + sw + gap
    tile_row = random.randint(0, height - th)
    stencil_row = random.randint(0, height - sh)
  return width, height, tile_row, tile_col, stencil_row, stencil_col


def _background_dominant(grid, bg):
  """True if bg strictly outnumbers every other colour (plurality)."""
  counts = collections.Counter(v for row in grid for v in row)
  return all(counts[bg] > n for c, n in counts.items() if c != bg)


def _random_tile_shape(max_height=5, max_width=5):
  shapes = [(h, w) for h in range(3, min(5, max_height) + 1)
            for w in range(3, min(5, max_width) + 1)]
  if not shapes:
    raise ValueError("mask too large for a random tile with sides at least 3")
  # Same unconstrained mixture: 75% square, 25% non-square. Condition
  # directly on output-size feasibility instead of rejecting valid masks.
  return random.choices(shapes, weights=[6 if h == w else 1
                                        for h, w in shapes])[0]


def generate(width=None, height=None, background=None, tile=None,
             tile_row=None, tile_col=None, mask=None, stencil_color=None,
             stencil_row=None, stencil_col=None):
  """Returns an input/output pair.

  Args:
    width: input grid width, 1..30 (random if None; must fit the layout).
    height: input grid height, 1..30 (random if None; must fit the layout).
    background: background colour 0..9 (random if None).
    tile: the tile, as a list of rows of colours. Its border ring must be
      non-background, and it must use at least two non-background colours.
      Its highest-ranked component must span its full box. Random if None.
    tile_row: top row of the tile in the input.
    tile_col: left column of the tile in the input.
    mask: stencil mask (list of rows of 0/1) touching all box sides.
      Random if None.
    stencil_color: the single colour used to draw the stencil. It must not
      be the background or appear in the tile. Random if None.
    stencil_row: top row of the stencil bounding box in the input.
    stencil_col: left column of the stencil bounding box in the input.

  The four placement arguments must be given all together or not at all.
  If they are given, tile and mask must be given too.
  """
  for name, v in (("width", width), ("height", height)):
    if v is not None and (not _is_int(v) or not 1 <= v <= 30):
      raise ValueError(name + " must be an integer 1..30")
  if background is None:
    background = random.randint(0, 9)
  _check_color("background", background)
  bg = background
  if stencil_color is not None:
    _check_color("stencil_color", stencil_color)
    if stencil_color == bg:
      raise ValueError("stencil colour must differ from background")
  positions = (tile_row, tile_col, stencil_row, stencil_col)
  explicit_place = all(p is not None for p in positions)
  if not explicit_place and any(p is not None for p in positions):
    raise ValueError("give all four placement arguments or none")
  if explicit_place:
    if any(not _is_int(p) for p in positions):
      raise ValueError("placement arguments must be integers")
    if tile is None or mask is None:
      raise ValueError("explicit placement requires explicit tile and mask")
  if tile is not None:
    _check_tile(tile, bg)
    used = set(v for row in tile for v in row)
    if stencil_color is not None and stencil_color in used:
      raise ValueError("stencil colour must not appear in the tile")
    if not [c for c in range(10) if c != bg and c not in used]:
      raise ValueError("no colour left for the stencil")
    if mask is None and (30 // len(tile) < 2 or 30 // len(tile[0]) < 2):
      raise ValueError("tile too large for a random stencil of side >= 2")
  if mask is not None:
    _check_mask(mask)
    if tile is None and (30 // len(mask) < 3 or 30 // len(mask[0]) < 3):
      raise ValueError("mask too large for a random tile with sides at least 3")
  if tile is not None and mask is not None:
    if len(mask) * len(tile) > 30 or len(mask[0]) * len(tile[0]) > 30:
      raise ValueError("output would exceed 30x30")
  fixed = (tile is not None and mask is not None and width is not None
           and height is not None)

  for _ in range(100):
    sc = stencil_color
    t = tile
    if t is None:
      if sc is None:
        sc = random.choice([c for c in range(10) if c != bg])
      rth, rtw = _random_tile_shape(
          30 // len(mask) if mask is not None else 5,
          30 // len(mask[0]) if mask is not None else 5)
      others = [c for c in range(10) if c not in (bg, sc)]
      random.shuffle(others)
      palette = others[:random.choice([2, 3])]
      t = _make_tile(rth, rtw, bg, palette)
    th, tw = len(t), len(t[0])
    if sc is None:
      used = set(v for row in t for v in row)
      sc = random.choice([c for c in range(10)
                          if c != bg and c not in used])
    m = mask
    if m is None:
      m = _make_mask(random.randint(2, min(6, 30 // th)),
                     random.randint(2, min(6, 30 // tw)))
    sh, sw = len(m), len(m[0])
    if sh * th > 30 or sw * tw > 30:
      raise ValueError("output would exceed 30x30")

    if explicit_place:
      w, h = width, height
      if h is None:
        need = max(tile_row + th, stencil_row + sh)
        h = random.randint(max(10, need), max(10, need, 22))
      if w is None:
        need = max(tile_col + tw, stencil_col + sw)
        w = random.randint(max(10, need), max(10, need, 22))
      if not (1 <= w <= 30 and 1 <= h <= 30):
        raise ValueError("grid size out of range")
      if (min(positions) < 0 or tile_row + th > h or stencil_row + sh > h
          or tile_col + tw > w or stencil_col + sw > w):
        raise ValueError("objects out of bounds")
      if not (_gap(tile_row, tile_row + th - 1, stencil_row,
                   stencil_row + sh - 1)
              or _gap(tile_col, tile_col + tw - 1, stencil_col,
                      stencil_col + sw - 1)):
        raise ValueError("tile and stencil must be separated by background")
      t_row, t_col, s_row, s_col = positions
    else:
      options = _layout_options(th, tw, sh, sw, width, height)
      if not options:
        if tile is not None and mask is not None:
          raise ValueError("width/height too small to separate the objects")
        continue
      w, h, t_row, t_col, s_row, s_col = _place(th, tw, sh, sw, width,
                                                height, options)

    grid = common.grid(w, h, bg)
    for r in range(th):
      for c in range(tw):
        grid[t_row + r][t_col + c] = t[r][c]
    for r in range(sh):
      for c in range(sw):
        if m[r][c]:
          grid[s_row + r][s_col + c] = sc
    if not _background_dominant(grid, bg):
      if fixed:
        raise ValueError("background must be the strict plurality colour")
      continue

    output = common.grid(sw * tw, sh * th, bg)
    for r in range(sh):
      for c in range(sw):
        if not m[r][c]:
          continue
        for y in range(th):
          for x in range(tw):
            output[r * th + y][c * tw + x] = t[y][x]
    return {"input": grid, "output": output}
  raise ValueError("could not build a scene satisfying the given arguments")


def validate():
  """Reconstructs the canonical examples from explicit latent parameters."""
  train = [
      generate(width=12, height=12, background=4,
               tile=[[8, 3, 8], [3, 4, 3], [8, 3, 8]], tile_row=5,
               tile_col=1,
               mask=[[1, 1, 0, 1], [1, 0, 1, 1], [0, 1, 0, 1]],
               stencil_color=2, stencil_row=1, stencil_col=6),
      generate(width=17, height=12, background=3,
               tile=[[8, 8, 8], [8, 2, 8], [8, 8, 8]], tile_row=5,
               tile_col=8,
               mask=[[1, 0, 0], [0, 1, 0], [0, 1, 0], [1, 1, 1]],
               stencil_color=1, stencil_row=2, stencil_col=2),
      generate(width=12, height=12, background=1,
               tile=[[8, 9, 9, 8], [9, 4, 4, 9], [9, 4, 4, 9],
                     [8, 9, 9, 8]], tile_row=6, tile_col=5,
               mask=[[1, 1, 1], [1, 0, 1], [0, 1, 0]],
               stencil_color=6, stencil_row=2, stencil_col=1),
  ]
  test = [
      generate(width=13, height=14, background=8,
               tile=[[6, 6, 3, 6, 6], [6, 4, 3, 4, 6], [3, 3, 3, 3, 3],
                     [6, 4, 3, 4, 6], [6, 6, 3, 6, 6]], tile_row=1,
               tile_col=1,
               mask=[[0, 1, 1, 1, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1],
                     [1, 0, 1, 0, 1], [1, 1, 1, 1, 1]],
               stencil_color=1, stencil_row=7, stencil_col=6),
  ]
  return {"train": train, "test": test}
