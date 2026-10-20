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

"""Generator."""

import common


def _unambiguous_motif(rows, cols, colors):
  """Every symmetry preserving the visible core must preserve its decoration."""
  marks = [(r, c) for r, c, ink in zip(rows, cols, colors) if ink == common.red()]
  if len(marks) != 1: return False
  mr, mc = marks[0]
  full = {(r - mr, c - mc, ink) for r, c, ink in zip(rows, cols, colors)}
  core = {(r, c, ink) for r, c, ink in full
          if ink in (common.red(), common.yellow())}
  for swap in (False, True):
    for sy in (-1, 1):
      for sx in (-1, 1):
        def transform(points):
          return {(sy * (c if swap else r), sx * (r if swap else c), ink)
                  for r, c, ink in points}
        if transform(core) == core and transform(full) != full: return False
  return True


def _sample_motif(wide, tall, num_blue, num_green, max_attempts=256):
  extras = [common.red()] + [common.blue()] * num_blue + [common.green()] * num_green
  for _ in range(max_attempts):
    pixels = common.sample(common.all_pixels(wide, tall), 5)
    if not common.diagonally_connected(pixels): continue
    added = []
    for color in extras:
      candidates = [(r + dr, c + dc) for r, c in pixels
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
      candidates = [(r, c) for r, c in candidates
                    if (r, c) not in pixels and (r, c) not in added
                    and (color != common.red() or (r != tall // 2 and c != wide // 2))]
      if not candidates: break
      added.append(common.choice(candidates))
    if len(added) != len(extras): continue
    points, colors = pixels + added, [common.yellow()] * 5 + extras
    top, left = min(r for r, c in points), min(c for r, c in points)
    rows, cols = [r - top for r, c in points], [c - left for r, c in points]
    if _unambiguous_motif(rows, cols, colors): return rows, cols, colors
  raise RuntimeError("Could not draw an orientation-identifiable motif")


def generate(width=None, height=None, rows=None, cols=None, colors=None,
             megarows=None, megacols=None, megarotates=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the grid
    height: the height of the grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    colors: a list of digits representing the colors to be used
    megarows: a list of vertical coordinates for sprite placement
    megacols: a list of horizontal coordinates for sprite placement
    megarotates: a list of digits representing the rotations of mega-sprites
  """
  if width is None:
    width, height = common.randint(13, 15), common.randint(13, 15)
    # Choose the dimensions of the rainbow sprites.
    sprite_type, wide, tall = common.randint(0, 2), 3, 3
    if sprite_type == 1: wide, tall = 4, 2
    if sprite_type == 2: wide, tall = 5, 1
    num_blue, num_green = common.randint(1, 2), common.randint(1, 3)
    rows, cols, colors = _sample_motif(wide, tall, num_blue, num_green)
    wide, tall = max(cols) + 1, max(rows) + 1
    # Choose the positions of the mega-sprites, making sure they don't overlap.
    num_sprites = common.randint(3, 4)
    megarotates = [common.randint(0, 3) for _ in range(num_sprites)]
    megawides = [tall if a == 1 else wide for a in megarotates]
    megatalls = [wide if a == 1 else tall for a in megarotates]
    for attempt in range(256):
      if attempt: width, height = common.randint(13, 15), common.randint(13, 15)
      placed = common.place_rectangles(width, height, megawides, megatalls, spacing=1)
      if placed is not None:
        megarows, megacols = placed
        break
    else:
      raise RuntimeError("Could not place all motif copies")

  grid, output = common.grids(width, height)
  wide, tall = max(cols) + 1, max(rows) + 1
  for i, megarotate in enumerate(megarotates):
    mr, mc = megarows[i], megacols[i]
    for row, col, color in zip(rows, cols, colors):
      r, c = row, col
      if megarotate == 1: r, c = c, tall - 1 - r
      if megarotate == 2: r, c = tall - 1 - r, wide - 1 - c
      if megarotate == 3: c = wide - 1 - c
      output[mr + r][mc + c] = color
      if i != 0 and color not in [common.yellow(), common.red()]: continue
      grid[mr + r][mc + c] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=13, height=13, rows=[0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2],
               cols=[1, 3, 4, 0, 1, 2, 3, 4, 0, 2, 4],
               colors=[1, 1, 2, 4, 4, 4, 4, 4, 3, 3, 3], megarows=[1, 2, 7],
               megacols=[1, 9, 3], megarotates=[0, 1, 2]),
      generate(width=13, height=13, rows=[0, 1, 1, 1, 1, 2, 3, 3, 3, 3],
               cols=[2, 0, 1, 2, 3, 2, 0, 1, 2, 3],
               colors=[2, 4, 4, 4, 1, 4, 3, 3, 4, 3], megarows=[1, 4, 9],
               megacols=[2, 8, 3], megarotates=[0, 3, 1]),
      generate(width=13, height=13, rows=[0, 0, 1, 1, 1, 1, 2, 2, 3],
               cols=[2, 3, 0, 1, 2, 3, 1, 2, 2],
               colors=[4, 2, 1, 4, 4, 4, 3, 4, 1], megarows=[1, 5, 8],
               megacols=[1, 7, 3], megarotates=[0, 3, 2]),
  ]
  test = [
      generate(width=15, height=14, rows=[0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3],
               cols=[0, 1, 0, 1, 2, 0, 2, 3, 1, 2, 3],
               colors=[1, 3, 4, 4, 2, 4, 4, 3, 4, 4, 1], megarows=[2, 3, 9, 8],
               megacols=[2, 10, 0, 7], megarotates=[0, 1, 2, 3]),
  ]
  return {"train": train, "test": test}
