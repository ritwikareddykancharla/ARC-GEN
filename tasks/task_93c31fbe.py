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

"""ARC task 93c31fbe: mirror marker patterns inside bracket frames.

Rule: the grid holds several rectangular frames. Each frame is drawn only as
four L-shaped corner brackets of one colour. Each bracket is 3 cells in a
2x2 box. The grid also holds marker cells of colour 1. Every 1 outside all
frame boxes is erased. Inside each frame, the 1-pattern is kept and is
reflected about the frame's centre line along its longer dimension. Wide
frames mirror left-right and tall frames mirror up-down.

Scope of random scenes:
- An explicit width or height must be 5..30, and the longer side must be at
  least 6. When sampled, the lower bound of a side grows with the frame
  count, from 12 for one frame up to 26.
- There are 1..5 non-square frames in random scenes. If num_frames is None,
  a target in 2..4 is clamped once to the capacity of a uniform 5x6 or 6x5
  tiling on the requested canvas (using 30 for an unspecified side).
  This is a conservative packing bound, not the maximum possible count.
  The chosen count is retained across placement retries. After 50 failed
  rejection-packing attempts, a random tile partition supplies separated
  boxes with the same count; frame sizes and offsets still vary.
- One frame colour from 2..9 is used per scene. The background is 0 and the
  marker colour is 1.
- Each frame is at least 5x6. The short side is at most 10 and the long side
  at most 20. Sizes beyond the fixture range are synthetic extensions.
- Frame boxes never overlap or touch, not even diagonally. At least one empty
  row or column lies between any two boxes, as in train pair 3.
- Each frame holds one to three small 8-connected clusters of 1s. Clusters may
  merge. They lie strictly inside one half of the frame interior, on a random
  side. Every mirrored cell is therefore new, and the pair is never an
  identity.
- Stray 1-blobs of 1..4 cells lie outside every frame box as distractors.
  Strays are never 8-adjacent to each other. They are best-effort: a frame
  covering the canvas leaves no exterior, and after 50 failed pattern draws
  a labelled small-grid fallback uses one interior cell per frame and no
  strays to preserve background dominance.
- Background 0 is kept strictly the most frequent colour in both input and
  output. This keeps the background unambiguous on very small grids.

Explicit scenes are given as width, height, colour, frame boxes and a list
of 1-cells. They are validated: integer values, in bounds, at least 5x5,
non-square, pairwise separated, no 1 on a bracket, background 0 strictly
dominant in the input, and output different from input. The fixtures are
rebuilt from these explicit latent parameters. Explicit lists may contain
more than five frames if num_frames is omitted. Output background dominance
is not required in explicit mode: the rule identifies the background from
input and can legitimately increase the marker count beyond it.
"""

import random

import common


_DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
          (1, -1), (1, 0), (1, 1)]
_BOX_ATTEMPTS = 200
_FILL_ATTEMPTS = 60
_FALLBACK_FROM = 50


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _bracket_cells(t, l, b, r):
  return [(t, l), (t, l + 1), (t + 1, l),
          (t, r - 1), (t, r), (t + 1, r),
          (b - 1, l), (b, l), (b, l + 1),
          (b, r - 1), (b, r), (b - 1, r)]


def _inside(cell, box):
  y, x = cell
  t, l, b, r = box
  return t <= y <= b and l <= x <= r


def _separated(a, c):
  """True when the boxes neither overlap nor touch, even diagonally.

  At least one empty row or one empty column must lie between them.
  """
  t, l, b, r = a
  t2, l2, b2, r2 = c
  return not (t <= b2 + 1 and t2 <= b + 1 and l <= r2 + 1 and l2 <= r + 1)


def _sample_boxes(height, width, n):
  """Place exactly n separated, non-square frame boxes, or return None."""
  boxes = []
  for _ in range(n):
    placed = False
    for _ in range(200):
      tall = random.random() < 0.5
      long_cap = min(20, height if tall else width)
      short_cap = min(10, width if tall else height, long_cap - 1)
      if short_cap < 5:
        continue
      short = random.randint(5, short_cap)
      long_ = random.randint(short + 1, min(short + 12, long_cap))
      h, w = (long_, short) if tall else (short, long_)
      t = random.randint(0, height - h)
      l = random.randint(0, width - w)
      box = (t, l, t + h - 1, l + w - 1)
      if all(_separated(box, other) for other in boxes):
        boxes.append(box)
        placed = True
        break
    if not placed:
      return None
  return boxes


def _tiled_boxes(height, width, n):
  """Construct a random separated tiling when rejection packing is too tight.

  This retains the requested frame count. Tile dimensions, frame dimensions,
  selected tiles and offsets vary; it does not replay a fixed scene.
  """
  layouts = [(nr,nc,mh,mw) for mh,mw in ((5,6),(6,5))
             for nr in range(1,n+1) for nc in range(1,n+1)
             if nr*nc >= n and nr*mh+nr-1 <= height and nc*mw+nc-1 <= width]
  if not layouts:
    return None
  nr,nc,mh,mw = random.choice(layouts)
  def partition(total, count, minimum):
    lengths = [minimum]*count
    for _ in range(total-(count-1)-count*minimum):
      lengths[random.randrange(count)] += 1
    starts, cursor = [], 0
    for length in lengths:
      starts.append(cursor)
      cursor += length+1
    return list(zip(starts,lengths))
  rows, cols = partition(height,nr,mh), partition(width,nc,mw)
  tiles = [(r,c,H,W) for r,H in rows for c,W in cols]
  boxes = []
  for r,c,H,W in random.sample(tiles,n):
    sizes = [(h,w) for h in range(5,min(20,H)+1)
             for w in range(5,min(20,W)+1) if h != w and min(h,w) <= 10]
    h,w = random.choice(sizes)
    t,l = r+random.randint(0,H-h), c+random.randint(0,W-w)
    boxes.append((t,l,t+h-1,l+w-1))
  return boxes


def _neighbourhood(cells):
  out = set()
  for (y, x) in cells:
    out.add((y, x))
    for dy, dx in _DIRS8:
      out.add((y + dy, x + dx))
  return out


def _grow_blob(seed, size, allowed, blocked):
  blob = {seed}
  for _ in range(60):
    if len(blob) >= size:
      break
    y, x = random.choice(sorted(blob))
    dy, dx = random.choice(_DIRS8)
    c = (y + dy, x + dx)
    if c in allowed and c not in blocked:
      blob.add(c)
  return blob


def _half_cells(box):
  """Interior cells strictly on one random side of the long-axis mirror."""
  t, l, b, r = box
  h, w = b - t + 1, r - l + 1
  side = random.choice([0, 1])
  allowed = []
  for y in range(t + 1, b):
    for x in range(l + 1, r):
      key = 2 * x - (l + r) if w > h else 2 * y - (t + b)
      if (side == 0 and key < 0) or (side == 1 and key > 0):
        allowed.append((y, x))
  return allowed


def _sample_pattern(box, single=False):
  """Return 1..3 small clusters (or one cell) inside one half of the box."""
  allowed = _half_cells(box)
  if single:
    return [random.choice(allowed)]
  allowed_set = set(allowed)
  cells = set()
  for _ in range(random.randint(1, 3)):
    free = [c for c in allowed if c not in cells]
    if not free:
      break
    seed = random.choice(free)
    cells |= _grow_blob(seed, random.randint(1, 5), allowed_set, cells)
  return sorted(cells)


def _sample_strays(height, width, boxes):
  """Return separate stray 1-blobs (1..4 cells) outside every frame box."""
  outside = set()
  for y in range(height):
    for x in range(width):
      if not any(_inside((y, x), bx) for bx in boxes):
        outside.add((y, x))
  strays = set()
  for _ in range(random.randint(1, 6)):
    blocked = _neighbourhood(strays)
    free = sorted(outside - blocked)
    if not free:
      break
    seed = random.choice(free)
    strays |= _grow_blob(seed, random.randint(1, 4), outside, blocked)
  return sorted(strays)


def _render(width, height, colour, frames, ones):
  """Draw the input and build the output from the latent scene."""
  grid = common.grid(width, height, 0)
  for (t, l, b, r) in frames:
    for (y, x) in _bracket_cells(t, l, b, r):
      grid[y][x] = colour
  for (y, x) in ones:
    if not (0 <= y < height and 0 <= x < width) or grid[y][x] == colour:
      raise ValueError('1-cell out of bounds or on a bracket')
    grid[y][x] = 1
  output = [row[:] for row in grid]
  for (y, x) in ones:
    output[y][x] = 0
  for (t, l, b, r) in frames:
    h, w = b - t + 1, r - l + 1
    for (y, x) in ones:
      if not _inside((y, x), (t, l, b, r)):
        continue
      output[y][x] = 1
      if w >= h:
        output[y][l + r - x] = 1
      else:
        output[t + b - y][x] = 1
  return grid, output


def _background_dominant(g):
  counts = {}
  for row in g:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  zeros = counts.get(0, 0)
  return all(zeros > n for v, n in counts.items() if v != 0)


def generate(width=None, height=None, colour=None, frames=None, ones=None,
             num_frames=None):
  """Build one input/output pair.

  Args:
    width: grid width (columns), an int. For random scenes it must be 5..30.
      If None, it is sampled with a lower bound that grows with the frame
      count. Required when frames is given (1..30).
    height: grid height (rows). Same conventions as width. For random scenes
      with both sides given, the longer side must be at least 6.
    colour: frame bracket colour, an int in 2..9. Sampled if None.
    frames: list of (top, left, bottom, right) frame boxes. Sampled if None.
      If given, ones, width and height must be given too. Boxes must be in
      bounds, at least 5x5, non-square, and must not overlap or touch.
    ones: list of (row, col) input cells of colour 1. It covers both the
      in-frame patterns and the strays. Only allowed together with frames.
    num_frames: number of frames (1..5). For random scenes it is honoured
      exactly. If it is None, a target in 2..4 is clamped to a conservative
      uniform-tiling capacity and retained through retries. Must equal
      len(frames) if both are given; explicit lists can exceed five when
      this control is omitted.
  """
  if colour is None:
    colour = random.choice([2, 3, 4, 5, 6, 7, 8, 9])
  if not _is_int(colour) or not 2 <= colour <= 9:
    raise ValueError('colour must be an int in 2..9')
  if num_frames is not None and (not _is_int(num_frames)
                                 or not 1 <= num_frames <= 5):
    raise ValueError('num_frames must be an int in 1..5')
  for v in (width, height):
    if v is not None and not _is_int(v):
      raise ValueError('width/height must be ints')
  if frames is None:
    if ones is not None:
      raise ValueError('ones requires explicit frames')
    for v in (width, height):
      if v is not None and not 5 <= v <= 30:
        raise ValueError('random scenes need width/height in 5..30')
    if width is not None and height is not None and max(width, height) < 6:
      raise ValueError('no non-square frame of at least 5x6 fits')
    base_n = num_frames if num_frames is not None else random.randint(2, 4)
    if num_frames is None:
      H, W = height or 30, width or 30
      capacity = max(((H+1)//6)*((W+1)//7), ((H+1)//7)*((W+1)//6))
      base_n = min(base_n, capacity)
      if base_n < 1:
        raise ValueError('no supported uniform frame tiling fits')
    boxes = None
    h = w = None
    for attempt in range(_BOX_ATTEMPTS):
      n = base_n
      lo = min(26, 8 + 4 * n)
      h = height if height is not None else random.randint(lo, 30)
      w = width if width is not None else random.randint(lo, 30)
      boxes = (_sample_boxes(h, w, n) if attempt < 50 else
               _tiled_boxes(h, w, n))
      if boxes is not None:
        break
    if boxes is None:
      raise ValueError('could not place the requested frames in the grid')
    height, width, frames = h, w, boxes
    for attempt in range(_FILL_ATTEMPTS):
      fallback = attempt >= _FALLBACK_FROM
      cells = set()
      for bx in frames:
        cells.update(_sample_pattern(bx, single=fallback))
      if not fallback:
        cells.update(_sample_strays(height, width, frames))
      grid, output = _render(width, height, colour, frames, sorted(cells))
      if _background_dominant(grid) and _background_dominant(output):
        return {'input': grid, 'output': output}
    raise ValueError('grid too small to keep background 0 dominant')
  if ones is None or width is None or height is None:
    raise ValueError('explicit frames need width, height and ones')
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError('width/height must be 1..30')
  for name, values in (("frames", frames), ("ones", ones)):
    if not isinstance(values, (list, tuple)) or not all(
        isinstance(v, (list, tuple)) for v in values):
      raise ValueError(name + " must be a list of coordinate tuples")
  frames = [tuple(f) for f in frames]
  if not frames:
    raise ValueError('at least one frame is required')
  if num_frames is not None and num_frames != len(frames):
    raise ValueError('num_frames disagrees with len(frames)')
  for f in frames:
    if len(f) != 4 or not all(_is_int(v) for v in f):
      raise ValueError('frames must be 4-tuples of ints')
    t, l, b, r = f
    if not (0 <= t and b < height and 0 <= l and r < width):
      raise ValueError('frame out of bounds')
    if b - t < 4 or r - l < 4:
      raise ValueError('frames must be at least 5x5')
    if b - t == r - l:
      raise ValueError('square frames have no defined mirror axis')
  for i in range(len(frames)):
    for j in range(i + 1, len(frames)):
      if not _separated(frames[i], frames[j]):
        raise ValueError('frames must not overlap or touch')
  ones = [tuple(c) for c in ones]
  for c in ones:
    if len(c) != 2 or not all(_is_int(v) for v in c):
      raise ValueError('ones must be (row, col) int pairs')
  grid, output = _render(width, height, colour, frames, ones)
  if not _background_dominant(grid):
    raise ValueError('background 0 must be the most frequent colour')
  if grid == output:
    raise ValueError('explicit scene produces an identity pair')
  return {'input': grid, 'output': output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=23, height=22, colour=8,
               frames=[(2, 3, 6, 9), (1, 16, 10, 21), (12, 6, 17, 14)],
               ones=[(3, 5), (5, 4), (5, 5),
                     (3, 17), (3, 18), (4, 20), (5, 18), (5, 19),
                     (13, 12), (15, 12), (15, 13), (16, 11),
                     (5, 12), (5, 13), (10, 1), (13, 2), (13, 21),
                     (14, 20), (20, 18)]),
      generate(width=25, height=23, colour=2,
               frames=[(1, 2, 5, 15), (3, 19, 10, 23), (8, 9, 19, 13)],
               ones=[(2, 6), (2, 7), (3, 5), (3, 6), (4, 8),
                     (5, 22), (6, 21),
                     (15, 10), (16, 11), (16, 12), (17, 10),
                     (13, 1), (13, 2), (14, 3), (15, 20), (18, 21),
                     (21, 3)]),
      generate(width=21, height=20, colour=3,
               frames=[(2, 3, 12, 9), (13, 11, 17, 17)],
               ones=[(8, 7), (9, 5), (9, 7), (10, 6), (10, 7), (10, 8),
                     (11, 5),
                     (14, 13), (15, 12), (15, 13),
                     (2, 13), (6, 17), (7, 18), (7, 19), (8, 19), (16, 6),
                     (17, 2), (17, 3), (18, 3)]),
  ]
  test = [
      generate(width=28, height=26, colour=4,
               frames=[(1, 2, 9, 7), (3, 12, 7, 19), (16, 3, 23, 14),
                       (10, 19, 22, 25)],
               ones=[(2, 4), (3, 4), (3, 5), (4, 3),
                     (4, 14), (5, 13), (6, 14),
                     (17, 6), (18, 5), (18, 6), (19, 8), (20, 4), (20, 6),
                     (20, 7), (21, 5), (21, 6), (22, 6),
                     (18, 23), (19, 21), (19, 22), (20, 22), (20, 23),
                     (21, 21),
                     (0, 15), (1, 23), (2, 24), (2, 25), (2, 26), (5, 25),
                     (11, 10), (12, 4), (12, 7), (12, 9), (12, 11),
                     (13, 4), (14, 17)]),
  ]
  return {'train': train, 'test': test}
