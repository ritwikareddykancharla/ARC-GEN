# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task b99e7126.

Rule: the grid is a lattice of 3x3 tiles separated by 1-cell divider lines.
The outer border also uses the divider colour. Most tiles repeat one
'normal' pattern. A few tiles carry one identical 'special' pattern, which
adds exactly one colour that the normal tile lacks. The cells of that new
colour form a 3x3 shape mask. The existing special tiles are some of the
cells of the same mask drawn at lattice scale, with one tile per mask cell.
Exactly one translation of the mask covers all of them. The output stamps
the special tile on every remaining mask cell at that offset. This completes
the enlarged copy of the shape.

Uniqueness is enforced against every translation of the mask, including
translations that would run partly off the lattice. The lattice edge is
never the only thing that disambiguates the placement. All four original
examples satisfy this stronger condition.

Scope: tiles are always 3x3 with 1-cell dividers. Every original example
uses a 7x7 lattice, which gives a 29x29 grid. When neither rows nor cols is
given, a fair coin selects (7, 7); otherwise both sides are uniform over
their feasible ranges (so the overall (7, 7) probability exceeds 1/2).
With one side fixed, the free side has a separate half-probability bias
toward 7, otherwise it is uniform over its feasible range. The minimum is
4, increased to offset+3 when a fixed offset requires it. Smaller and rectangular
lattices (17..29 cells per side) are synthetic extensions. Lattices larger
than 7 tiles exceed the 30-cell limit. Fewer than 4 tiles per side is
rejected because a 3-tile side admits only one placement.

Sampled latent variables:
- the lattice size;
- the divider colour;
- a normal tile with 2 (usually) or 3 colours, often mirror-symmetric;
- one new colour;
- a random 8-connected mask of 3..8 cells (mostly 4..7) that fills its
  3x3 box;
- the non-mask cells of the special tile: a uniform fill, a copy of the
  normal tile, or random normal colours;
- the lattice offset;
- a proper subset of mask cells (at least 2) shown in the input. It is
  chosen from all subsets that fix the translation uniquely.
The answer is built from these latent values. The input is never solved.
"""

import itertools
import random

import common


_T = 3  # tile size (fixed by the task)
_MIN_N = 4  # minimum tiles per side; 3 would leave a single placement
_MAX_N = 7  # 7 * (3 + 1) + 1 = 29 <= 30
_MASK_SIZES = [3, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 8]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _colors(tile):
  return {v for row in tile for v in row}


def _check_tile(tile, name):
  if (not isinstance(tile, (list, tuple)) or len(tile) != _T
      or any(not isinstance(row, (list, tuple)) or len(row) != _T
             for row in tile)):
    raise ValueError(name + ' must be a 3x3 tile')
  for row in tile:
    for v in row:
      if not _is_int(v) or not 0 <= v <= 9:
        raise ValueError(name + ' contains an invalid colour')
  return [list(row) for row in tile]


def _mask_cells(normal, special):
  cols = _colors(normal)
  return sorted((i, j) for i in range(_T) for j in range(_T)
                if special[i][j] not in cols)


def _full_bbox(cells):
  return ({i for i, _ in cells} == set(range(_T))
          and {j for _, j in cells} == set(range(_T)))


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    i, j = stack.pop()
    for di in (-1, 0, 1):
      for dj in (-1, 0, 1):
        nb = (i + di, j + dj)
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
  return seen == cells


def _mask_ok(cells):
  """Masks: 3..8 cells, 8-connected, filling the 3x3 box."""
  return 3 <= len(cells) <= 8 and _full_bbox(cells) and _connected(cells)


def _grow_mask(k):
  """Random 8-connected k-cell mask that fills the 3x3 box, or None."""
  if k == 3:
    # Only the two diagonals are connected permutations spanning all rows/cols.
    return [(i, i) for i in range(_T)] if random.random() < 0.5 else [
        (i, _T - 1 - i) for i in range(_T)]
  cells = [(i, j) for i in range(_T) for j in range(_T)]
  for _ in range(200):
    chosen = {random.choice(cells)}
    while len(chosen) < k:
      frontier = sorted({(i + di, j + dj) for i, j in chosen
                         for di in (-1, 0, 1) for dj in (-1, 0, 1)
                         if 0 <= i + di < _T and 0 <= j + dj < _T} - chosen)
      chosen.add(random.choice(frontier))
    if _full_bbox(chosen):
      return sorted(chosen)
  return None


def _unique_shift(mask, shown):
  """True iff no nonzero translation of the mask also covers `shown`.

  Shown cells are relative to the mask, so this test is independent of the
  lattice size and also excludes translations that run off the lattice.
  """
  mset = set(mask)
  for dy in range(-(_T - 1), _T):
    for dx in range(-(_T - 1), _T):
      if dy == 0 and dx == 0:
        continue
      if all((i + dy, j + dx) in mset for i, j in shown):
        return False
  return True


def _unique_subsets(mask):
  """Proper subsets (size >= 2) that fix the translation, keyed by size."""
  by_size = {}
  for size in range(2, len(mask)):
    good = [sorted(s) for s in itertools.combinations(mask, size)
            if _unique_shift(mask, s)]
    if good:
      by_size[size] = good
  return by_size


def _choose_shown(pool):
  size = random.choice(sorted(pool))
  return list(random.choice(pool[size]))


def _random_tile(colors):
  """Random 3x3 tile that uses every colour in `colors`, often symmetric."""
  for _ in range(50):
    tile = [[random.choice(colors) for _ in range(_T)] for _ in range(_T)]
    if random.random() < 0.5:
      for row in tile:
        row[2] = row[0]
    if random.random() < 0.5:
      tile[2] = list(tile[0])
    if _colors(tile) == set(colors):
      return tile
  cells = [(i, j) for i in range(_T) for j in range(_T)]
  random.shuffle(cells)
  tile = [[random.choice(colors) for _ in range(_T)] for _ in range(_T)]
  for (i, j), col in zip(cells, colors):
    tile[i][j] = col
  return tile


def _special_tile(normal, mask, new):
  """Mask cells get `new`; other cells come from the normal colours."""
  normal_colors = sorted(_colors(normal))
  mode = random.randint(0, 2)
  fill = random.choice(normal_colors)
  tile = []
  for i in range(_T):
    row = []
    for j in range(_T):
      if (i, j) in mask:
        row.append(new)
      elif mode == 0:
        row.append(fill)
      elif mode == 1:
        row.append(normal[i][j])
      else:
        row.append(random.choice(normal_colors))
    tile.append(row)
  return tile


def _sample_side(lo):
  if random.random() < 0.5:
    return _MAX_N
  return random.randint(lo, _MAX_N)


def _sample_dims(rows, cols, offset):
  lo_r = _MIN_N if offset is None else max(_MIN_N, offset[0] + _T)
  lo_c = _MIN_N if offset is None else max(_MIN_N, offset[1] + _T)
  if rows is None and cols is None:
    if random.random() < 0.5:
      return _MAX_N, _MAX_N
    return random.randint(lo_r, _MAX_N), random.randint(lo_c, _MAX_N)
  nr = rows if rows is not None else _sample_side(lo_r)
  nc = cols if cols is not None else _sample_side(lo_c)
  return nr, nc


def _stamp(grid, r, c, tile):
  for i in range(_T):
    for j in range(_T):
      grid[r * (_T + 1) + 1 + i][c * (_T + 1) + 1 + j] = tile[i][j]


def generate(divider=None, normal=None, special=None, offset=None,
             shown=None, rows=None, cols=None):
  """Returns an input/output pair.

  Any argument left as None is sampled. Values that are given are honoured
  and validated. Booleans and non-integers are rejected, never coerced.

  Args:
    divider: colour of the lattice lines and border. It must not appear in
      either tile.
    normal: 3x3 normal tile.
    special: 3x3 special tile. It must add exactly one colour absent from
      normal. The cells of that colour form the shape mask, which must have
      3..8 cells, be 8-connected and touch every row and column of the tile.
      Requires normal.
    offset: (tile_row, tile_col) of the mask's top-left corner on the lattice.
    shown: mask cells (i, j), relative to the mask, that already hold the
      special tile in the input. Requires special. It must have at least 2
      cells, must not be the whole mask, and no other translation of the
      mask (even partly off-lattice) may cover it.
    rows: number of tile rows, 4..7 (all original examples use 7).
    cols: number of tile columns, 4..7 (all original examples use 7).

  Raises:
    ValueError: the given parameters are inconsistent or cannot be completed
      into a valid, unambiguous, non-identity scene.
  """
  if special is not None and normal is None:
    raise ValueError('special requires normal')
  if shown is not None and special is None:
    raise ValueError('shown requires special and normal')
  for name, val in (('rows', rows), ('cols', cols)):
    if val is not None and (not _is_int(val) or not _MIN_N <= val <= _MAX_N):
      raise ValueError(name + ' must be an int in 4..7')
  if divider is not None and (not _is_int(divider) or not 0 <= divider <= 9):
    raise ValueError('divider must be a colour 0..9')
  if normal is not None:
    normal = _check_tile(normal, 'normal')
  mask_given = None
  if special is not None:
    special = _check_tile(special, 'special')
    if len(_colors(special) - _colors(normal)) != 1:
      raise ValueError('special must add exactly one colour absent from normal')
    mask_given = _mask_cells(normal, special)
    if not _mask_ok(mask_given):
      raise ValueError('special mask must have 3..8 cells, be 8-connected '
                       'and fill its 3x3 box')
  given = set()
  if normal is not None:
    given |= _colors(normal)
  if special is not None:
    given |= _colors(special)
  if divider is not None and divider in given:
    raise ValueError('divider colour collides with a tile colour')
  if offset is not None:
    if (not isinstance(offset, (list, tuple)) or len(offset) != 2
        or not all(_is_int(v) for v in offset)):
      raise ValueError('offset must be a (tile_row, tile_col) pair of ints')
    offset = (offset[0], offset[1])
    if not (0 <= offset[0] <= _MAX_N - _T and 0 <= offset[1] <= _MAX_N - _T):
      raise ValueError('offset out of range')
    if rows is not None and offset[0] > rows - _T:
      raise ValueError('offset row does not fit in rows')
    if cols is not None and offset[1] > cols - _T:
      raise ValueError('offset column does not fit in cols')
  shown_pool = None
  if special is not None:
    if shown is not None:
      if not isinstance(shown, (list, tuple)):
        raise ValueError('shown must be a list of (i, j) pairs')
      cells = set()
      for cell in shown:
        if (not isinstance(cell, (list, tuple)) or len(cell) != 2
            or not all(_is_int(v) for v in cell)):
          raise ValueError('shown must be a list of (i, j) int pairs')
        cells.add((cell[0], cell[1]))
      shown = sorted(cells)
      if not set(shown) <= set(mask_given):
        raise ValueError('shown must be a subset of the mask')
      if not 2 <= len(shown) < len(mask_given):
        raise ValueError('shown must have at least 2 cells and fewer than the '
                         'whole mask')
      if not _unique_shift(mask_given, shown):
        raise ValueError('shown cells do not determine the offset uniquely')
    else:
      shown_pool = _unique_subsets(mask_given)
      if not shown_pool:
        raise ValueError('no shown subset fixes the offset uniquely')

  for _ in range(100):
    nr, nc = _sample_dims(rows, cols, offset)
    if offset is not None:
      oy, ox = offset
    else:
      oy, ox = random.randint(0, nr - _T), random.randint(0, nc - _T)
    dv = divider
    if dv is None:
      free = [v for v in range(10) if v not in given]
      if not free:
        raise ValueError('no colour left for the divider')
      dv = random.choice(free)
    nm = normal
    if nm is None:
      ncol = 3 if random.random() < 0.25 else 2
      nm = _random_tile(random.sample([v for v in range(10) if v != dv],
                                      ncol))
    if special is None:
      free = [v for v in range(10) if v != dv and v not in _colors(nm)]
      if not free:
        raise ValueError('no colour left for the special shape')
      cells = _grow_mask(random.choice(_MASK_SIZES))
      if cells is None:
        continue
      sp = _special_tile(nm, cells, random.choice(free))
      mask = _mask_cells(nm, sp)
      pool = _unique_subsets(mask)
      if not pool:
        continue
    else:
      sp = special
      mask = mask_given
      pool = shown_pool
    sh = shown if shown is not None else _choose_shown(pool)
    if nr * nc - len(sh) <= len(sh):
      continue  # unreachable for 4..7 lattices; kept as a safety invariant

    grid = common.grid(nc * (_T + 1) + 1, nr * (_T + 1) + 1, dv)
    for r in range(nr):
      for c in range(nc):
        _stamp(grid, r, c, nm)
    for i, j in sh:
      _stamp(grid, oy + i, ox + j, sp)
    output = [list(row) for row in grid]
    for i, j in mask:
      _stamp(output, oy + i, ox + j, sp)
    return {'input': grid, 'output': output}
  raise ValueError('could not construct a valid scene from the given parameters')


def validate():
  """Reconstructs the canonical fixtures through explicit parameters."""
  train = [
      generate(divider=2, normal=[[4, 4, 4], [4, 1, 4], [4, 4, 4]],
               special=[[3, 1, 3], [3, 1, 3], [3, 3, 3]], offset=(1, 2),
               shown=[(2, 0), (2, 1), (2, 2)], rows=7, cols=7),
      generate(divider=2, normal=[[8, 8, 8], [3, 8, 3], [8, 8, 8]],
               special=[[1, 8, 1], [1, 1, 1], [1, 8, 1]], offset=(1, 1),
               shown=[(1, 0), (1, 1), (1, 2)], rows=7, cols=7),
      generate(divider=1, normal=[[4, 2, 4], [2, 4, 2], [4, 2, 4]],
               special=[[4, 8, 4], [8, 8, 8], [8, 4, 8]], offset=(2, 1),
               shown=[(1, 0), (1, 1), (1, 2), (2, 0)], rows=7, cols=7),
  ]
  test = [
      generate(divider=8, normal=[[9, 2, 9], [2, 2, 2], [9, 9, 9]],
               special=[[9, 4, 9], [4, 9, 4], [4, 4, 4]], offset=(3, 1),
               shown=[(0, 1), (1, 0), (1, 2)], rows=7, cols=7),
  ]
  return {'train': train, 'test': test}
