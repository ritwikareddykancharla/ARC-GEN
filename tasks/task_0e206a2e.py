# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Generator.'''

import common

# The eight planar symmetries as (a, b, c, d): (y, x) -> (a*y + b*x, c*y + d*x).
_MATS = ((1, 0, 0, 1), (1, 0, 0, -1), (-1, 0, 0, 1), (-1, 0, 0, -1),
         (0, 1, 1, 0), (0, 1, -1, 0), (0, -1, 1, 0), (0, -1, -1, 0))
_MAX_SCENES = 400
_MAX_PLACEMENTS = 200
_MAX_MARKER_PICKS = 200


def _around(y, x):
  for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
      if dy or dx:
        yield y + dy, x + dx


def _render(width, height, rows, cols, idxs, colors, brows, bcols, rotates):
  '''Draws input and output grids for fully specified parameters.'''
  num_sprites, mode = max(idxs) + 1, max(set(colors), key=colors.count)
  grid, output = common.grids(width, height)
  for row, col, i, color in zip(rows, cols, idxs, colors):
    r, c = row, col
    brow, bcol = brows[i], bcols[i]
    grid[brow + r][bcol + c] = color
    brow, bcol, rot = brows[num_sprites + i], bcols[num_sprites + i], rotates[i]
    wide = max([c for c, idx in zip(cols, idxs) if idx == i]) + 1
    tall = max([r for r, idx in zip(rows, idxs) if idx == i]) + 1
    if rot == 1: r, c = wide - c - 1, r
    if rot == 2: r, c = c, tall - r - 1
    if rot == 3: r = tall - r - 1
    if rot == 4: r, c = c, r
    output[brow + r][bcol + c] = color
    if color == mode: continue  # For the clone, we hide the common color.
    grid[brow + r][bcol + c] = color
  return {'input': grid, 'output': output}


def _sample(num_sprites):
  '''One bounded attempt at random scene parameters (None on failure).'''
  placed = False
  for _ in range(_MAX_PLACEMENTS):
    width, height = common.randint(12, 24), common.randint(12, 24)
    wides, talls, lengths, rotates, brows, bcols = [], [], [], [], [], []
    for _ in range(num_sprites):
      wides.append(common.randint(3, 6))
      talls.append(9 - wides[-1])
      lengths.append(max(wides[-1], talls[-1]))
      rotates.append(common.randint(1, 4))
    brows.extend([common.randint(0, height - length) for length in lengths])
    brows.extend([common.randint(0, height - length) for length in lengths])
    bcols.extend([common.randint(0, width - length) for length in lengths])
    bcols.extend([common.randint(0, width - length) for length in lengths])
    o = common.overlaps(brows, bcols, lengths + lengths, lengths + lengths, 3)
    if not o:
      placed = True
      break
  if not placed:
    return None
  color_list = common.random_colors(4)
  rows, cols, idxs, colors = [], [], [], []
  for idx in range(num_sprites):
    wide, tall = wides[idx], talls[idx]
    pixels = common.continuous_creature(common.randint(6, 12), wide, tall)
    sprite_colors = [color_list[3]] * len(pixels)
    pos = None
    for _ in range(_MAX_MARKER_PICKS):  # Pick positions that aren't all in a line
      cand = common.sample(range(len(pixels)), 3)
      if len(set(pixels[k][0] for k in cand)) == 1: continue
      if len(set(pixels[k][1] for k in cand)) == 1: continue
      pos = cand
      break
    if pos is None:
      return None
    sprite_colors[pos[0]] = color_list[0]
    sprite_colors[pos[1]] = color_list[1]
    sprite_colors[pos[2]] = color_list[2]
    rows.extend(p[0] for p in pixels)
    cols.extend(p[1] for p in pixels)
    idxs.extend([idx] * len(pixels))
    colors.extend(sprite_colors)
  return {'width': width, 'height': height, 'rows': rows, 'cols': cols,
          'idxs': idxs, 'colors': colors, 'brows': brows, 'bcols': bcols,
          'rotates': rotates}


def _unambiguous(example, params):
  '''True iff the visible input admits exactly one complete re-placement.

  Independent of any solver order: every shape is tried under all eight
  symmetries and every translation that puts all of its embedded markers on
  same-coloured loose markers; complete assignments with disjoint marker use
  are counted.
  '''
  grid = example['input']
  height, width = len(grid), len(grid[0])
  rows, cols, idxs, colors = params['rows'], params['cols'], params['idxs'], params['colors']
  brows, bcols = params['brows'], params['bcols']
  num_sprites = max(idxs) + 1
  tallies = sorted((colors.count(v) for v in set(colors)), reverse=True)
  if len(tallies) > 1 and tallies[0] == tallies[1]:
    return False
  mode = max(set(colors), key=colors.count)
  counts = {}
  for line in grid:
    for v in line:
      if v != 0:
        counts[v] = counts.get(v, 0) + 1
  ranked = sorted(counts.values(), reverse=True)
  if not ranked or (len(ranked) > 1 and ranked[0] == ranked[1]):
    return False
  if max(counts, key=counts.get) != mode:
    return False
  owner, sprites = {}, []
  for i in range(num_sprites):
    cells = {}
    for r, c, j, color in zip(rows, cols, idxs, colors):
      if j == i:
        cells[(brows[i] + r, bcols[i] + c)] = color
    for (y, x), color in cells.items():
      if not (0 <= y < height and 0 <= x < width) or grid[y][x] != color:
        return False
      if (y, x) in owner:
        return False
      owner[(y, x)] = i
    markers = [(y, x, color) for (y, x), color in sorted(cells.items()) if color != mode]
    if len(cells) < 2 or not markers or len(markers) == len(cells):
      return False
    start = next(iter(cells))
    seen, stack = {start}, [start]
    while stack:
      y, x = stack.pop()
      for ny, nx in _around(y, x):
        if (ny, nx) in cells and (ny, nx) not in seen:
          seen.add((ny, nx))
          stack.append((ny, nx))
    if len(seen) != len(cells):
      return False
    sprites.append((cells, markers))
  for (y, x), i in owner.items():
    for ny, nx in _around(y, x):
      if 0 <= ny < height and 0 <= nx < width and grid[ny][nx] != 0:
        if owner.get((ny, nx)) != i:
          return False
  targets = {}
  for y in range(height):
    for x in range(width):
      if grid[y][x] != 0 and (y, x) not in owner:
        if grid[y][x] == mode:
          return False
        targets[(y, x)] = grid[y][x]
  options = []
  for cells, markers in sprites:
    found = {}
    for a, b, c, d in _MATS:
      moved = [(a * y + b * x, c * y + d * x, col) for y, x, col in markers]
      ay, ax, acol = moved[0]
      for (ty, tx), col in targets.items():
        if col != acol:
          continue
        dy, dx = ty - ay, tx - ax
        used = [(y + dy, x + dx) for y, x, _ in moved]
        if all(targets.get(p) == m[2] for p, m in zip(used, moved)):
          stamp = frozenset((a * y + b * x + dy, c * y + d * x + dx, col2)
                            for (y, x), col2 in cells.items())
          found[stamp] = frozenset(used)
    options.append(list(found.items()))

  def count(i, used):
    if i == len(options):
      return 1
    total = 0
    for _, u in options[i]:
      if u & used:
        continue
      total += count(i + 1, used | u)
      if total > 1:
        return total
    return total

  return count(0, frozenset()) == 1


def generate(width=None, height=None, rows=None, cols=None, idxs=None,
             colors=None, brows=None, bcols=None, rotates=None):
  '''Returns input and output grids according to the given parameters.

  Args:
    width: the width of the (square) grid
    height: the height of the (square) grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    idxs: a list of indices into the sprite list
    colors: a list of digits representing the colors to be used
    brows: a list of vertical coordinates where the sprites should be placed
    bcols: a list of horizontal coordinates where the sprites should be placed
    rotates: a list of rotations for the sprites
  '''
  if width is not None:
    return _render(width, height, rows, cols, idxs, colors, brows, bcols,
                   rotates)
  num_sprites = common.randint(1, 2)
  for _ in range(_MAX_SCENES):
    params = _sample(num_sprites)
    if params is None:
      continue
    example = _render(**params)
    if _unambiguous(example, params):
      return example
  raise RuntimeError('could not sample an unambiguous scene')


def validate():
  '''Validates the generator.'''
  train = [
      generate(width=18, height=14,
               rows=[0, 1, 1, 1, 2, 2, 2, 0, 1, 1, 2, 2, 2, 3, 3, 4],
               cols=[1, 0, 1, 2, 0, 1, 2, 0, 0, 2, 0, 1, 2, 0, 2, 0],
               idxs=[0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               colors=[8, 3, 8, 1, 8, 4, 8, 3, 8, 8, 8, 8, 4, 8, 8, 1],
               brows=[1, 6, 9, 2], bcols=[2, 7, 1, 13], rotates=[1, 1]),
      generate(width=15, height=14,
               rows=[0, 1, 1, 1, 2, 3, 4, 5, 5, 5],
               cols=[1, 0, 1, 2, 1, 1, 1, 0, 1, 2],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
               colors=[2, 4, 3, 3, 3, 3, 3, 3, 1, 3],
               brows=[3, 10], bcols=[3, 9], rotates=[2]),
      generate(width=14, height=16,
               rows=[0, 1, 1, 2, 2, 2, 2, 2, 2, 3],
               cols=[4, 0, 4, 0, 1, 2, 3, 4, 5, 4],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
               colors=[4, 8, 8, 1, 8, 8, 8, 2, 8, 8],
               brows=[2, 10], bcols=[5, 1], rotates=[3]),
  ]
  test = [
      generate(width=19, height=24,
               rows=[0, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 0, 0, 1, 1, 2, 2, 2],
               cols=[2, 1, 2, 3, 4, 5, 2, 5, 0, 1, 2, 3, 0, 1, 1, 3, 1, 2, 3],
               idxs=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
               colors=[5, 5, 1, 5, 5, 4, 5, 5, 2, 5, 5, 5, 5, 2, 5, 5, 4, 5, 1],
               brows=[3, 9, 16, 12], bcols=[5, 10, 9, 2], rotates=[1, 4]),
  ]
  return {'train': train, 'test': test}
