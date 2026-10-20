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

"""ARC task 8f215267: count same-coloured shapes and tally them inside frames.

Rule: the input has a left column of hollow rectangular frames. All frames in
a scene share one size, each frame has its own colour, and consecutive frames
are separated by one background row. Small solid shapes are scattered to the
right of the frames, and sometimes below them.

In the output every small shape is erased to background. Each frame then gets
n single dots of its own colour on its middle row, where n is the number of
small (4-connected) shapes of that frame's colour. The dots start two columns
inside the frame's right edge and step two columns leftwards: x1-2, x1-4, and
so on. Shapes whose colour has no frame (distractors) simply vanish.

Scope. The random path samples all of these:
  - the background colour;
  - the number of frames (2-5) and their distinct colours. A single frame is
    used only when requested, or when a supplied height admits no more;
  - the frame origin, the frame size and the grid size;
  - the per-frame shape counts (0..capacity, at least one shape overall);
  - 0-2 distractor colours, each used 1-2 times;
  - the shape templates (dominoes, bars, squares, plus signs, L, T, S and F
    shapes) under random rotation and reflection, and their positions.

Every original example uses 5x11 frames, and the default sampler favours that
size. These are synthetic extensions that are consistent with the rule:
  - frame widths 7, 9 and 13, and frame height 7 (random path);
  - explicit odd frame widths up to 27 and frame heights 3 and 9;
  - one-frame scenes. Six or seven frames require explicit frame_height=3
    and sufficient canvas height. More than seven cannot fit in 30 rows.
Explicit non-ring patterns may be larger than the native template catalogue,
including solid blocks or borders with filled interiors. These are counted
as shapes, while a completely hollow border is reserved for a frame.
A frame of width W holds at most (W-2)//2 dots. Counts above that capacity
are never sampled or accepted, so the tally is never truncated.

Every scene keeps the following invariants:
  - every shape keeps an 8-neighbour gap from the frames and from every other
    shape;
  - patterns are 4-connected and are never hollow rings, so no shape can read
    as a frame;
  - distractor colours never coincide with frame colours or the background;
  - the background is the strict plurality colour;
  - input != output.
"""

import collections
import random

import common


SHAPES = [
  ['##'],
  ['##', '##'],
  ['###', '###'],
  ['.#.', '###', '.#.'],
  ['#.', '##'],
  ['###'],
  ['###', '.#.'],
  ['.##', '##.'],
  ['.#.', '###', '###', '.#.'],
  ['.##.', '####', '.##.'],
  ['..#..', '#####', '..#..'],
  ['..#', '###', '.#.'],
  ['#..', '###'],
]

FRAME_H = 5
FRAME_W = 11
RANDOM_FRAME_WIDTHS = [11, 11, 11, 9, 13, 7]
RANDOM_FRAME_HEIGHTS = [5, 5, 5, 7]


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _cells(pattern):
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == '#']


def _capacity(frame_w):
  return (frame_w - 2) // 2


def _orient(pattern):
  """Applies a random rotation and reflection to a template."""
  rows = list(pattern)
  for _ in range(random.randint(0, 3)):
    rows = [''.join(rows[r][c] for r in range(len(rows) - 1, -1, -1))
            for c in range(len(rows[0]))]
  if random.random() < 0.5:
    rows = [row[::-1] for row in rows]
  return rows


def _check_colour(value, name):
  if not _is_int(value) or not 0 <= value <= 9:
    raise ValueError(name + ' must be an integer colour 0..9')


def _check_opt_int(value, name, lo, hi):
  if value is not None and (not _is_int(value) or not lo <= value <= hi):
    raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))


def _check_frame_width(frame_w):
  if not _is_int(frame_w) or frame_w < 7 or frame_w > 27 or (
      frame_w % 2 == 0):
    raise ValueError('frame_width must be odd in 7..27')


def _check_frame_height(frame_h):
  if not _is_int(frame_h) or frame_h < 3 or frame_h > 9 or (
      frame_h % 2 == 0):
    raise ValueError('frame_height must be odd in 3..9')


def _check_pattern(pattern):
  """Requires a non-empty, rectangular, 4-connected, non-ring pattern."""
  if isinstance(pattern, str) or not isinstance(pattern, (list, tuple)):
    raise ValueError('pattern must be a list of strings, not a bare string')
  if not pattern or any(not isinstance(row, str) for row in pattern):
    raise ValueError('pattern must be a non-empty list of strings')
  pw = len(pattern[0])
  if pw == 0 or any(len(row) != pw for row in pattern):
    raise ValueError('pattern rows must be non-empty and of equal length')
  if any(ch not in '#.' for row in pattern for ch in row):
    raise ValueError('pattern may only contain # and .')
  cells = set(_cells(pattern))
  if not cells:
    raise ValueError('pattern must contain at least one filled cell')
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  if len(seen) != len(cells):
    raise ValueError('pattern must be 4-connected')
  r0 = min(r for r, _ in cells)
  r1 = max(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  c1 = max(c for _, c in cells)
  if r1 - r0 >= 2 and c1 - c0 >= 2:
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    if cells == border:
      raise ValueError('a hollow-ring pattern would read as a frame')


def _boxes(left, top, frame_w, frame_h, n):
  out = []
  for i in range(n):
    r0 = top + (frame_h + 1) * i
    out.append((r0, left, r0 + frame_h - 1, left + frame_w - 1))
  return out


def _box_cells(boxes):
  cells = set()
  for r0, c0, r1, c1 in boxes:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        cells.add((r, c))
  return cells


def _gap_ok(cells, occupied):
  for r, c in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        if (r + dy, c + dx) in occupied:
          return False
  return True


def _bg_dominant(grid, background):
  tally = collections.Counter(v for row in grid for v in row)
  return all(tally[background] > k for c, k in tally.items()
             if c != background)


def _build(width, height, background, left, top, frame_w, frame_h,
           frame_colors, shapes):
  """Draws input and output from explicit latent parameters."""
  grid = common.grid(width, height, background)
  out = common.grid(width, height, background)
  boxes = _boxes(left, top, frame_w, frame_h, len(frame_colors))
  cap = _capacity(frame_w)
  for col, (r0, c0, r1, c1) in zip(frame_colors, boxes):
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        if r in (r0, r1) or c in (c0, c1):
          grid[r][c] = col
          out[r][c] = col
    count = sum(1 for s in shapes if s[0] == col)
    if count > cap:
      raise ValueError('more shapes than the frame can tally')
    mid = r0 + frame_h // 2
    for k in range(count):
      out[mid][c1 - 2 - 2 * k] = col
  for col, r0, c0, pattern in shapes:
    for dr, dc in _cells(pattern):
      grid[r0 + dr][c0 + dc] = col
  return {'input': grid, 'output': out}


def _check_scene(width, height, background, left, top, frame_w, frame_h,
                 frame_colors, shapes):
  """Rejects explicit scenes that are out of bounds or ambiguous."""
  if not _is_int(width) or not _is_int(height) or not (
      1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError('grid size must be integers 1..30')
  _check_colour(background, 'background')
  _check_frame_width(frame_w)
  _check_frame_height(frame_h)
  if not _is_int(left) or not _is_int(top) or left < 0 or top < 0:
    raise ValueError('left and top must be non-negative integers')
  if isinstance(frame_colors, str) or not isinstance(
      frame_colors, (list, tuple)):
    raise ValueError('frame_colors must be a list of colours')
  fc = list(frame_colors)
  if not fc:
    raise ValueError('at least one frame colour is required')
  for c in fc:
    _check_colour(c, 'frame colour')
  if len(set(fc)) != len(fc) or background in fc:
    raise ValueError('frame colours must be distinct and differ from background')
  boxes = _boxes(left, top, frame_w, frame_h, len(fc))
  for r0, c0, r1, c1 in boxes:
    if r1 >= height or c1 >= width:
      raise ValueError('frame out of bounds')
  if not isinstance(shapes, (list, tuple)) or not shapes:
    raise ValueError('at least one small shape is required (else identity)')
  occupied = _box_cells(boxes)
  for shape in shapes:
    if not isinstance(shape, (list, tuple)) or len(shape) != 4:
      raise ValueError('each shape is (colour, row, col, pattern)')
    col, r0, c0, pattern = shape
    _check_colour(col, 'shape colour')
    if col == background:
      raise ValueError('shape colour equals background')
    if not _is_int(r0) or not _is_int(c0):
      raise ValueError('shape row and col must be integers')
    _check_pattern(pattern)
    cells = [(r0 + dr, c0 + dc) for dr, dc in _cells(pattern)]
    for r, c in cells:
      if not (0 <= r < height and 0 <= c < width):
        raise ValueError('shape out of bounds')
    if not _gap_ok(cells, occupied):
      raise ValueError('shape touches (8-neighbour) a frame or another shape')
    occupied.update(cells)
  cap = _capacity(frame_w)
  for col in fc:
    if sum(1 for s in shapes if s[0] == col) > cap:
      raise ValueError('more shapes than the frame can tally')


def _place(width, height, left, top, frame_w, frame_h, nframes, plan):
  """Places shapes with an 8-neighbourhood gap from frames and each other."""
  occupied = _box_cells(_boxes(left, top, frame_w, frame_h, nframes))
  below = top + (frame_h + 1) * nframes
  placed = []
  for col in plan:
    ok = False
    for _ in range(300):
      pattern = _orient(random.choice(SHAPES))
      ph, pw = len(pattern), len(pattern[0])
      if ph > height or pw > width:
        continue
      r0 = random.randint(0, height - ph)
      c0 = random.randint(0, width - pw)
      cells = [(r0 + dr, c0 + dc) for dr, dc in _cells(pattern)]
      if any(c < left + frame_w + 1 and r < below for r, c in cells):
        continue
      if not _gap_ok(cells, occupied):
        continue
      occupied.update(cells)
      placed.append((col, r0, c0, pattern))
      ok = True
      break
    if not ok:
      return None
  return placed


def generate(width=None, height=None, background=None, left=None, top=None,
             frame_colors=None, shapes=None, frame_width=None,
             frame_height=None, num_frames=None, counts=None,
             distractor_colors=None):
  """Returns an input/output pair.

  Args:
    width: grid width 1..30 (random when None; 9-13 columns right of frames).
    height: grid height 1..30. It must fit all frames. When None it is random,
      with extra rows under the frames (more rows when the strip right of the
      frames is narrow).
    background: background colour 0..9. When None it is random and never a
      frame or distractor colour.
    left: column of the frames' left edge, 0..29 (random 1..2, or 0 if needed).
    top: row of the first frame's top edge, 0..29 (random 1..2, or 0 if
      needed).
    frame_colors: list of distinct frame colours 0..9, top to bottom.
    shapes: list of (colour, row, col, pattern) small shapes, where each
      pattern is a list of strings with '#' for filled cells. When shapes is
      given, the scene is drawn exactly. The caller must then also give width,
      height, background, left, top and frame_colors. frame_width and
      frame_height default to 11 and 5. num_frames, counts and
      distractor_colors must not be given. Shapes must keep an 8-neighbour gap
      from frames and from each other.
    frame_width: odd frame width 7..27 (random from 7, 9, 11, 13; 11 favoured).
    frame_height: odd frame height 3..9 (random from 5, 7; 5 favoured).
    num_frames: number of frames 1..7 (random 2..5 subject to height).
      Six or seven require frame_height=3 and sufficient grid height.
    counts: per-frame number of same-coloured shapes, each 0..capacity
      (random when None).
    distractor_colors: colours of frameless shapes, each used 1-2 times. When
      None, 0-2 colours are drawn, and at least one if every count is 0.

  Raises:
    ValueError for invalid or clearly infeasible controls. RuntimeError if a
    valid but very tight request cannot be placed within the bounded retries.
  """
  if shapes is not None:
    needed = {'width': width, 'height': height, 'background': background,
              'left': left, 'top': top, 'frame_colors': frame_colors}
    missing = [k for k, v in needed.items() if v is None]
    if missing:
      raise ValueError('explicit shapes require: ' + ', '.join(missing))
    if num_frames is not None or counts is not None or (
        distractor_colors is not None):
      raise ValueError('num_frames/counts/distractor_colors conflict with shapes')
    fw = FRAME_W if frame_width is None else frame_width
    fh = FRAME_H if frame_height is None else frame_height
    _check_scene(width, height, background, left, top, fw, fh,
                 frame_colors, shapes)
    pair = _build(width, height, background, left, top, fw, fh,
                  list(frame_colors), shapes)
    if not _bg_dominant(pair['input'], background):
      raise ValueError('background must be the most frequent colour')
    return pair

  _check_opt_int(width, 'width', 1, 30)
  _check_opt_int(height, 'height', 1, 30)
  _check_opt_int(left, 'left', 0, 29)
  _check_opt_int(top, 'top', 0, 29)
  _check_opt_int(num_frames, 'num_frames', 1, 7)
  if background is not None:
    _check_colour(background, 'background')
  if frame_width is not None:
    _check_frame_width(frame_width)
  if frame_height is not None:
    _check_frame_height(frame_height)
  sizes = set()
  if frame_colors is not None:
    if not isinstance(frame_colors, (list, tuple)):
      raise ValueError('frame_colors must be a list of colours')
    frame_colors = list(frame_colors)
    for c in frame_colors:
      _check_colour(c, 'frame colour')
    if not frame_colors or len(set(frame_colors)) != len(frame_colors):
      raise ValueError('frame_colors must be a non-empty distinct list')
    if background is not None and background in frame_colors:
      raise ValueError('background collides with a frame colour')
    sizes.add(len(frame_colors))
  dcl = []
  if distractor_colors is not None:
    if not isinstance(distractor_colors, (list, tuple)):
      raise ValueError('distractor_colors must be a list of colours')
    dcl = list(distractor_colors)
    for c in dcl:
      _check_colour(c, 'distractor colour')
    if len(set(dcl)) != len(dcl):
      raise ValueError('distractor colours must be distinct')
    if frame_colors is not None and set(dcl) & set(frame_colors):
      raise ValueError('distractor colours collide with frame colours')
    if background is not None and background in dcl:
      raise ValueError('distractor colour collides with background')
  if counts is not None:
    if not isinstance(counts, (list, tuple)):
      raise ValueError('counts must be a list of integers')
    counts = list(counts)
    if not counts:
      raise ValueError('counts must be non-empty')
    if any(not _is_int(k) or k < 0 for k in counts):
      raise ValueError('counts must be non-negative integers')
    max_cap = _capacity(frame_width if frame_width is not None
                        else max(RANDOM_FRAME_WIDTHS))
    if max(counts) > max_cap:
      raise ValueError('counts exceed the frame capacity')
    if sum(counts) == 0 and distractor_colors is not None and not dcl:
      raise ValueError('zero counts and no distractors give an identity pair')
    sizes.add(len(counts))
  if num_frames is not None:
    sizes.add(num_frames)
  if len(sizes) > 1:
    raise ValueError('frame_colors, counts and num_frames disagree')
  n_req = sizes.pop() if sizes else None
  if background is None:
    used = set(frame_colors or []) | set(dcl)
    if len(used) >= 10:
      raise ValueError('no colour left for the background')
  if frame_colors is None:
    avail = [c for c in range(10) if c != background and c not in dcl]
    if len(avail) - (1 if background is None else 0) < (n_req or 1):
      raise ValueError('not enough colours left for the frames')
  fw_lo = frame_width if frame_width is not None else min(RANDOM_FRAME_WIDTHS)
  fh_lo = frame_height if frame_height is not None else min(
      RANDOM_FRAME_HEIGHTS)
  if (left or 0) + fw_lo > (width if width is not None else 30):
    raise ValueError('frames do not fit in the requested width')
  if (top or 0) + (n_req or 1) * (fh_lo + 1) - 1 > (
      height if height is not None else 30):
    raise ValueError('frames do not fit in the requested height')

  for _ in range(300):
    fw = frame_width if frame_width is not None else random.choice(
        RANDOM_FRAME_WIDTHS)
    fh = frame_height if frame_height is not None else random.choice(
        RANDOM_FRAME_HEIGHTS)
    cap = _capacity(fw)
    if counts is not None and max(counts) > cap:
      continue
    wmax = width if width is not None else 30
    hmax = height if height is not None else 30
    lf = left if left is not None else random.choice([1, 2])
    if lf + fw > wmax:
      if left is not None or fw > wmax:
        continue
      lf = 0
    t = top if top is not None else random.choice([1, 2])
    max_n = (hmax - t + 1) // (fh + 1)
    if top is None and max_n < (n_req or 2):
      t = 0
      max_n = (hmax + 1) // (fh + 1)
    if n_req is not None:
      n = n_req
      if n > max_n:
        continue
    else:
      hi = min(5, max_n)
      if hi < 1:
        continue
      n = random.randint(2, hi) if hi >= 2 else 1
    min_h = t + n * (fh + 1) - 1
    if min_h > hmax:
      continue
    w = width if width is not None else min(
        30, lf + fw + 1 + random.randint(9, 13))
    if w < lf + fw:
      continue
    strip = w - (lf + fw + 1)
    if height is not None:
      h = height
    elif strip >= 5:
      h = random.randint(min(min_h + 1, 30), min(30, min_h + 6))
    else:
      h = min(30, min_h + random.randint(6, 10))
    used = set(frame_colors or []) | set(dcl)
    bg = background if background is not None else random.choice(
        [c for c in range(10) if c not in used])
    if frame_colors is not None:
      fc = list(frame_colors)
    else:
      pool = [c for c in range(10) if c != bg and c not in dcl]
      if len(pool) < n:
        continue
      fc = random.sample(pool, n)
    if counts is not None:
      cnts = list(counts)
    else:
      cnts = [random.randint(0, cap) for _ in range(n)]
      if sum(cnts) == 0 or sum(cnts) > 13:
        continue
    others = [c for c in range(10) if c != bg and c not in fc]
    if distractor_colors is not None:
      dc = list(dcl)
    else:
      lo = 1 if sum(cnts) == 0 else 0
      hi_d = min(2, len(others))
      if hi_d < lo:
        continue
      dc = random.sample(others, random.randint(lo, hi_d))
    plan = []
    for c, k in zip(fc, cnts):
      plan += [c] * k
    for c in dc:
      plan += [c] * random.randint(1, 2)
    if not plan:
      continue
    random.shuffle(plan)
    placed = _place(w, h, lf, t, fw, fh, n, plan)
    if placed is None:
      continue
    pair = _build(w, h, bg, lf, t, fw, fh, fc, placed)
    if not _bg_dominant(pair['input'], bg):
      continue
    return pair
  raise RuntimeError('could not construct a scene with the given parameters')


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  train = [
    generate(width=23, height=23, background=1, left=1, top=1,
             frame_colors=[4, 8, 2], shapes=[
               (3, 1, 15, ['##', '##']),
               (8, 1, 20, ['##']),
               (4, 4, 18, ['##', '##']),
               (3, 7, 20, ['#', '#']),
               (4, 8, 15, ['##']),
               (2, 12, 16, ['###', '###']),
               (8, 16, 15, ['##', '##']),
               (8, 19, 18, ['#', '#']),
               (8, 20, 11, ['##']),
             ]),
    generate(width=23, height=23, background=8, left=2, top=2,
             frame_colors=[1, 6, 4], shapes=[
               (4, 1, 15, ['.#.', '###', '.#.']),
               (6, 1, 20, ['##']),
               (4, 4, 17, ['..#', '###', '.#.']),
               (2, 8, 15, ['##', '##']),
               (3, 8, 20, ['##', '#.']),
               (1, 11, 16, ['.#', '##']),
               (6, 17, 15, ['#', '#']),
               (6, 18, 17, ['##', '#.']),
             ]),
    generate(width=23, height=20, background=3, left=1, top=1,
             frame_colors=[2, 4, 1], shapes=[
               (1, 1, 15, ['.#.', '###', '###', '.#.']),
               (8, 7, 14, ['.#.', '###', '.#.']),
               (1, 7, 18, ['.##.', '####', '.##.']),
               (4, 13, 16, ['.#.', '###', '.#.']),
               (4, 17, 18, ['##', '##']),
             ]),
  ]
  test = [
    generate(width=23, height=27, background=8, left=1, top=1,
             frame_colors=[2, 4, 3, 1], shapes=[
               (1, 1, 14, ['.#.', '###', '.#.']),
               (4, 1, 19, ['##', '##']),
               (2, 5, 16, ['..#..', '#####', '..#..']),
               (4, 10, 19, ['.#', '##']),
               (2, 11, 14, ['##', '##']),
               (4, 15, 16, ['#.', '##']),
               (5, 15, 20, ['##']),
               (4, 19, 20, ['##', '##']),
               (3, 21, 14, ['.#.', '###', '.#.']),
               (9, 24, 19, ['##', '##']),
             ]),
  ]
  return {'train': train, 'test': test}
