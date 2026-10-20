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

"""ARC task 80a900e0: diamond badges on a checkerboard shoot diagonal rays.

Rule:
  The grid is a checkerboard: 1 where (row + col) is even, 0 elsewhere.
  Several diamond badges are drawn on top of it. A badge has a centre cell,
  which stays 1. Around the centre is a ring of 8 cells of one colour, at
  offsets (+-2,0), (0,+-2) and (+-1,+-1). Each of the four diagonal sides
  (sy, sx) may carry a 3-cell segment of one colour. Its cells are
  centre + (sy*a, sx*(4-a)) for a = 1, 2, 3. In the output, each end cell of
  a segment (a = 1 and a = 3) launches a ray of the segment colour. The ray
  runs in direction (sy, sx) to the grid border and recolours checker cells.
  The middle cell launches nothing. The border may cut a badge off, but its
  ring must stay fully inside. A segment end that lies outside the grid
  launches no visible ray, because the ray already points away from the grid.

Scope:
  Random grid sizes are sampled from 12..30 per side. The lower bound rises
  to 16 for 3 requested badges and to 20 for 4. Explicit sizes 7..30 are
  accepted. Sizes other than the fixture sizes (14x20, 30x24, 21x22) are
  synthetic extensions. The checkerboard phase is fixed with (0,0) = 1 and
  the background is fixed at 0, as in every example.

  Random scenes have 1 to 4 badges, each with 1 to 4 segments. Centres are
  biased towards the border part of the time, so some segments are cut off.
  The bias is symmetric across all four edges: the parity is fixed by
  choosing the second coordinate from values of matching parity.
  Occasionally a segment points into a corner so that both of its rays fall
  off-grid. That segment is then visible but has no effect; this case is a
  synthetic extension.

  Ring and segment colours are sampled from 2..9. Segment colours may repeat
  within a badge or across badges, and may equal another badge's ring colour.
  A segment never takes its own badge's ring colour. Badge diamonds are
  pairwise disjoint. Rays never cross each other or touch another badge, so
  ray order and occlusion conventions never decide an answer. The same
  invariants are enforced on explicit `patterns`.
"""

import random

import common

SIDES = ((-1, -1), (-1, 1), (1, -1), (1, 1))
RING = ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1))
COLOURS = (2, 3, 4, 5, 6, 7, 8, 9)
MIN_SIDE = {1: 12, 2: 12, 3: 16, 4: 20}


def _inside(r, c, h, w):
  return 0 <= r < h and 0 <= c < w


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _ray_cells(cy, cx, sy, sx, h, w):
  """Return the in-grid cells of the two rays launched by side (sy, sx)."""
  cells = []
  for a in (1, 3):
    r, c = cy + sy * a + sy, cx + sx * (4 - a) + sx
    while _inside(r, c, h, w):
      cells.append((r, c))
      r += sy
      c += sx
  return cells


def _diamond(cy, cx):
  return set((cy + dy, cx + dx) for dy in range(-4, 5) for dx in range(-4, 5)
             if abs(dy) + abs(dx) <= 4)


def _render(width, height, patterns):
  """Draw the input and the output from the latent badges."""
  grid = common.grid(width, height, 0)
  for r in range(height):
    for c in range(width):
      if (r + c) % 2 == 0:
        grid[r][c] = 1
  for cy, cx, ring, segs in patterns:
    for dy, dx in RING:
      grid[cy + dy][cx + dx] = ring
    for sy, sx, col in segs:
      for a in (1, 2, 3):
        r, c = cy + sy * a, cx + sx * (4 - a)
        if _inside(r, c, height, width):
          grid[r][c] = col
  output = [row[:] for row in grid]
  for cy, cx, ring, segs in sorted(patterns, key=lambda p: (p[0], p[1])):
    seg_map = {(sy, sx): col for sy, sx, col in segs}
    for side in SIDES:
      if side not in seg_map:
        continue
      sy, sx = side
      for r, c in _ray_cells(cy, cx, sy, sx, height, width):
        if output[r][c] == 1:
          output[r][c] = seg_map[side]
  return grid, output


def _layout_conflict(patterns, h, w):
  """Return True if diamonds overlap or a ray meets another diamond or ray."""
  for i in range(len(patterns)):
    for j in range(i + 1, len(patterns)):
      a, b = patterns[i], patterns[j]
      if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 10:
        return True
  dias = [_diamond(p[0], p[1]) for p in patterns]
  rays = set()
  for i, p in enumerate(patterns):
    cy, cx, segs = p[0], p[1], p[3]
    for sy, sx, _ in segs:
      cells = set(_ray_cells(cy, cx, sy, sx, h, w))
      if cells & rays:
        return True
      for j, dia in enumerate(dias):
        if j != i and cells & dia:
          return True
      rays |= cells
  return False


def _check_patterns(width, height, patterns):
  """Reject malformed explicit badge specifications with ValueError."""
  if not isinstance(patterns, (list, tuple)) or not patterns:
    raise ValueError("patterns must be a non-empty list")
  for p in patterns:
    if not isinstance(p, (list, tuple)) or len(p) != 4:
      raise ValueError("each badge must be (cy, cx, ring, segments)")
    cy, cx, ring, segs = p
    if not (_is_int(cy) and _is_int(cx) and _is_int(ring)):
      raise ValueError("badge centre and ring colour must be integers")
    if (cy + cx) % 2:
      raise ValueError("badge centre must lie on a checker-1 cell")
    if not (2 <= cy <= height - 3 and 2 <= cx <= width - 3):
      raise ValueError("badge ring must lie fully inside the grid")
    if ring not in COLOURS:
      raise ValueError("ring colour must be in 2..9")
    if not isinstance(segs, (list, tuple)) or not 1 <= len(segs) <= 4:
      raise ValueError("each badge needs 1 to 4 segments")
    for s in segs:
      if (not isinstance(s, (list, tuple)) or len(s) != 3 or
          not all(_is_int(v) for v in s)):
        raise ValueError("each segment must be (sy, sx, colour)")
    sides = [(s[0], s[1]) for s in segs]
    if len(set(sides)) != len(sides) or any(s not in SIDES for s in sides):
      raise ValueError("segment sides must be distinct diagonal sides")
    for _, _, col in segs:
      if col not in COLOURS or col == ring:
        raise ValueError("segment colour must be in 2..9 and differ from ring")


def _scene_ok(grid, patterns, h, w):
  """Check that the colour counts and the badge centres are unambiguous."""
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  ones = counts.get(1, 0)
  if counts.get(0, 0) <= ones:
    return False
  for v, n in counts.items():
    if v not in (0, 1) and n >= ones:
      return False
  found = set()
  for r in range(h):
    for c in range(w):
      if grid[r][c] != 1:
        continue
      vals = set()
      ok = True
      for dy, dx in RING:
        if not _inside(r + dy, c + dx, h, w):
          ok = False
          break
        vals.add(grid[r + dy][c + dx])
      if ok and len(vals) == 1 and vals.pop() not in (0, 1):
        found.add((r, c))
  return found == set((p[0], p[1]) for p in patterns)


def _pick_coord(lo, hi, parity=None):
  """Sample a coordinate in lo..hi, biased towards the border part of the time.

  If parity is given, only values v with v % 2 == parity are returned.
  """
  if random.random() < 0.3:
    vals = [v for v in (lo, lo + 1, hi - 1, hi)
            if parity is None or v % 2 == parity]
  else:
    vals = [v for v in range(lo, hi + 1)
            if parity is None or v % 2 == parity]
  return random.choice(vals)


def _pick_centre(h, w):
  """Sample a checker-1 centre with a symmetric border bias on both axes."""
  if random.random() < 0.5:
    cy = _pick_coord(2, h - 3)
    cx = _pick_coord(2, w - 3, cy % 2)
  else:
    cx = _pick_coord(2, w - 3)
    cy = _pick_coord(2, h - 3, cx % 2)
  return cy, cx


def _sample_scene(w, h, target):
  """Place up to `target` badges whose rays avoid everything else."""
  patterns, claimed, rays = [], set(), set()
  for _ in range(target):
    for _try in range(60):
      cy, cx = _pick_centre(h, w)
      if any(abs(cy - p[0]) + abs(cx - p[1]) < 10 for p in patterns):
        continue
      dia = _diamond(cy, cx)
      if dia & rays:
        continue
      ring = random.choice(COLOURS)
      others = [c for c in COLOURS if c != ring]
      palette = random.sample(others, random.choice([1, 1, 2, 3, 4]))
      k = random.choices([1, 2, 3, 4], weights=[2, 4, 3, 2])[0]
      segs, new_rays = [], set()
      for sy, sx in random.sample(SIDES, k):
        cells = set(_ray_cells(cy, cx, sy, sx, h, w))
        if not cells:
          # A segment pointing into a corner: visible, but launches nothing.
          if random.random() < 0.6:
            segs.append((sy, sx, random.choice(palette)))
          continue
        if cells & claimed or cells & rays or cells & new_rays:
          continue
        segs.append((sy, sx, random.choice(palette)))
        new_rays |= cells
      if not segs:
        continue
      segs.sort(key=lambda s: SIDES.index((s[0], s[1])))
      patterns.append((cy, cx, ring, segs))
      claimed |= dia
      rays |= new_rays
      break
  return patterns


def _fallback_scene(w, h):
  """Return a random single badge with one ray-launching segment."""
  options = []
  for cy in range(2, h - 2):
    for cx in range(2, w - 2):
      if (cy + cx) % 2:
        continue
      for sy, sx in SIDES:
        if _ray_cells(cy, cx, sy, sx, h, w):
          options.append((cy, cx, sy, sx))
  cy, cx, sy, sx = random.choice(options)
  ring = random.choice(COLOURS)
  seg = random.choice([c for c in COLOURS if c != ring])
  return [(cy, cx, ring, [(sy, sx, seg)])]


def generate(width=None, height=None, patterns=None, num_patterns=None):
  """Build one input/output pair.

  Args:
    width: grid width. It is sampled when None, from 12..30, or from a
      higher lower bound for 3 or 4 requested badges. Explicit values may be
      7..30.
    height: grid height. It is sampled in the same way as width when None.
      Explicit values may be 7..30.
    patterns: list of (cy, cx, ring_colour, segments). Each segment is
      (sy, sx, colour) for the diagonal side (sy, sx), with sy, sx in {-1, 1}.
      Width and height are required with this argument. Constraints:
      - The badge centre must have (cy + cx) even.
      - The ring must lie fully inside the grid.
      - Badge diamonds must be disjoint (centre L1 distance >= 10).
      - Rays may not cross other rays or other badges.
      - The scene must change at least one cell.
      Violations raise ValueError. If None, a fresh random scene is sampled.
    num_patterns: exact integer number of badges (1..4) for a random scene.
      With explicit patterns it must equal len(patterns). A ValueError is
      raised if it is not an integer, or if the badges cannot be placed
      (for example 3 or 4 badges on a small explicit grid).
  """
  for v in (width, height):
    if v is not None and (not _is_int(v) or not 7 <= v <= 30):
      raise ValueError("width/height must be integers within 7..30")
  if num_patterns is not None and (not _is_int(num_patterns) or
                                   not 1 <= num_patterns <= 4):
    raise ValueError("num_patterns must be an integer within 1..4")
  if patterns is not None:
    if width is None or height is None:
      raise ValueError("explicit patterns require width and height")
    _check_patterns(width, height, patterns)
    if num_patterns is not None and num_patterns != len(patterns):
      raise ValueError("num_patterns disagrees with len(patterns)")
    if _layout_conflict(patterns, height, width):
      raise ValueError("badges overlap or rays cross other rays/badges")
    grid, output = _render(width, height, patterns)
    if not _scene_ok(grid, patterns, height, width):
      raise ValueError("explicit scene is ambiguous (counts or centres)")
    if grid == output:
      raise ValueError("explicit scene launches no visible ray")
    return {"input": grid, "output": output}
  lo = MIN_SIDE[num_patterns] if num_patterns is not None else 12
  for _ in range(200):
    w = width if width is not None else random.randint(lo, 30)
    h = height if height is not None else random.randint(lo, 30)
    if num_patterns is not None:
      target = num_patterns
    else:
      target = random.choices([1, 2, 3, 4], weights=[3, 3, 2, 1])[0]
    pats = _sample_scene(w, h, target)
    if not pats:
      continue
    if num_patterns is not None and len(pats) != num_patterns:
      continue
    if _layout_conflict(pats, h, w):
      continue
    grid, output = _render(w, h, pats)
    if grid == output or not _scene_ok(grid, pats, h, w):
      continue
    return {"input": grid, "output": output}
  if num_patterns not in (None, 1):
    raise ValueError("could not place the requested number of badges")
  for _ in range(50):
    w = width if width is not None else random.randint(12, 30)
    h = height if height is not None else random.randint(12, 30)
    pats = _fallback_scene(w, h)
    grid, output = _render(w, h, pats)
    if grid != output and _scene_ok(grid, pats, h, w):
      return {"input": grid, "output": output}
  raise ValueError("could not construct a valid scene")


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(width=14, height=20,
               patterns=[(10, 6, 3, [(-1, 1, 8), (1, -1, 8)])]),
      generate(width=30, height=24,
               patterns=[(6, 10, 3, [(-1, -1, 2), (-1, 1, 4), (1, -1, 4),
                                     (1, 1, 2)])]),
  ]
  test = [
      generate(width=21, height=22,
               patterns=[(5, 7, 6, [(-1, -1, 2), (-1, 1, 4), (1, -1, 9)]),
                         (14, 12, 3, [(-1, 1, 6), (1, 1, 7)]),
                         (19, 5, 2, [(1, -1, 6), (1, 1, 6)])]),
  ]
  return {"train": train, "test": test}
