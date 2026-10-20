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

"""ARC-GEN style generator for task 58490d8a.

Rule: the input has a non-zero background and exactly one rectangle of colour
0 (the panel). Column 1 of the panel holds a legend: one coloured dot on each
odd row (1, 3, 5, ...). Outside the panel there are small shapes in several
colours. Each shape is its own 8-connected component, and some shapes hold
together only through diagonal contacts. The output is the cropped panel.
In it, each legend row of colour c holds n dots of colour c at columns
1, 3, ..., 2n-1, where n is the number of separate shapes of colour c outside
the panel. Shapes whose colour is not in the legend are distractors and are
ignored.

Scope: the sampler draws a random background colour, a grid of 14..30 per
side, and a random panel size and position. The panel is (2k+1) rows by 5..13
columns (wider if larger counts are requested). There are 2-4 legend colours
(any number that fits the palette when the legend is given explicitly), and
1..min(panel_width // 2, 5) shapes per legend colour. At least one colour has
two or more shapes, so the panel always changes. There are 0-2 distractor
colours with 1-3 shapes each. Shapes mix the fixture library with fresh procedural 4/8-connected binary
masks of up to twelve cells in a 4x5 box; either mode can be selected. Every shape keeps a one-cell gap from every other shape and from the
panel, so the count is unambiguous.

Deliberately not supported: legend colours with zero shapes in random scenes,
counts that overflow the panel width, legend columns other than column 1, and
shapes that touch each other.
"""

import math
import random

import common


SPRITES = {
  "square": [[1, 1], [1, 1]],
  "plus": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
  "ring": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
  "x": [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
  "hook": [[1, 1, 0], [1, 0, 1], [0, 1, 0]],
  "hbar": [[1, 1, 1], [0, 1, 0], [1, 1, 1]],
  "tri": [[0, 1, 0], [1, 1, 1]],
  "arch": [[1, 1, 1], [1, 0, 1]],
  "tee": [[1, 0], [1, 1], [1, 0]],
  "fork": [[0, 1, 0], [1, 1, 1], [1, 0, 1]],
  "cup": [[1, 0, 1], [1, 1, 1]],
  "el": [[1, 0], [1, 1]],
  "diag": [[1, 0], [0, 1]],
  "bar": [[1, 1, 1]],
  "vbar": [[1], [1], [1]],
}


def _sprite(name):
  if isinstance(name,str):
    if name not in SPRITES:
      raise ValueError("unknown sprite "+name)
    return SPRITES[name]
  if not name or not name[0] or any(len(row)!=len(name[0]) for row in name):
    raise ValueError("sprite must be a nonempty rectangle")
  if any(v not in (0,1) for row in name for v in row):
    raise ValueError("sprite cells must be binary")
  points={(y,x) for y,row in enumerate(name) for x,v in enumerate(row) if v}
  if not points:
    raise ValueError("sprite cannot be empty")
  seen={min(points)};todo=list(seen)
  while todo:
    y,x=todo.pop()
    for dy in (-1,0,1):
      for dx in (-1,0,1):
        q=(y+dy,x+dx)
        if q in points and q not in seen:
          seen.add(q);todo.append(q)
  if seen!=points:
    raise ValueError("sprite must be 8-connected")
  return name


def _random_sprite():
  """Fresh small 4/8-connected masks, not selected from the fixture library."""
  h,w=random.randint(1,4),random.randint(1,5)
  target=random.randint(1,min(12,h*w))
  cells={(random.randrange(h),random.randrange(w))}
  diagonal=random.random()<0.5
  steps=[(dy,dx) for dy in (-1,0,1) for dx in (-1,0,1)
         if (dy or dx) and (diagonal or abs(dy)+abs(dx)==1)]
  while len(cells)<target:
    frontier=sorted({(y+dy,x+dx) for y,x in cells for dy,dx in steps
                     if 0<=y+dy<h and 0<=x+dx<w}-cells)
    cells.add(random.choice(frontier))
  y0=min(y for y,x in cells);x0=min(x for y,x in cells)
  y1=max(y for y,x in cells);x1=max(x for y,x in cells)
  return tuple(tuple(int((y,x) in cells) for x in range(x0,x1+1)) for y in range(y0,y1+1))


def _cells(name, r, c):
  sprite = _sprite(name)
  out = []
  for i, row in enumerate(sprite):
    for j, v in enumerate(row):
      if v:
        out.append((r + i, c + j))
  return out


def _dilate(cells):
  out = set()
  for (r, c) in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        out.add((r + dr, c + dc))
  return out


def _place(width, height, panel, todo):
  """Places (colour, sprite) shapes with one-cell gaps; None on failure."""
  pr, pc, ph, pw = panel
  blocked = _dilate([(pr + i, pc + j) for i in range(ph) for j in range(pw)])
  shapes = []
  for color, name in todo:
    sprite=_sprite(name)
    sh = len(sprite)
    sw = len(sprite[0])
    if sh > height or sw > width:
      return None
    spot = None
    for _ in range(40):
      r = random.randint(0, height - sh)
      c = random.randint(0, width - sw)
      if not any(cell in blocked for cell in _cells(name, r, c)):
        spot = (r, c)
        break
    if spot is None:
      cands = []
      for r in range(height - sh + 1):
        for c in range(width - sw + 1):
          if not any(cell in blocked for cell in _cells(name, r, c)):
            cands.append((r, c))
      if not cands:
        return None
      spot = random.choice(cands)
    r, c = spot
    blocked |= _dilate(_cells(name, r, c))
    shapes.append((color, r, c, name))
  return shapes


def _sample_scene(width, height, background, panel, legend, counts,
                  num_distractors, sprite_mode):
  """Samples the unspecified latent parameters; returns None on failure."""
  if counts is not None and legend is not None and len(counts) != len(legend):
    raise ValueError("counts must have one entry per legend colour")
  if counts is not None and any(n < 1 for n in counts):
    raise ValueError("counts must be positive")
  if background is None:
    pool = [c for c in range(1, 10) if legend is None or c not in legend]
    bg = random.choice(pool)
  else:
    bg = background
  others = [c for c in range(1, 10) if c != bg]
  if legend is None:
    k = len(counts) if counts is not None else random.choice([2, 2, 3, 3, 4])
    if k > len(others) or k < 1:
      raise ValueError("unsupported number of legend colours")
    legend = random.sample(others, k)
  legend = list(legend)
  k = len(legend)
  if panel is None:
    ph = 2 * k + 1
    minpw = max(5, 2 * max(counts)) if counts is not None else 5
    maxpw = min(max(13, minpw), width if width is not None else 30)
    if maxpw < minpw:
      raise ValueError("grid too narrow for the requested panel")
    pw = random.randint(minpw, maxpw)
    pr = pc = None
  else:
    pr, pc, ph, pw = panel
  if counts is None:
    cap = max(1, min(pw // 2, 5))
    counts = [random.randint(1, cap) for _ in range(k)]
    while sum(counts) > 12:
      i = counts.index(max(counts))
      counts[i] -= 1
    if cap >= 2 and max(counts) < 2:
      counts[random.randrange(k)] = random.randint(2, cap)
  rest = [c for c in others if c not in legend]
  if num_distractors is None:
    ndis = min(random.choice([0, 1, 1, 2]), len(rest))
  else:
    if num_distractors < 0 or num_distractors > len(rest):
      raise ValueError("not enough spare colours for the distractors")
    ndis = num_distractors
  distractors = random.sample(rest, ndis)
  dis_counts = [random.randint(1, 3) for _ in distractors]
  n = sum(counts) + sum(dis_counts)
  est = int(math.ceil(math.sqrt(2 * (ph + 2) * (pw + 2) + 30 * n)))
  if width is None:
    lo = min(30, max(pw + 2, 14, est))
    width = random.randint(lo, 30)
  if height is None:
    lo = min(30, max(ph + 2, 14, est))
    height = random.randint(lo, 30)
  if pr is None:
    if pw > width or ph > height:
      raise ValueError("panel does not fit the requested grid")
    pr = random.randint(0, height - ph)
    pc = random.randint(0, width - pw)
  names = list(SPRITES.keys())
  todo = []
  for color, cnt in list(zip(legend, counts)) + list(zip(distractors,
                                                         dis_counts)):
    if sprite_mode=="procedural" or (sprite_mode=="mixed" and random.random()<0.5):
      fam=[_random_sprite() for _ in range(random.choice([1,1,2]))]
    else:
      fam = random.sample(names, random.choice([1, 1, 2]))
    for _ in range(cnt):
      todo.append((color, random.choice(fam)))
  random.shuffle(todo)
  shapes = _place(width, height, (pr, pc, ph, pw), todo)
  if shapes is None:
    return None
  return width, height, bg, (pr, pc, ph, pw), legend, shapes


def _check_scene(width, height, background, panel, legend, shapes):
  """Raises ValueError if the latent parameters are inconsistent."""
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid sides must be in 1..30")
  if background not in range(1, 10):
    raise ValueError("background must be a non-zero colour")
  if len(set(legend)) != len(legend):
    raise ValueError("legend colours must be distinct")
  for c in legend:
    if c not in range(1, 10) or c == background:
      raise ValueError("legend colours must be non-zero and non-background")
  pr, pc, ph, pw = panel
  if pr < 0 or pc < 0 or pr + ph > height or pc + pw > width:
    raise ValueError("panel must lie inside the grid")
  if pw < 3 or ph < 2 * len(legend) + 1:
    raise ValueError("panel too small for its legend")
  owner = {}
  for idx, (color, r, c, name) in enumerate(shapes):
    _sprite(name)
    if color not in range(1, 10) or color == background:
      raise ValueError("shape colours must be non-zero and non-background")
    for (y, x) in _cells(name, r, c):
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError("shape out of bounds")
      if pr <= y < pr + ph and pc <= x < pc + pw:
        raise ValueError("shape overlaps the panel")
      if (y, x) in owner:
        raise ValueError("shapes overlap")
      owner[(y, x)] = idx
  for (y, x), idx in owner.items():
    color = shapes[idx][0]
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        other = owner.get((y + dy, x + dx))
        if other is not None and other != idx and shapes[other][0] == color:
          raise ValueError("same-coloured shapes must not touch")
  for color in legend:
    n = sum(1 for s in shapes if s[0] == color)
    if 2 * n > pw:
      raise ValueError("too many shapes of one legend colour for the panel")


def _render(width, height, background, panel, legend, shapes):
  pr, pc, ph, pw = panel
  grid = common.grid(width, height, background)
  for i in range(ph):
    for j in range(pw):
      grid[pr + i][pc + j] = 0
  for idx, color in enumerate(legend):
    grid[pr + 2 * idx + 1][pc + 1] = color
  for color, r, c, name in shapes:
    for (y, x) in _cells(name, r, c):
      grid[y][x] = color
  output = common.grid(pw, ph, 0)
  for idx, color in enumerate(legend):
    output[2 * idx + 1][1] = color
    n = sum(1 for s in shapes if s[0] == color)
    for t in range(n):
      output[2 * idx + 1][1 + 2 * t] = color
  return grid, output


def _background_dominant(grid, background):
  tally = {}
  for row in grid:
    for v in row:
      tally[v] = tally.get(v, 0) + 1
  bgc = tally.get(background, 0)
  return all(v < bgc for k, v in tally.items() if k != background)


def generate(width=None, height=None, background=None, panel=None,
             legend=None, shapes=None, counts=None, num_distractors=None,
             sprite_mode=None):
  """Generates one input/output pair.

  Args:
    width: grid width (columns), 1..30. Optional random-scene control.
    height: grid height (rows), 1..30. Optional random-scene control.
    background: background colour (1..9). Optional random-scene control.
    panel: (row, col, panel_height, panel_width) of the colour-0 panel.
    legend: legend colours, top to bottom, at panel rows 1, 3, ...
    sprite_mode: mixed (default), library or procedural random shape sampling.
    shapes: explicit list of (colour, row, col, sprite_name_or_binary_mask) shapes outside
      the panel. If given, width, height, background, panel and legend are
      required too, and counts/num_distractors must be omitted.
    counts: number of shapes per legend colour (random scenes only).
    num_distractors: number of non-legend shape colours (random scenes only).
  """
  if sprite_mode not in (None,"mixed","library","procedural"):
    raise ValueError("sprite_mode must be mixed, library or procedural")
  if shapes is not None:
    if None in (width, height, background, panel, legend):
      raise ValueError("explicit shapes require width, height, background, "
                       "panel and legend")
    if counts is not None or num_distractors is not None or sprite_mode is not None:
      raise ValueError("counts/num_distractors only apply to random scenes")
    _check_scene(width, height, background, panel, legend, shapes)
    grid, output = _render(width, height, background, panel, legend, shapes)
    if not _background_dominant(grid, background):
      raise ValueError("background must be the most frequent colour")
    return {"input": grid, "output": output}
  for _ in range(60):
    scene = _sample_scene(width, height, background, panel, legend, counts,
                          num_distractors, sprite_mode or "mixed")
    if scene is None:
      continue
    w, h, bg, pnl, leg, shp = scene
    _check_scene(w, h, bg, pnl, leg, shp)
    grid, output = _render(w, h, bg, pnl, leg, shp)
    if _background_dominant(grid, bg):
      return {"input": grid, "output": output}
  raise ValueError("requested parameters leave no room for a valid scene")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
    generate(width=22, height=20, background=3, panel=(13, 0, 7, 7),
             legend=[8, 4, 2],
             shapes=[(8, 1, 17, "hook"), (8, 2, 3, "hook"),
                     (8, 6, 12, "hook"), (2, 7, 2, "square"),
                     (2, 16, 16, "square"), (4, 12, 10, "ring")]),
    generate(width=23, height=23, background=1, panel=(0, 11, 7, 12),
             legend=[2, 8, 3],
             shapes=[(2, 2, 2, "hbar"), (2, 20, 17, "hbar"),
                     (3, 4, 7, "plus"), (3, 6, 0, "plus"),
                     (3, 15, 18, "plus"), (3, 17, 11, "plus"),
                     (8, 10, 4, "x"), (8, 10, 15, "x"),
                     (4, 17, 4, "tri")]),
    generate(width=20, height=21, background=8, panel=(2, 9, 5, 5),
             legend=[1, 4],
             shapes=[(1, 8, 2, "tri"), (1, 12, 9, "tri"),
                     (2, 15, 3, "square"), (4, 15, 12, "fork")]),
  ]
  test = [
    generate(width=25, height=22, background=4, panel=(13, 1, 9, 11),
             legend=[1, 2, 8, 3],
             shapes=[(8, 1, 4, "square"), (8, 2, 21, "square"),
                     (8, 8, 17, "square"), (8, 17, 20, "square"),
                     (3, 1, 10, "plus"), (3, 3, 15, "plus"),
                     (3, 8, 1, "plus"), (3, 14, 13, "plus"),
                     (3, 19, 14, "plus"), (6, 3, 1, "tee"),
                     (2, 5, 6, "ring"), (2, 11, 20, "ring"),
                     (1, 6, 21, "arch"), (1, 8, 10, "arch")]),
  ]
  return {"train": train, "test": test}
