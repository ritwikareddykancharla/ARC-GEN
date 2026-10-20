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

"""ARC-GEN style generator for task 7666fa5d.

Rule: the input holds several straight anti-diagonal segments of one colour
on a background of 8. A segment is described in rotated coordinates:
u = x + y says which anti-diagonal it lies on, and v = y - x says where it
sits along that line. Consecutive cells on a segment differ by 2 in v, so a
segment is a triple (u, v_start, v_end). Take every pair of segments on
different lines whose v-spans overlap. Paint colour 2 on each background
cell strictly between their two lines (by u) and inside the shared v-span.
A band is filled even when another segment lies between the two outer
lines. Segment cells keep their colour.

Scope: all original examples are 16x16, and half of the random scenes use
that size. The other half are synthetic extensions with each side drawn
from 12..22. Callers may pass any size from 6 to 30. A scene has 2..5
segments, or 2..6 on larger grids. Each segment is 2 or more cells long, up
to two thirds of the shorter side. All segments share one colour, which is
never 2 or 8. Most segments are placed to overlap an earlier segment's
v-span, which gives nested and merged bands. Some lie on the same diagonal
as an earlier segment with a visible gap. The rest are free and often act
as non-overlapping distractors. Segments never share or touch cells, even
diagonally. Overlapping segments on different lines are at least 3 lines
apart. Every random scene changes at least one cell.
For three or more segments on grids at least 12x12, the default mixture
includes crossing-band and collinear-notch cases. The mechanism argument
can require either decision explicitly. Endpoint-only overlap follows the
archived rule and is retained as a synthetic extension.
"""

import random

import common


BACKGROUND = 8
FILL = 2
COLORS = (1, 3, 4, 5, 6, 7, 9)


def _cells(seg):
  """Yields the (y, x) cells of a segment (u, v_start, v_end)."""
  u, a, b = seg
  for v in range(a, b + 1, 2):
    yield (u + v) // 2, (u - v) // 2


def _v_bounds(u, width, height):
  """Inclusive range of v = y - x for in-grid cells on the line x + y = u."""
  return max(u - 2 * (width - 1), -u), min(u, 2 * (height - 1) - u)


def _check_segments(width, height, segments):
  """Rejects explicit segments that are malformed, off-grid or touching."""
  owner = {}
  if not 2 <= len(segments) <= 8:
    raise ValueError('require 2..8 explicit segments')
  for idx, seg in enumerate(segments):
    u, a, b = seg
    if b - a < 2 or (a - u) % 2 or (b - u) % 2:
      raise ValueError('segment %r has a bad span or parity' % (seg,))
    vmin, vmax = _v_bounds(u, width, height)
    if a < vmin or b > vmax:
      raise ValueError('segment %r leaves the grid' % (seg,))
    for cell in _cells(seg):
      if cell in owner:
        raise ValueError('segments overlap at %r' % (cell,))
      owner[cell] = idx
  for (y, x), idx in owner.items():
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        other = owner.get((y + dy, x + dx))
        if other is not None and other != idx:
          raise ValueError('segments %d and %d touch' % (idx, other))


def _spaced(seg, others):
  """Stricter spacing used by the random sampler."""
  u, a, b = seg
  for (u2, a2, b2) in others:
    du = abs(u - u2)
    dist = max(a2 - b, a - b2, 0)
    if du == 0 and dist < 6:
      return False
    if 0 < du <= 2 and dist < 4:
      return False
  return True


def _fill_cells(width, height, segments):
  """Cells painted 2: every overlapping pair's band, minus segment cells."""
  seg_cells = set()
  for seg in segments:
    seg_cells.update(_cells(seg))
  fill = set()
  for i, s1 in enumerate(segments):
    for s2 in segments[i + 1:]:
      if s1[0] == s2[0]:
        continue
      lo, hi = max(s1[1], s2[1]), min(s1[2], s2[2])
      if lo > hi:
        continue
      u_lo, u_hi = min(s1[0], s2[0]), max(s1[0], s2[0])
      for u in range(u_lo + 1, u_hi):
        for v in range(lo + (lo - u) % 2, hi + 1, 2):
          y, x = (u + v) // 2, (u - v) // 2
          if 0 <= y < height and 0 <= x < width and (y, x) not in seg_cells:
            fill.add((y, x))
  return fill


def _render(width, height, color, segments):
  grid = common.grid(width, height, BACKGROUND)
  for seg in segments:
    for y, x in _cells(seg):
      grid[y][x] = color
  out = [row[:] for row in grid]
  for y, x in _fill_cells(width, height, segments):
    out[y][x] = FILL
  return grid, out


def _mechanism_ok(width, height, segs, mechanism):
  if mechanism == 'any':
    return True
  fill = _fill_cells(width, height, segs)
  ink = {p for seg in segs for p in _cells(seg)}
  if mechanism == 'crossing':
    lines = sorted({s[0] for s in segs})
    neighbour_pairs = set(zip(lines, lines[1:]))
    adjacent = set()
    for i, a in enumerate(segs):
      for b in segs[i + 1:]:
        if tuple(sorted((a[0], b[0]))) in neighbour_pairs:
          adjacent |= _fill_cells(width, height, [a, b])
    return fill != adjacent - ink
  merged = {}
  for u, a, b in segs:
    if u not in merged:
      merged[u] = [a, b]
    else:
      merged[u] = [min(a, merged[u][0]), max(b, merged[u][1])]
  joined = [(u, a, b) for u, (a, b) in merged.items()]
  # Compare on cells that are background in both inputs, so merely filling
  # a missing piece of segment does not count as a band-notch decision.
  merged_ink = {p for seg in joined for p in _cells(seg)}
  return fill - merged_ink != _fill_cells(width, height, joined) - ink


def _notch_seed(width, height, cap):
  """Two separated collinear spans and a partner spanning their gap."""
  if cap < 6:
    return None
  for _ in range(60):
    u = random.randint(1, width + height - 3)
    lo, hi = _v_bounds(u, width, height)
    length_max = min(cap, (hi - lo) // 2 + 1)
    if length_max < 6:
      continue
    span = 2 * (random.randint(6, length_max) - 1)
    start = lo + 2 * random.randint(0, (hi - lo - span) // 2)
    end = start + span
    gap = random.randrange(6, span - 3, 2)
    first_end = start + 2 * random.randint(1, (span - gap - 2) // 2)
    second_start = first_end + gap
    partners = [v for v in range(u % 2, width + height - 1, 2)
                if abs(v - u) >= 4 and _v_bounds(v, width, height)[0] <= start
                and _v_bounds(v, width, height)[1] >= end]
    if partners:
      return [(u, start, first_end), (u, second_start, end),
              (random.choice(partners), start, end)]
  return None


def _sample_segments(width, height, n, mechanism):
  """Builds n well-spaced segments with at least one non-empty band."""
  cap = max(2, (2 * min(width, height)) // 3)
  for _ in range(300):
    segs = _notch_seed(width, height, cap) if mechanism == 'notch' else []
    if segs is None:
      continue
    for _ in range(n - len(segs)):
      placed = False
      for _ in range(80):
        r = random.random()
        ref = random.choice(segs) if segs else None
        if ref is not None and 0.6 <= r < 0.75:
          u = ref[0]  # Same diagonal as an earlier segment, with a gap.
        else:
          u = random.randint(1, width + height - 3)
        vmin, vmax = _v_bounds(u, width, height)
        maxlen = (vmax - vmin) // 2 + 1
        if maxlen < 2:
          continue
        length = random.randint(2, min(cap, maxlen))
        span = 2 * (length - 1)
        lo, hi = vmin, vmax - span
        if ref is not None and r < 0.6:
          # Force the v-span to overlap the reference segment's span.
          lo = max(lo, ref[1] - span)
          hi = min(hi, ref[2])
          lo += (lo - u) % 2
        if lo > hi:
          continue
        start = lo + 2 * random.randint(0, (hi - lo) // 2)
        seg = (u, start, start + span)
        if _spaced(seg, segs):
          segs.append(seg)
          placed = True
          break
      if not placed:
        break
    if len(segs) != n:
      continue
    if not _fill_cells(width, height, segs):
      continue
    if not _mechanism_ok(width, height, segs, mechanism):
      continue
    return segs
  raise ValueError('bounded placement exhausted for %d segments, %s, on %dx%d'
                   % (n, mechanism, width, height))


def generate(width=None, height=None, color=None, num_segments=None,
             segments=None, mechanism=None):
  """Generates one input/output pair.

  Args:
    width: grid width, 6..30. If width and height are both None, the size is
      16x16 half the time and otherwise each side is drawn from 12..22. A
      missing side is drawn from 12..22. With explicit segments, the default
      is 16.
    height: grid height, 6..30. Same defaults as width.
    color: segment colour, 0..9 but not 2 or 8. Random from 1,3,4,5,6,7,9 if
      None.
    num_segments: number of random segments, 2..8. The default is 2..5, or
      2..6 when width*height >= 300. If segments is also given, it must equal
      len(segments).
    segments: optional list of (u, v_start, v_end) triples with u = x + y and
      v = y - x. The v_start and v_end values must have the same parity as u.
      The segments must be in the grid and must not share or touch cells.
      If None, a random valid scene is constructed.
    mechanism: 'any', 'crossing' (all-pairs differs from adjacent-line
      filling), or 'notch' (merging collinear spans would change the fill).
      None samples a mixture when the size and count allow it.
      Dense small-grid requests can exhaust bounded placement and raise
      ValueError; counts are never silently reduced.
  """
  for name, value in (('width', width), ('height', height), ('color', color),
                      ('num_segments', num_segments)):
    if value is not None and type(value) is not int:
      raise ValueError(name + ' must be an integer')
  if mechanism not in (None, 'any', 'crossing', 'notch'):
    raise ValueError('unknown mechanism')
  if segments is not None:
    parsed = []
    for s in segments:
      if len(s) != 3:
        raise ValueError('segment %r is not a (u, v_start, v_end) triple'
                         % (s,))
      if any(type(t) is not int for t in s):
        raise ValueError('segment coordinates must be integers')
      parsed.append(tuple(s))
    segments = parsed
    if num_segments is not None and num_segments != len(segments):
      raise ValueError('num_segments disagrees with len(segments)')
    if width is None:
      width = 16
    if height is None:
      height = 16
  else:
    if width is None and height is None:
      if random.random() < 0.5:
        width, height = 16, 16
      else:
        width, height = random.randint(12, 22), random.randint(12, 22)
    if width is None:
      width = random.randint(12, 22)
    if height is None:
      height = random.randint(12, 22)
  if not (6 <= width <= 30 and 6 <= height <= 30):
    raise ValueError('grid sides must be within 6..30')
  if color is None:
    color = random.choice(COLORS)
  elif color not in range(10) or color in (BACKGROUND, FILL):
    raise ValueError('segment colour must be 0..9 and not 2 or 8')
  if segments is None:
    if num_segments is None:
      num_segments = random.randint(2, 6 if width * height >= 300 else 5)
    if not 2 <= num_segments <= 8:
      raise ValueError('num_segments must be within 2..8')
    if mechanism is None:
      mechanism = (random.choice(['any', 'any', 'crossing', 'notch'])
                   if num_segments >= 3 and min(width, height) >= 12 else 'any')
    if mechanism != 'any' and num_segments < 3:
      raise ValueError('crossing/notch mechanisms require at least three segments')
    segments = _sample_segments(width, height, num_segments, mechanism)
  else:
    _check_segments(width, height, segments)
    if not _fill_cells(width, height, segments):
      raise ValueError('explicit scene has no nonempty band')
    if mechanism is not None and not _mechanism_ok(width, height, segments, mechanism):
      raise ValueError('explicit scene does not demonstrate requested mechanism')
  grid, out = _render(width, height, color, segments)
  return {'input': grid, 'output': out}


def validate():
  """Reconstructs the original fixtures from explicit latent segments."""
  train = [
      generate(width=16, height=16, color=4,
               segments=[(8, -8, -6), (12, -12, -6), (16, -14, -8),
                         (12, 4, 8), (17, 1, 11), (23, -5, 7)]),
      generate(width=16, height=16, color=3,
               segments=[(6, -2, 6), (11, -11, -1), (15, -3, 13),
                         (23, -7, 7)]),
  ]
  test = [
      generate(width=16, height=16, color=9,
               segments=[(8, 0, 2), (13, -5, 5), (18, -8, 8),
                         (22, -8, 8)]),
  ]
  return {'train': train, 'test': test}
