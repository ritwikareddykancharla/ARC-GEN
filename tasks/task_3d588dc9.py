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

"""Generator for ARC task 3d588dc9.

Rule: the background (7) holds several colour-0 "keys". Each key is a solid
rectangular body with a two-cell stem sticking out of the middle of one
odd-length side. There is exactly one colour-5 staircase triangle, plus
distractors: staircase triangles in other colours, single dots (possibly
colour 0) and an optional stemless 2x2 block of 0. The key whose body shares
rows or columns with the bounding box of the 5 triangle (the nearest one if
several qualify) is edited. Its stem is erased to background, and the body
edge facing the 5 triangle is recoloured 6. Everything else is unchanged.

Scope: random grids are 12..30 cells per side (the fixtures are 16x16).
Triangles have 2..5 rows. The top row is the longest and each lower row
loses one cell on the non-anchored side. Triangles are left- or right-aligned
and often touch a grid edge. Key bodies are 3..5 per side, the stem is 2 long
and leaves from the middle of an odd side. Random scenes contain one or two aligned
keys with a unique nearest candidate, plus 1..2 keys not aligned with the 5 triangle, 1..2 distractor
triangles (which may align with non-target keys), optional 2x2 0 blocks, and
1..3 dots. All objects are kept at least one background cell apart, measured
between bounding boxes.
"""

import copy
import random

import common

BACKGROUND = 7
KEY_COLOUR = 0
TARGET_COLOUR = 5
MARK_COLOUR = 6
DISTRACTOR_COLOURS = [1, 2, 3, 4, 8, 9]


def _tri_cells(row, col, rows, top, align):
  """Cells of a staircase triangle anchored at (row, col)."""
  cells = []
  for i in range(rows):
    for j in range(top - i):
      if align == 'L':
        cells.append((row + i, col + j))
      else:
        cells.append((row + i, col - j))
  return cells


def _tri_box(row, col, rows, top, align):
  if align == 'L':
    return (row, col, row + rows - 1, col + top - 1)
  return (row, col - top + 1, row + rows - 1, col)


def _key_parts(row, col, bh, bw, stem):
  """Body cells and stem cells of a key."""
  body = [(row + i, col + j) for i in range(bh) for j in range(bw)]
  if stem == 'U':
    tail = [(row - 1, col + bw // 2), (row - 2, col + bw // 2)]
  elif stem == 'D':
    tail = [(row + bh, col + bw // 2), (row + bh + 1, col + bw // 2)]
  elif stem == 'L':
    tail = [(row + bh // 2, col - 1), (row + bh // 2, col - 2)]
  else:
    tail = [(row + bh // 2, col + bw), (row + bh // 2, col + bw + 1)]
  return body, tail


def _key_box(row, col, bh, bw, stem):
  r0, c0, r1, c1 = row, col, row + bh - 1, col + bw - 1
  if stem == 'U':
    r0 -= 2
  elif stem == 'D':
    r1 += 2
  elif stem == 'L':
    c0 -= 2
  else:
    c1 += 2
  return (r0, c0, r1, c1)


def _overlap(a0, a1, b0, b1):
  return not (a1 < b0 or a0 > b1)


def _aligned(key, fbox):
  row, col, bh, bw, _ = key
  rows = _overlap(row, row + bh - 1, fbox[0], fbox[2])
  cols = _overlap(col, col + bw - 1, fbox[1], fbox[3])
  return rows, cols


def _free(box, boxes, height, width):
  """True if box is inside the grid and one cell clear of all boxes."""
  r0, c0, r1, c1 = box
  if r0 < 0 or c0 < 0 or r1 >= height or c1 >= width:
    return False
  for a0, b0, a1, b1 in boxes:
    if not (r1 < a0 - 1 or r0 > a1 + 1 or c1 < b0 - 1 or c0 > b1 + 1):
      return False
  return True


def _sample_triangle(height, width, colour, boxes, edge_prob):
  for _ in range(80):
    rows = random.randint(2, 5)
    top = random.randint(rows, min(rows + 4, width - 4))
    align = random.choice('LR')
    if random.random() < edge_prob:
      col = 0 if align == 'L' else width - 1
    elif align == 'L':
      col = random.randint(0, width - top)
    else:
      col = random.randint(top - 1, width - 1)
    row = random.randint(0, height - rows)
    tri = (row, col, rows, top, align, colour)
    box = _tri_box(row, col, rows, top, align)
    if _free(box, boxes, height, width):
      boxes.append(box)
      return tri
  return None


def _sample_key_shape():
  for _ in range(20):
    bh = random.choice([3, 3, 4, 5])
    bw = random.choice([3, 3, 4, 5])
    dirs = (['U', 'D'] if bw % 2 else []) + (['L', 'R'] if bh % 2 else [])
    if dirs:
      return bh, bw, random.choice(dirs)
  raise RuntimeError("Could not sample a valid key shape")


def _sample_key(height, width, boxes, fbox, want_aligned):
  for _ in range(10):
    bh, bw, stem = _sample_key_shape()
    options = []
    for row in range(height):
      for col in range(width):
        key = (row, col, bh, bw, stem)
        if not _free(_key_box(*key), boxes, height, width):
          continue
        rows, cols = _aligned(key, fbox)
        if (rows or cols) == want_aligned:
          options.append(key)
    if options:
      key = random.choice(options)
      boxes.append(_key_box(*key))
      return key
  return None


def _sample_spot(height, width, boxes, size):
  options = []
  for row in range(height):
    for col in range(width):
      box = (row, col, row + size - 1, col + size - 1)
      if _free(box, boxes, height, width):
        options.append(box)
  if not options:
    return None
  box = random.choice(options)
  boxes.append(box)
  return (box[0], box[1])


def _random_scene(requested_height, requested_width, aligned_keys):
  for _ in range(200):
    height = requested_height if requested_height is not None else random.randint(12,30)
    width = requested_width if requested_width is not None else random.randint(12,30)
    boxes = []
    five = _sample_triangle(height, width, TARGET_COLOUR, boxes, 0.7)
    if five is None:
      continue
    fbox = _tri_box(*five[:5])
    target = _sample_key(height, width, boxes, fbox, True)
    if target is None:
      continue
    keys = [target]
    n_aligned = aligned_keys if aligned_keys is not None else random.choice((1,2))
    for _ in range(n_aligned-1):
      other=_sample_key(height,width,boxes,fbox,True)
      if other is not None:keys.append(other)
    if len(keys)!=n_aligned:continue
    cy,cx=(fbox[0]+fbox[2])/2,(fbox[1]+fbox[3])/2
    distances=[abs(r+(h-1)/2-cy)+abs(c+(w-1)/2-cx) for r,c,h,w,d in keys]
    if distances.count(min(distances))!=1:continue
    for _ in range(random.randint(1, 2)):
      other = _sample_key(height, width, boxes, fbox, False)
      if other is not None:
        keys.append(other)
    if len(keys) <= n_aligned:
      continue
    random.shuffle(keys)
    triangles = [five]
    for colour in random.sample(DISTRACTOR_COLOURS, random.randint(1, 2)):
      tri = _sample_triangle(height, width, colour, boxes, 0.5)
      if tri is not None:
        triangles.append(tri)
    blocks = []
    if random.random() < 0.5:
      spot = _sample_spot(height, width, boxes, 2)
      if spot is not None:
        blocks.append(spot)
    dots = []
    for _ in range(random.randint(1, 3)):
      if random.random() < 0.25:
        colour = KEY_COLOUR
      else:
        colour = random.choice(DISTRACTOR_COLOURS)
      spot = _sample_spot(height, width, boxes, 1)
      if spot is not None:
        dots.append((spot[0], spot[1], colour))
    return height, width, triangles, keys, blocks, dots
  raise RuntimeError('could not construct a scene')


def _render(height, width, background, triangles, keys, blocks, dots):
  grid = common.grid(width, height, background)
  for tri in triangles:
    for r, c in _tri_cells(*tri[:5]):
      grid[r][c] = tri[5]
  for key in keys:
    body, tail = _key_parts(*key)
    for r, c in body + tail:
      grid[r][c] = KEY_COLOUR
  for r, c in blocks:
    for dr in range(2):
      for dc in range(2):
        grid[r + dr][c + dc] = KEY_COLOUR
  for r, c, colour in dots:
    grid[r][c] = colour
  return grid


def _answer(grid, background, triangles, keys):
  out = copy.deepcopy(grid)
  five = [t for t in triangles if t[5] == TARGET_COLOUR][0]
  fbox = _tri_box(*five[:5])
  fcy = (fbox[0] + fbox[2]) / 2
  fcx = (fbox[1] + fbox[3]) / 2
  best = None
  for key in keys:
    rows, cols = _aligned(key, fbox)
    if not (rows or cols):
      continue
    row, col, bh, bw, _ = key
    dist = abs(row + (bh - 1) / 2 - fcy) + abs(col + (bw - 1) / 2 - fcx)
    if best is None or dist < best[0]:
      best = (dist, key, rows)
  if best is None:
    raise ValueError('no key aligned with the 5 triangle')
  _, key, rows = best
  row, col, bh, bw, _ = key
  _, tail = _key_parts(*key)
  for r, c in tail:
    out[r][c] = background
  if rows:
    x = col if fcx < col + (bw - 1) / 2 else col + bw - 1
    for r in range(row, row + bh):
      out[r][x] = MARK_COLOUR
  else:
    y = row if fcy < row + (bh - 1) / 2 else row + bh - 1
    for c in range(col, col + bw):
      out[y][c] = MARK_COLOUR
  return out


def generate(height=None, width=None, triangles=None, keys=None,
             blocks=None, dots=None, background=None, aligned_keys=None):
  """Build one input/output pair.

  Args:
    height: exact grid height (random 12..30; explicit default 16).
    width: exact grid width (random 12..30; explicit default 16).
    triangles: list of (row, col, rows, top_len, align, colour). align 'L'
      means rows start at col and extend right; 'R' means rows end at col.
      Exactly one triangle must have colour 5. If None, a fresh random scene
      is built.
    keys: list of (row, col, body_h, body_w, stem_dir), stem_dir in UDLR.
      The stem is two cells long and leaves the middle of an odd-length side.
    blocks: list of (row, col) top-left corners of stemless 2x2 0 blocks.
    dots: list of (row, col, colour) single-cell distractors.
    background: background colour (fixed 7).
    aligned_keys: exact random aligned-candidate count, 1 or 2.
  """
  if background is None:
    background = BACKGROUND
  if background != BACKGROUND:raise ValueError("Native background must be 7")
  for d in (height,width):
    if d is not None and (not isinstance(d,int) or not 1 <= d <= 30):raise ValueError("Dimensions must be in 1..30")
  if aligned_keys not in (None,1,2):raise ValueError("aligned_keys must be 1 or 2")
  if triangles is None:
    if any(v is not None for v in (keys,blocks,dots)):raise ValueError("Explicit scene parts require triangles")
    if any(d is not None and d < 12 for d in (height,width)):raise ValueError("Random sides must be at least 12")
    height, width, triangles, keys, blocks, dots = _random_scene(height,width,aligned_keys)
  else:
    if aligned_keys is not None:raise ValueError("aligned_keys applies to random scenes")
    height = 16 if height is None else height
    width = 16 if width is None else width
    keys = keys or []
    blocks = blocks or []
    dots = dots or []
  if not keys or sum(t[5]==5 for t in triangles)!=1:raise ValueError("Need keys and exactly one target triangle")
  occupied=set()
  groups=[]
  for r,c,n,top,align,colour in triangles:
    if align not in ('L','R') or n<1 or top<n or colour not in DISTRACTOR_COLOURS+[5]:raise ValueError("Invalid triangle")
    groups.append(_tri_cells(r,c,n,top,align))
  for r,c,h,w,d in keys:
    if d not in 'UDLR' or min(h,w)<3 or (d in 'UD' and w%2==0) or (d in 'LR' and h%2==0):raise ValueError("Invalid key body or stem")
    body,tail=_key_parts(r,c,h,w,d);groups.append(body+tail)
  for r,c in blocks:groups.append([(r+i,c+j) for i in range(2) for j in range(2)])
  for r,c,colour in dots:
    if colour not in DISTRACTOR_COLOURS+[0]:raise ValueError("Invalid distractor colour")
    groups.append([(r,c)])
  for cells in groups:
    if any(not (0<=r<height and 0<=c<width) or (r,c) in occupied for r,c in cells):raise ValueError("Overlapping or out-of-bounds scene")
    occupied.update(cells)
  grid = _render(height, width, background, triangles, keys, blocks, dots)
  return {'input': grid, 'output': _answer(grid, background, triangles, keys)}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=16, width=16,
               triangles=[(0, 6, 3, 3, 'R', 1), (9, 15, 4, 6, 'R', 5)],
               keys=[(6, 2, 4, 3, 'U'), (13, 5, 3, 4, 'R')],
               dots=[(1, 9, 8), (6, 10, 3)]),
      generate(height=16, width=16,
               triangles=[(1, 0, 3, 4, 'L', 9), (6, 0, 4, 8, 'L', 5)],
               keys=[(1, 7, 3, 4, 'R'), (7, 9, 3, 4, 'R')],
               dots=[(6, 15, 0), (14, 1, 9)]),
  ]
  test = [
      generate(height=16, width=16,
               triangles=[(1, 0, 4, 5, 'L', 5), (5, 15, 5, 5, 'R', 2)],
               keys=[(2, 7, 4, 3, 'D'), (9, 6, 3, 4, 'R')],
               blocks=[(1, 12)],
               dots=[(13, 11, 8)]),
  ]
  return {'train': train, 'test': test}
