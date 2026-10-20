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

"""ARC task db0c5428: reflect the eight frame tiles outward and fill the hole.

Rule: the input holds one 9x9 D4-symmetric square on a background of 8. The
square is a 3x3 arrangement of 3x3 tiles, and its central tile is empty. In the
output, each of the eight outer tiles is mirrored across its outer edge and
stamped one tile further out. Edge tiles are flipped once and corner tiles are
rotated 180 degrees. Together they form a 15x15 star. Cells outside the canvas
are clipped. The empty centre is then filled from the 5x5 ring around it.
Centre cell (i, j) takes ring cell (2i, 2j), and the middle cell takes ring
cell (0, 1).

Scope: the latent scene has two tiles. The top-left corner tile is symmetric
under transpose, and the top-middle edge tile is symmetric under a left-right
flip. Together they determine the whole D4-symmetric 9x9 frame. Any tile that
is not supplied is sampled from a palette of 2-4 non-background colours. The
palette also includes every colour of a supplied tile, so it can be larger.
About 60% of draws aim for pairwise-distinct centre source colours. This target
is met only where sampled cells can achieve it. Otherwise the generator only
ensures that the sources are not all equal.

Repairs apply only to sampled tiles. If both tiles are supplied they are used
as given, so degenerate (for example monochrome) tiles are accepted. For
sampled tiles:
  * each mirrored copy usually differs from its source, and a corner's
    180-degree rotation usually differs from a single flip;
  * when the middle source colour is (tied) modal in the frame, about half the
    time a bounded search tries to replace it with a non-modal colour. This
    breaks the 'middle = modal colour' confound that the fixtures share. The
    search can fail, so the achieved non-modal rate is below 50%;
  * about half the time the middle source is decorrelated from the edge tile's
    middle-row side cell, and separately from its top-middle cell. All
    fixtures share both coincidences.

Random canvas sides are 15..30 and are often square. By default about 88% of
random placements leave room for the full 15x15 star. The other ~12% (or
clip=True) place the frame so that the star is clipped by the canvas. This is a
synthetic extension, because no fixture clips. Canvases larger than 19 are also
synthetic extensions. Colour 8 must be the strict plurality (most frequent)
colour of the input. Asymmetric frames, other backgrounds and scenes with
multiple frames are not generated.
"""

import collections
import random

import common

BG = 8
MAX_SIDE = 30
FRAME_CELLS = 72
CLIP_PROB = 0.12


def _flipud(t):
  return [list(r) for r in t[::-1]]


def _fliplr(t):
  return [list(r[::-1]) for r in t]


def _transpose(t):
  return [list(r) for r in zip(*t)]


def _tiles(corner, edge):
  """Returns the dict (by, bx) -> 3x3 tile of the D4-symmetric frame."""
  left = _transpose(edge)
  return {
      (0, 0): [list(r) for r in corner],
      (0, 1): [list(r) for r in edge],
      (0, 2): _fliplr(corner),
      (1, 0): left,
      (1, 2): _fliplr(left),
      (2, 0): _flipud(corner),
      (2, 1): _flipud(edge),
      (2, 2): _flipud(_fliplr(corner)),
  }


def _check_tile(t, name):
  """Checks that an explicit tile is a 3x3 grid of non-background colours."""
  if (not isinstance(t, (list, tuple)) or len(t) != 3 or
      any(not isinstance(r, (list, tuple)) or len(r) != 3 for r in t)):
    raise ValueError(name + " must be a 3x3 tile")
  for r in t:
    for v in r:
      if type(v) is not int or v < 0 or v > 9 or v == BG:
        raise ValueError(name + " must use int colours 0..9 other than 8")


def _choice_excluding(palette, banned):
  options = [c for c in palette if c not in banned]
  return random.choice(options)


def _sample_tiles(corner=None, edge=None):
  """Samples whichever of the corner and edge tiles was not supplied."""
  if corner is not None:
    _check_tile(corner, "corner")
    if any(corner[i][j] != corner[j][i] for i in range(3) for j in range(3)):
      raise ValueError("corner must be symmetric under transpose")
    corner = [list(r) for r in corner]
  if edge is not None:
    _check_tile(edge, "edge")
    if any(r[0] != r[2] for r in edge):
      raise ValueError("edge must be symmetric under a left-right flip")
    edge = [list(r) for r in edge]
  if corner is not None and edge is not None:
    return corner, edge

  distinct = random.random() < 0.6
  counts = collections.Counter()
  for t in (corner, edge):
    if t is not None:
      counts.update(v for r in t for v in r)
  palette = list(counts)
  random.shuffle(palette)
  low = 3 if distinct else 2
  target = random.randint(max(low, len(palette)), max(4, len(palette)))
  spare = [c for c in range(10) if c != BG and c not in palette]
  palette += random.sample(spare, target - len(palette))
  main = counts.most_common(1)[0][0] if counts else palette[0]

  def pick():
    if random.random() < 0.45:
      return main
    return random.choice(palette)

  corner_sampled = corner is None
  edge_sampled = edge is None
  if corner_sampled:
    corner = [[0] * 3 for _ in range(3)]
    for i in range(3):
      for j in range(i, 3):
        v = pick()
        corner[i][j] = v
        corner[j][i] = v
  if edge_sampled:
    edge = [[0] * 3 for _ in range(3)]
    for i in range(3):
      for j in range(2):
        v = pick()
        edge[i][j] = v
        edge[i][2 - j] = v

  def centre_ok(c, m, e):
    return len({c, m, e}) == 3 if distinct else len({c, m, e}) >= 2

  # Centre sources: corners <- corner[2][2], edges <- edge[2][1],
  # middle <- edge[2][0]. Only sampled cells are repaired, and every repair
  # keeps each tile symmetric. No retry loop is needed.
  def set_mid(v):
    edge[2][0] = v
    edge[2][2] = v

  if distinct:
    if edge_sampled:
      c = corner[2][2]
      if edge[2][0] == c:
        set_mid(_choice_excluding(palette, {c}))
      if edge[2][1] in (c, edge[2][0]):
        edge[2][1] = _choice_excluding(palette, {c, edge[2][0]})
    else:
      banned = {edge[2][0], edge[2][1]}
      if corner[2][2] in banned:
        corner[2][2] = _choice_excluding(palette, banned)
  elif len({corner[2][2], edge[2][0], edge[2][1]}) < 2:
    if edge_sampled:
      set_mid(_choice_excluding(palette, {corner[2][2]}))
    else:
      corner[2][2] = _choice_excluding(palette, {edge[2][0]})

  # Usually make the mirrored copies differ from their sources. Row 0 of the
  # edge and corner cell (0, 0) never feed the centre fill.
  if edge_sampled and edge[0] == edge[2] and random.random() < 0.85:
    edge[0][1] = _choice_excluding(palette, {edge[2][1]})
  # For a transpose-symmetric corner, rot180 equals a single flip iff row 0 ==
  # row 2. Setting corner[0][0] to anything other than corner[2][2] removes
  # both that case and rot180 == identity.
  if (corner_sampled and random.random() < 0.85 and
      (corner[0] == corner[2] or _flipud(_fliplr(corner)) == corner)):
    corner[0][0] = _choice_excluding(palette, {corner[2][2]})

  # When the middle colour is (tied) modal, about half the time try to replace
  # it with a non-modal colour. Each tile appears 4 times in the frame, so the
  # tile counts give the frame mode. The search is bounded and may fail.
  def mid_is_modal(e):
    cnt = collections.Counter(v for t in (corner, e) for r in t for v in r)
    m = cnt[e[2][0]]
    return all(m >= n for col, n in cnt.items() if col != e[2][0])

  if edge_sampled and random.random() < 0.5 and mid_is_modal(edge):
    opts = [v for v in palette if v != edge[2][0]]
    random.shuffle(opts)
    for v in opts:
      trial = [list(r) for r in edge]
      trial[2][0] = v
      trial[2][2] = v
      if not centre_ok(corner[2][2], v, trial[2][1]):
        continue
      if trial[0] == trial[2] and edge[0] != edge[2]:
        continue
      if not mid_is_modal(trial):
        edge = trial
        break

  # Decorrelate the middle source from the neighbouring edge cells that all
  # fixtures happen to share with it. Neither cell feeds the centre fill.
  # Lowering the middle colour's count can never make it more modal.
  if edge_sampled and random.random() < 0.5 and edge[1][0] == edge[2][0]:
    v = _choice_excluding(palette, {edge[2][0]})
    edge[1][0] = v
    edge[1][2] = v
  if edge_sampled and random.random() < 0.5 and edge[0][1] == edge[2][0]:
    opts = [v for v in palette if v not in (edge[2][0], edge[2][1])]
    if opts:
      # Differing from edge[2][1] also keeps row 0 != row 2.
      edge[0][1] = random.choice(opts)
  return corner, edge


def _check_int(v, name):
  if v is not None and type(v) is not int:
    raise ValueError(name + " must be an int")


def _min_side(pos):
  """Smallest sampled side that holds the frame at pos (star if possible)."""
  if pos is None:
    return 15
  if pos < 0 or pos + 9 > MAX_SIDE:
    raise ValueError("frame offset does not fit in a 30-cell canvas")
  return max(15, min(pos + 12, MAX_SIDE), pos + 9)


def _side_candidates(pos, other, maxc):
  """Sides for a sampled dimension that keep 8 the strict plurality."""
  cands = list(range(_min_side(pos), MAX_SIDE + 1))
  if other is not None:
    cands = [s for s in cands if s * other - FRAME_CELLS > maxc]
  if not cands:
    raise ValueError("no canvas side keeps 8 the most frequent colour")
  return cands


def _clips(pos, size):
  """True if a frame at pos on this axis pushes part of the star off-canvas."""
  return pos < 3 or pos + 12 > size


def _clipped_pos(size):
  """Samples an offset whose star is clipped on this axis."""
  opts = [p for p in range(0, size - 8) if _clips(p, size)]
  return random.choice(opts)


def generate(width=None, height=None, row=None, col=None, corner=None,
             edge=None, clip=None):
  """Builds one input/output pair.

  Args:
    width: canvas width, int 9..30. If omitted, it is sampled from 15..30
      (enlarged as needed for an explicit col) and is often equal to height.
    height: canvas height, int 9..30. If omitted, it is sampled from 15..30
      (enlarged as needed for an explicit row).
    row: int top row of the 9x9 frame. If omitted, it is sampled according
      to clip.
    col: int left column of the 9x9 frame, sampled the same way.
    corner: 3x3 top-left tile, symmetric under transpose, without colour 8.
      Sampled if omitted, and compatible with a supplied edge.
    edge: 3x3 top-middle tile, symmetric under a left-right flip, without
      colour 8. Sampled if omitted, and compatible with a supplied corner.
    clip: optional bool saying whether the 15x15 star is clipped by the
      canvas. If None, a random choice (about 12% True) is used for sampled
      offsets. Explicit offsets are kept as given. True forces a sampled
      offset to clip unless an explicit one already does. False keeps sampled
      offsets clear of the border. An explicit clip that contradicts
      explicit offsets or sides raises ValueError.

  Colour 8 must be the strict plurality colour of the input. Sampled sides
  always satisfy this. If explicit sides violate it, or invalid controls are
  given, a ValueError is raised.
  """
  for v, name in ((width, "width"), (height, "height"), (row, "row"),
                  (col, "col")):
    _check_int(v, name)
  if clip is not None and type(clip) is not bool:
    raise ValueError("clip must be a bool or None")
  for side in (width, height):
    if side is not None and not 9 <= side <= MAX_SIDE:
      raise ValueError("canvas sides must be ints in 9..30")
  for pos in (row, col):
    if pos is not None and (pos < 0 or pos + 9 > MAX_SIDE):
      raise ValueError("frame offset does not fit in a 30-cell canvas")

  corner, edge = _sample_tiles(corner, edge)
  tiles = _tiles(corner, edge)
  frame_counts = collections.Counter(
      v for t in tiles.values() for r in t for v in r)
  maxc = max(frame_counts.values())

  if height is None:
    height = random.choice(_side_candidates(row, width, maxc))
  if width is None:
    cands = _side_candidates(col, height, maxc)
    if height in cands and random.random() < 0.6:
      width = height
    else:
      width = random.choice(cands)
  if (row is not None and row + 9 > height) or (
      col is not None and col + 9 > width):
    raise ValueError("frame does not fit in the canvas")

  # Placement. Explicit offsets are always kept as given.
  pos = {"row": row, "col": col}
  size = {"row": height, "col": width}
  sampled = [a for a in ("row", "col") if pos[a] is None]
  explicit_clip = any(_clips(pos[a], size[a]) for a in ("row", "col")
                      if pos[a] is not None)
  clip_given = clip is not None
  if not sampled:
    if clip_given and clip != explicit_clip:
      raise ValueError("clip contradicts the explicit frame placement")
  else:
    if clip is None:
      clip = random.random() < CLIP_PROB
    if clip:
      forced = None if explicit_clip else random.choice(sampled)
      for a in sampled:
        if a == forced:
          pos[a] = _clipped_pos(size[a])
        else:
          pos[a] = random.randint(0, size[a] - 9)
    else:
      if clip_given and explicit_clip:
        raise ValueError("clip=False contradicts the explicit placement")
      for a in sampled:
        if size[a] >= 15:
          pos[a] = random.randint(3, size[a] - 12)
        elif clip_given:
          raise ValueError("clip=False needs sides of at least 15")
        else:
          pos[a] = random.randint(0, size[a] - 9)
  row, col = pos["row"], pos["col"]

  grid = common.grid(width, height, BG)
  for (by, bx), t in tiles.items():
    for i in range(3):
      for j in range(3):
        grid[row + 3 * by + i][col + 3 * bx + j] = t[i][j]

  counts = collections.Counter(v for r in grid for v in r)
  if any(n >= counts[BG] for c, n in counts.items() if c != BG):
    raise ValueError("background 8 must remain the most frequent colour")

  output = [list(r) for r in grid]
  for (by, bx), t in tiles.items():
    dy, dx = by - 1, bx - 1
    m = t
    if dy != 0:
      m = _flipud(m)
    if dx != 0:
      m = _fliplr(m)
    ty = row + 3 * by + 3 * dy
    tx = col + 3 * bx + 3 * dx
    for i in range(3):
      for j in range(3):
        yy, xx = ty + i, tx + j
        if 0 <= yy < height and 0 <= xx < width:
          output[yy][xx] = m[i][j]

  # Centre fill from the latent tiles. ring[0][0] = corner[2][2],
  # ring[0][1] = edge[2][0], ring[0][2] = edge[2][1], and the ring is D4
  # symmetric.
  c_src, m_src, e_src = corner[2][2], edge[2][0], edge[2][1]
  for i in range(3):
    for j in range(3):
      if i == 1 and j == 1:
        v = m_src
      elif i != 1 and j != 1:
        v = c_src
      else:
        v = e_src
      output[row + 3 + i][col + 3 + j] = v
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=18, height=18, row=3, col=3,
               corner=[[6, 6, 4], [6, 4, 6], [4, 6, 9]],
               edge=[[4, 6, 4], [6, 4, 6], [6, 9, 6]]),
      generate(width=16, height=16, row=4, col=3,
               corner=[[1, 1, 1], [1, 1, 1], [1, 1, 7]],
               edge=[[1, 1, 1], [1, 1, 1], [1, 7, 1]]),
      generate(width=19, height=19, row=5, col=6,
               corner=[[5, 6, 5], [6, 5, 5], [5, 5, 3]],
               edge=[[5, 5, 5], [5, 5, 5], [5, 2, 5]]),
  ]
  test = [
      generate(width=17, height=17, row=4, col=4,
               corner=[[3, 7, 7], [7, 7, 4], [7, 4, 4]],
               edge=[[7, 7, 7], [7, 7, 7], [7, 1, 7]]),
  ]
  return {"train": train, "test": test}
