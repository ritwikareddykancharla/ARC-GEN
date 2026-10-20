"""Generator for ARC task 73ccf9c2 (ARC-GEN style).

Rule: the input shows several single-colour shapes on a black background.
Shapes are built from cells that may touch only at corners, so they are found
with 8-connectivity.  Every shape except one is left-right mirror symmetric
within its own bounding box.  The output is the bounding-box crop of the one
shape that is NOT left-right symmetric.

Scope: grids 14..30 per side, 3..5 shapes of one colour (1..9) with sizes
3..7 per side, exactly one asymmetric shape.  Symmetric distractors are
randomly built mirror-symmetric 8-connected masks; the asymmetric target is
either a perturbed symmetric mask or a free random mask.  Shapes are placed
with at least one empty cell of separation so they never merge.

Copyright 2026 Ritwika Kancharla
SPDX-License-Identifier: Apache-2.0
"""

import random

import common


def _parse(pattern):
  """Converts a pattern (list of strings or 0/1 rows) to a 0/1 mask."""
  mask = []
  for row in pattern:
    if isinstance(row, str):
      mask.append([1 if ch in "#1" else 0 for ch in row])
    else:
      mask.append([1 if v else 0 for v in row])
  return mask


def _connected8(mask):
  """Returns True when all filled cells form one 8-connected component."""
  h, w = len(mask), len(mask[0])
  cells = [(r, c) for r in range(h) for c in range(w) if mask[r][c]]
  if not cells:
    return False
  seen = {cells[0]}
  stack = [cells[0]]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and mask[nr][nc]:
          if (nr, nc) not in seen:
            seen.add((nr, nc))
            stack.append((nr, nc))
  return len(seen) == len(cells)


def _crop(mask):
  """Crops a mask to its tight bounding box (None when empty)."""
  h, w = len(mask), len(mask[0])
  rows = [r for r in range(h) if any(mask[r])]
  cols = [c for c in range(w) if any(mask[r][c] for r in range(h))]
  if not rows or not cols:
    return None
  return [[mask[r][c] for c in range(cols[0], cols[-1] + 1)]
          for r in range(rows[0], rows[-1] + 1)]


def _mismatch(mask):
  """Counts cells that disagree with the left-right mirror of the mask."""
  total = 0
  for row in mask:
    w = len(row)
    for i in range(w):
      if row[i] != row[w - 1 - i]:
        total += 1
  return total


def _random_symmetric(w, h):
  """Builds a tight, 8-connected, left-right symmetric w x h mask."""
  p = random.uniform(0.35, 0.7)
  for _ in range(60):
    mask = [[0] * w for _ in range(h)]
    for r in range(h):
      for c in range((w + 1) // 2):
        if random.random() < p:
          mask[r][c] = 1
          mask[r][w - 1 - c] = 1
    cropped = _crop(mask)
    if cropped is None or len(cropped) != h or len(cropped[0]) != w:
      continue
    if not _connected8(mask):
      continue
    return mask
  return None


def _random_asymmetric(w, h):
  """Builds a tight, 8-connected mask that is NOT left-right symmetric."""
  for _ in range(60):
    if random.random() < 0.6:
      base = _random_symmetric(w, h)
      if base is None:
        continue
      mask = [row[:] for row in base]
      for _ in range(random.randint(1, 3)):
        r = random.randrange(h)
        c = random.randrange(w)
        mask[r][c] ^= 1
    else:
      p = random.uniform(0.35, 0.7)
      mask = [[1 if random.random() < p else 0 for _ in range(w)]
              for _ in range(h)]
    mask = _crop(mask)
    if mask is None or len(mask) < 2 or len(mask[0]) < 2:
      continue
    if not _connected8(mask) or _mismatch(mask) == 0:
      continue
    return mask
  return None


def _overlaps(r, c, h, w, placed):
  """True if the 1-cell-expanded box of (r,c,h,w) touches any placed box."""
  for pr, pc, pm in placed:
    ph, pw = len(pm), len(pm[0])
    if (r - 1 <= pr + ph - 1 and pr <= r + h and
        c - 1 <= pc + pw - 1 and pc <= c + w):
      return True
  return False


def _sample_scene(width=None, height=None, color=None):
  """Samples grid size, colour and a list of placed shapes."""
  for _ in range(300):
    wd = width if width is not None else random.randint(14, 30)
    ht = height if height is not None else random.randint(14, 30)
    col = color if color is not None else random.randint(1, 9)
    area = wd * ht
    max_side = max(3, min(7, min(wd, ht) // 3))
    if area < 300:
      n = 3
    elif area < 520:
      n = random.choice([3, 4])
    else:
      n = random.choice([3, 4, 5])
    target = random.randrange(n)
    masks = []
    ok = True
    for i in range(n):
      w = random.randint(3, max_side)
      h = random.randint(3, max_side)
      m = _random_asymmetric(w, h) if i == target else _random_symmetric(w, h)
      if m is None:
        ok = False
        break
      masks.append(m)
    if not ok:
      continue
    placed = []
    for m in masks:
      h, w = len(m), len(m[0])
      pos = None
      for _ in range(100):
        r = random.randint(0, ht - h)
        c = random.randint(0, wd - w)
        if not _overlaps(r, c, h, w, placed):
          pos = (r, c)
          break
      if pos is None:
        ok = False
        break
      placed.append((pos[0], pos[1], m))
    if not ok:
      continue
    filled = sum(sum(row) for _, _, m in placed for row in m)
    if filled * 10 > area * 4:
      continue
    return wd, ht, col, placed
  raise RuntimeError("could not sample a valid scene")


def generate(width=None, height=None, color=None, shapes=None):
  """Returns {"input": grid, "output": grid} for one example.

  Args:
    width: grid width (sampled when None).
    height: grid height (sampled when None).
    color: colour (1..9) shared by all shapes (sampled when None).
    shapes: list of (row, col, pattern) placements, where pattern is a list
      of strings ('#' filled, '.' empty) or 0/1 rows.  Exactly one pattern
      must be left-right asymmetric.  Sampled when None.
  """
  if shapes is None:
    width, height, color, shapes = _sample_scene(width, height, color)
  masks = [(r, c, _parse(p)) for r, c, p in shapes]
  grid = common.grid(width, height, 0)
  for r, c, m in masks:
    for dr, row in enumerate(m):
      for dc, v in enumerate(row):
        if v:
          grid[r + dr][c + dc] = color
  targets = [m for _, _, m in masks if _mismatch(m) > 0]
  if len(targets) != 1:
    raise ValueError("scene must contain exactly one asymmetric shape")
  output = [[color if v else 0 for v in row] for row in targets[0]]
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical train/test pairs from explicit latents."""
  train = [
      generate(width=21, height=21, color=2, shapes=[
          (2, 0, ["..##.##..", "...###...", "####.####", "..#####.."]),
          (5, 10, ["...#...", ".#####.", "..#.#..", "###.###", ".#...#."]),
          (13, 2, ["#...#", ".#.#.", "#####", ".#.#.", "#####"]),
          (14, 12, ["...#.", ".###.", "#.#.#", ".##.."]),
      ]),
      generate(width=23, height=23, color=1, shapes=[
          (0, 1, ["..#..", "#####", "#...#", "##.##", ".#.#."]),
          (5, 7, ["...#...", ".#####.", "..###..", "###.###"]),
          (11, 14, ["#..#", ".##.", ".##.", "#..#", ".##."]),
          (15, 4, ["..##", ".###", "###.", ".#.."]),
      ]),
      generate(width=20, height=20, color=3, shapes=[
          (3, 2, ["#...#", "#####", ".#.#."]),
          (2, 11, ["..#..", "#.#.#", "#####", "#.#.#", ".#.#."]),
          (9, 14, [".#..#.", "..##..", "######", ".#..#.", "..##.."]),
          (12, 4, ["#.....#", ".#.#.#.", "..###..", ".#####.", "....#.."]),
      ]),
  ]
  test = [
      generate(width=22, height=22, color=8, shapes=[
          (1, 2, [".####.", "..##..", ".#..#.", "######", "..##..", ".#..#."]),
          (1, 12, ["#..#", ".##.", "####", "#..#"]),
          (8, 13, ["..#.#", "#####", "..#.#", ".###.", "#.#.#", "#####",
                   ".###."]),
          (14, 3, ["..##..", ".#..#.", "######", "#.##.#"]),
      ]),
  ]
  return {"train": train, "test": test}
