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

"""ARC-GEN style generator for task 54dc2872.

Rule: the grid holds several L-shaped bodies. Each body has one marker cell
of another colour tucked diagonally into its bend. Lone pixels are scattered
elsewhere in the grid. If a lone pixel has the same colour as a shape's
marker, that shape is translated without rotation. It moves so that its
L-corner, the cell where the two arms meet, lands on that pixel, and the
moved shape covers the pixel. Shapes with no matching lone pixel stay where
they are. Lone pixels that match no marker are left unchanged.

Scope: the background is black (0).
- Grid size. Random grids are 10 to 30 cells per side by default. Explicit
  width and height may be anywhere from 5 to 30. The fixtures are 12x12 and
  12x13, so larger grids are a synthetic extension.
- Shapes. A scene has 2 to 5 shapes by default, or 1 to 6 when requested.
  Arm lengths are 2 to 5, and all four L orientations occur.
- Moving shapes. By default 1 to 3 shapes move, and at least one shape always
  stays put.
- Distractors. There are 0 to 2 lone pixels by default, or 0 to 4 when
  requested. Their colours never equal any marker.
- Colours. Markers are distinct across shapes, and so are bodies. A body
  colour may equal another shape's marker colour, as it does in the test
  fixture.
- Spacing. All input objects are separated by at least one empty cell,
  diagonals included. Moved shapes stay fully in bounds. In the output they
  never touch stationary shapes, distractors or other moved shapes. They may
  overlap their own old, erased positions or those of other moved shapes.
"""

import copy
import random

import common

_MAX_SHAPES = 6


def _footprint(r, c, dy, dx, hl, vl):
  r0, r1 = sorted((r, r + dy * (vl - 1)))
  c0, c1 = sorted((c, c + dx * (hl - 1)))
  return [(y, x) for y in range(r0, r1 + 1) for x in range(c0, c1 + 1)]


def _cells(r, c, dy, dx, hl, vl, body, marker):
  cells = {}
  for i in range(hl):
    cells[(r, c + dx * i)] = body
  for i in range(vl):
    cells[(r + dy * i, c)] = body
  cells[(r + dy, c + dx)] = marker
  return cells


def _inside(cells, height, width):
  return all(0 <= y < height and 0 <= x < width for y, x in cells)


def _clear(cells, occ):
  for y, x in cells:
    for a in (-1, 0, 1):
      for b in (-1, 0, 1):
        if (y + a, x + b) in occ:
          return False
  return True


def _corner_range(size, d, length):
  if d > 0:
    return 0, size - length
  return length - 1, size - 1


def _check_count(name, value, lo, hi):
  if value is None:
    return
  if not isinstance(value, int) or not lo <= value <= hi:
    raise ValueError('%s must be an integer in [%d, %d]' % (name, lo, hi))


def _random_scene(width, height, num_shapes, num_moving, num_distractors):
  for _ in range(300):
    h = height if height is not None else random.randint(10, 30)
    w = width if width is not None else random.randint(10, 30)
    if num_shapes is not None:
      n = num_shapes
    else:
      lo = 2
      if num_moving is not None:
        lo = min(_MAX_SHAPES, max(2, num_moving + 1))
      n = random.randint(lo, max(lo, 5))
    if num_moving is not None:
      nmove = num_moving
    else:
      nmove = random.randint(1, max(1, min(3, n - 1)))
    if num_distractors is not None:
      nd = num_distractors
    else:
      nd = random.randint(0, 2)
    markers = random.sample(range(1, 10), n)
    bodies = []
    for m in markers:
      opts = [c for c in range(1, 10) if c != m and c not in bodies]
      bodies.append(random.choice(opts))
    shapes = []
    occ_in = set()
    for i in range(n):
      for _ in range(60):
        dy = random.choice((-1, 1))
        dx = random.choice((-1, 1))
        hl = random.randint(2, 5)
        vl = random.randint(2, 5)
        r0, r1 = _corner_range(h, dy, vl)
        c0, c1 = _corner_range(w, dx, hl)
        if r0 > r1 or c0 > c1:
          continue
        r = random.randint(r0, r1)
        c = random.randint(c0, c1)
        fp = _footprint(r, c, dy, dx, hl, vl)
        if not _clear(fp, occ_in):
          continue
        occ_in.update(fp)
        shapes.append([r, c, dy, dx, hl, vl, bodies[i], markers[i], None])
        break
    if len(shapes) < n:
      continue
    occ_out = set()
    for s in shapes[nmove:]:
      occ_out.update(_footprint(*s[:6]))
    moved = 0
    for s in shapes[:nmove]:
      r0, r1 = _corner_range(h, s[2], s[5])
      c0, c1 = _corner_range(w, s[3], s[4])
      for _ in range(100):
        ty = random.randint(r0, r1)
        tx = random.randint(c0, c1)
        fp = _footprint(ty, tx, s[2], s[3], s[4], s[5])
        if not _clear([(ty, tx)], occ_in) or not _clear(fp, occ_out):
          continue
        occ_in.add((ty, tx))
        occ_out.update(fp)
        s[8] = (ty, tx)
        moved += 1
        break
      else:
        break
    if moved < nmove:
      continue
    free = [c for c in range(1, 10) if c not in markers]
    singles = []
    for _ in range(nd):
      for _ in range(100):
        y = random.randrange(h)
        x = random.randrange(w)
        if _clear([(y, x)], occ_in) and _clear([(y, x)], occ_out):
          occ_in.add((y, x))
          occ_out.add((y, x))
          singles.append((y, x, random.choice(free)))
          break
    if len(singles) < nd:
      continue
    random.shuffle(shapes)
    return w, h, [tuple(s) for s in shapes], singles
  raise ValueError('could not construct a scene for the requested parameters')


def _check_explicit(width, height, shapes, singles):
  if width is None or height is None:
    raise ValueError('width and height are required with explicit shapes')
  if not shapes:
    raise ValueError("need at least one L shape")
  for s in shapes:
    if len(s) != 9:
      raise ValueError('each shape needs 9 fields')
    r, c, dy, dx, hl, vl, body, marker, target = s
    if dy not in (-1, 1) or dx not in (-1, 1) or hl < 2 or vl < 2:
      raise ValueError('invalid L geometry')
    if body == marker or body not in range(1,10) or marker not in range(1,10):
      raise ValueError("body and marker must be distinct nonzero colours")
    cells = list(_cells(*s[:8]))
    if target is not None:
      cells += list(_cells(target[0], target[1], dy, dx, hl, vl, body,
                           marker))
    if not _inside(cells, height, width):
      raise ValueError('shape out of bounds')
  for y, x, colour in singles:
    if colour not in range(1,10) or colour in {s[7] for s in shapes}:
      raise ValueError("distractor colour must be nonzero and match no marker")
    if not _inside([(y, x)], height, width):
      raise ValueError('single out of bounds')


  if len({s[7] for s in shapes}) != len(shapes):
    raise ValueError("marker colours must be distinct")
  groups=[set(_cells(*s[:8])) for s in shapes]
  groups += [{tuple(s[8])} for s in shapes if s[8] is not None]
  groups += [{(y,x)} for y,x,_ in singles]
  occupied=set()
  for cells in groups:
    halo=cells | {(y+dy,x+dx) for y,x in cells for dy,dx in ((1,0),(-1,0),(0,1),(0,-1))}
    if halo & occupied:
      raise ValueError("input objects overlap or touch orthogonally")
    occupied |= cells


def generate(width=None, height=None, shapes=None, singles=None,
             num_shapes=None, num_moving=None, num_distractors=None):
  """Build one input/output pair.

  Args:
    width: grid width, from 5 to 30. In random mode it fixes the sampled
      width. With explicit shapes it is required.
    height: grid height, from 5 to 30. It behaves like width.
    shapes: optional list of tuples
      (r, c, dy, dx, hlen, vlen, body, marker, target).
      (r, c) is the L-corner. The horizontal arm runs hlen cells in column
      direction dx, and the vertical arm runs vlen cells in row direction dy.
      The marker sits at (r+dy, c+dx). target is the (row, col) of the
      matching lone pixel, or None if the shape stays.
    singles: list of (row, col, colour) distractor lone pixels whose colours
      match no marker. It is only allowed together with explicit shapes.
    num_shapes: random mode only. Number of L shapes, from 1 to 6.
    num_moving: random mode only. Number of shapes that move, from 1 up to
      num_shapes.
    num_distractors: random mode only. Number of non-matching lone pixels,
      from 0 to 4.
  """
  _check_count('width', width, 5, 30)
  _check_count('height', height, 5, 30)
  if shapes is None:
    if singles is not None:
      raise ValueError('singles may only be given with explicit shapes')
    _check_count('num_shapes', num_shapes, 1, _MAX_SHAPES)
    _check_count('num_moving', num_moving, 1, _MAX_SHAPES)
    _check_count('num_distractors', num_distractors, 0, 4)
    if (num_shapes is not None and num_moving is not None and
        num_moving > num_shapes):
      raise ValueError('num_moving cannot exceed num_shapes')
    width, height, shapes, singles = _random_scene(
        width, height, num_shapes, num_moving, num_distractors)
  else:
    if (num_shapes is not None or num_moving is not None or
        num_distractors is not None):
      raise ValueError('count controls are incompatible with explicit shapes')
    singles = singles or []
    _check_explicit(width, height, shapes, singles)
  grid = common.grid(width, height, 0)
  for s in shapes:
    for (y, x), v in _cells(*s[:8]).items():
      grid[y][x] = v
    if s[8] is not None:
      grid[s[8][0]][s[8][1]] = s[7]
  for y, x, colour in singles:
    grid[y][x] = colour
  output = copy.deepcopy(grid)
  moving = [s for s in shapes if s[8] is not None]
  for s in moving:
    for (y, x) in _cells(*s[:8]):
      output[y][x] = 0
    output[s[8][0]][s[8][1]] = 0
  for s in moving:
    ty, tx = s[8]
    for (y, x), v in _cells(ty, tx, *s[2:8]).items():
      output[y][x] = v
  return {'input': grid, 'output': output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=13, height=12, shapes=[
          (0, 3, 1, -1, 3, 3, 7, 1, None),
          (4, 3, 1, -1, 3, 3, 4, 5, None),
          (9, 3, 1, -1, 4, 3, 3, 8, (1, 11)),
          (6, 9, 1, 1, 2, 3, 9, 6, (5, 8)),
      ], singles=[(1, 6, 2)]),
      generate(width=12, height=12, shapes=[
          (5, 6, 1, 1, 3, 3, 6, 7, (1, 2)),
          (8, 3, 1, -1, 3, 3, 8, 9, None),
      ], singles=[]),
  ]
  test = [
      generate(width=13, height=12, shapes=[
          (2, 4, -1, 1, 3, 3, 3, 5, (6, 0)),
          (6, 6, -1, 1, 4, 3, 7, 3, None),
          (9, 10, -1, 1, 3, 2, 8, 6, (11, 8)),
      ], singles=[(8, 4, 9)]),
  ]
  return {'train': train, 'test': test}
