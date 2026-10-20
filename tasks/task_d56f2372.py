"""Generator for ARC task d56f2372 (pick the mirror-symmetric shape).

Rule: the input shows several coloured shapes on a background. Cells are
grouped by colour (a colour may consist of several connected pieces), and
each colour's tight bounding box, with only that colour kept, is a candidate.
Exactly one candidate equals its own left-right mirror; the output is that
candidate crop.

Scope: 3..6 coloured shapes with distinct colours 1..9 on a 0 background,
bounding boxes of width/height 3..9 that never overlap (one-cell gap).
Exactly one shape is left-right symmetric. Distractors are either random
asymmetric patterns or near-symmetric patterns with a single cell broken,
and shapes may be disconnected. Background is always 0. Up-down symmetry,
rotational symmetry and multi-symmetric inputs are deliberately not covered.

Copyright 2026 Ritwika Kancharla. Licensed under the Apache License 2.0.
"""

import random
import common


def _pat(rows):
  """Normalises a pattern given as strings of '0'/'1' or lists of ints."""
  out = []
  for row in rows:
    if isinstance(row, str):
      out.append([1 if ch == '1' else 0 for ch in row])
    else:
      out.append([1 if v else 0 for v in row])
  return out


def _is_symmetric(pattern):
  return all(row == row[::-1] for row in pattern)


def _is_tight(pattern):
  h, w = len(pattern), len(pattern[0])
  if not any(pattern[0]) or not any(pattern[h - 1]):
    return False
  if not any(pattern[y][0] for y in range(h)):
    return False
  if not any(pattern[y][w - 1] for y in range(h)):
    return False
  return True


def _count(pattern):
  return sum(sum(row) for row in pattern)


def _random_symmetric(h, w):
  """Random left-right symmetric tight pattern of size h x w."""
  for _ in range(200):
    p = [[0] * w for _ in range(h)]
    for y in range(h):
      for x in range((w + 1) // 2):
        if random.random() < 0.5:
          p[y][x] = 1
          p[y][w - 1 - x] = 1
    if _is_tight(p) and _count(p) >= 5 and _count(p) < h * w:
      return p
  return None


def _random_asymmetric(h, w):
  """Random tight pattern that is not left-right symmetric."""
  for _ in range(200):
    if random.random() < 0.5:
      base = _random_symmetric(h, w)
      if base is None:
        continue
      p = [row[:] for row in base]
      # Break symmetry by flipping one or two cells off the centre column.
      for _k in range(random.randint(1, 2)):
        y = random.randrange(h)
        xs = [x for x in range(w) if 2 * x != w - 1]
        x = random.choice(xs)
        p[y][x] = 1 - p[y][x]
    else:
      p = [[1 if random.random() < 0.5 else 0 for _ in range(w)]
           for _ in range(h)]
    if _is_tight(p) and not _is_symmetric(p) and _count(p) >= 4:
      return p
  return None


def _build(width, height, shapes):
  grid = common.grid(width, height, 0)
  for color, top, left, pattern in shapes:
    for dy, row in enumerate(pattern):
      for dx, v in enumerate(row):
        if v:
          grid[top + dy][left + dx] = color
  return grid


def _random_scene():
  n = random.choice([3, 4, 4, 5, 5, 6])
  colors = random.sample(range(1, 10), n)
  chosen = random.randrange(n)
  patterns = []
  for i in range(n):
    h = random.randint(3, 8)
    w = random.randint(3, 9)
    if i == chosen:
      p = _random_symmetric(h, w)
    else:
      p = _random_asymmetric(h, w)
    if p is None:
      return None
    patterns.append(p)
  width = random.randint(12, 30)
  height = random.randint(12, 30)
  # Place bounding boxes with a one-cell gap between them.
  boxes = []
  shapes = []
  order = list(range(n))
  random.shuffle(order)
  for i in order:
    p = patterns[i]
    h, w = len(p), len(p[0])
    if h > height or w > width:
      return None
    placed = False
    for _ in range(100):
      top = random.randint(0, height - h)
      left = random.randint(0, width - w)
      ok = True
      for (t2, l2, h2, w2) in boxes:
        if (top <= t2 + h2 and t2 <= top + h and
            left <= l2 + w2 and l2 <= left + w):
          ok = False
          break
      if ok:
        boxes.append((top, left, h, w))
        shapes.append((colors[i], top, left, p))
        placed = True
        break
    if not placed:
      return None
  return width, height, shapes


def generate(width=None, height=None, shapes=None):
  """Returns an input/output pair for the symmetric-shape task.

  Args:
    width: grid width.
    height: grid height.
    shapes: list of (color, top, left, pattern) where pattern is a list of
      rows of '0'/'1' strings (or 0/1 int lists) giving that colour's cells
      inside its tight bounding box. Exactly one pattern must be left-right
      symmetric.
  """
  if shapes is None:
    scene = None
    for _ in range(200):
      scene = _random_scene()
      if scene is not None:
        break
    if scene is None:
      raise RuntimeError('could not construct a scene')
    width, height, shapes = scene
  shapes = [(c, t, l, _pat(p)) for c, t, l, p in shapes]
  grid = _build(width, height, shapes)
  symmetric = [s for s in shapes if _is_symmetric(s[3])]
  if len(symmetric) != 1:
    raise ValueError('exactly one shape must be mirror-symmetric')
  color, _top, _left, pattern = symmetric[0]
  output = [[color if v else 0 for v in row] for row in pattern]
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical train/test fixtures."""
  train = [
      generate(width=17, height=22, shapes=[
          (2, 2, 1, ['00100', '01110', '11011', '01000']),
          (3, 7, 8, ['0110100', '0110110', '1011101', '0010100']),
          (4, 10, 0, ['1001', '1111', '0110', '1111', '0110', '0100']),
          (1, 15, 5, ['0001000', '0011100', '0110110', '1100011',
                      '0110110', '0001000']),
      ]),
      generate(width=16, height=21, shapes=[
          (8, 2, 2, ['01010', '00100', '01110', '11011']),
          (2, 3, 9, ['01010', '11111', '00100', '01100']),
          (1, 9, 12, ['0100', '1111', '0110']),
          (7, 11, 4, ['11011', '01010', '01111', '11111']),
          (6, 17, 7, ['00100', '11011', '11010', '00100']),
      ]),
      generate(width=19, height=21, shapes=[
          (6, 2, 2, ['11011', '01110', '01010']),
          (3, 2, 10, ['0010000', '0111110', '1101011', '0001000']),
          (1, 9, 4, ['01010', '10101', '11110']),
          (7, 13, 12, ['0110', '1011']),
          (4, 16, 4, ['01110', '01010', '11011', '10001', '01000']),
      ]),
  ]
  test = [
      generate(width=20, height=22, shapes=[
          (1, 2, 1, ['00110', '01110', '10001', '01110', '10101']),
          (2, 6, 7, ['000010000', '011111110', '001010100', '111111111',
                     '000101000', '000010000']),
          (8, 12, 14, ['00100', '11011', '01010', '01110', '11111',
                       '00100', '01110', '01000']),
          (4, 14, 2, ['01100110', '10000001', '01100110', '01011000',
                      '00111100', '11011011', '00011000']),
      ]),
  ]
  return {'train': train, 'test': test}
