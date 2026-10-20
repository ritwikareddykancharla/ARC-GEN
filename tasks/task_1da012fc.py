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

"""ARC task 1da012fc: recolour shapes from a miniature colour key.

Rule: the input holds one solid rectangle of colour 5 (the key) containing
isolated single cells of distinct colours (dots), plus several shapes of one
shared colour elsewhere on a black background. The key is a scaled-down map
of the shape layout. Each dot's position, normalised inside the key
rectangle, is matched to the shape whose bounding-box centre, normalised
inside the bounding box of all shapes, lies at the corresponding position.
The matching minimises total squared distance. Each shape is recoloured with
its dot's colour. The key itself is left unchanged.

Scope: 2..5 shapes laid out on a compressed 2x2 / 2x3 / 3x2 / 3x3 slot
lattice with random jitter, gaps and cell sizes. The shapes are random
8-connected sprites, often mirror-symmetric, and some connect only
diagonally. The key has random size (5..10 per side) and sits left, right,
above or below the shape field. Dot colours, shape colour and margins are
random. The key colour 5 and the background 0 are fixed, as in the task.
"""

import itertools
import random

import common

_PALETTE = [1, 2, 3, 4, 6, 7, 8, 9]


def _cells(sprite):
  return [(r, c) for r, row in enumerate(sprite)
          for c, ch in enumerate(row) if ch == '#']


def _connected8(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nb = (r + dr, c + dc)
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
  return len(seen) == len(cells)


def _random_sprite():
  for _ in range(200):
    h = random.randint(2, 4)
    w = random.randint(2, 5)
    sym = random.random() < 0.7
    rows = []
    for _ in range(h):
      if sym:
        half = [random.random() < 0.6 for _ in range((w + 1) // 2)]
        row = half + half[:w // 2][::-1]
      else:
        row = [random.random() < 0.6 for _ in range(w)]
      rows.append(row)
    cells = [(r, c) for r in range(h) for c in range(w) if rows[r][c]]
    if len(cells) < 3:
      continue
    if any(not any(rows[r]) for r in range(h)):
      continue
    if any(not any(rows[r][c] for r in range(h)) for c in range(w)):
      continue
    if not _connected8(cells):
      continue
    if len(cells) == h * w and random.random() < 0.8:
      continue
    return [''.join('#' if v else '.' for v in row) for row in rows]
  return ['.#.', '###', '.#.']


def _d2(a, b):
  return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _assignment_margin(key, dots, shapes):
  """Cost gap between the intended pairing (shape j <-> dot j) and the rest."""
  kr, kc, kh, kw = key
  dpos = [((r - kr) / max(1, kh - 1), (c - kc) / max(1, kw - 1))
          for r, c, _ in dots]
  boxes = [(t, l, t + len(s) - 1, l + len(s[0]) - 1) for t, l, s, _ in shapes]
  y0 = min(b[0] for b in boxes)
  x0 = min(b[1] for b in boxes)
  y1 = max(b[2] for b in boxes)
  x1 = max(b[3] for b in boxes)
  spos = [(((b[0] + b[2]) / 2 - y0) / max(1, y1 - y0),
           ((b[1] + b[3]) / 2 - x0) / max(1, x1 - x0)) for b in boxes]
  n = len(shapes)
  ident = sum(_d2(spos[j], dpos[j]) for j in range(n))
  other = None
  for perm in itertools.permutations(range(n)):
    if perm == tuple(range(n)):
      continue
    cost = sum(_d2(spos[j], dpos[perm[j]]) for j in range(n))
    other = cost if other is None else min(other, cost)
  return other - ident


def _axis(k, parts, allow_border=False):
  """Key coordinates for lattice lines, spaced >= 2; optionally include border."""
  low, high = (0,k-1) if allow_border else (1,k-2)
  if parts == 1:
    return [random.randint(low, high)]
  span_min = 2 * (parts - 1)
  lo = random.randint(low, high - span_min)
  hi = random.randint(lo + span_min, high)
  return [lo + round(i * (hi - lo) / (parts - 1)) for i in range(parts)]


def _sample_scene(num_shapes=None, requested_width=None, requested_height=None, requested_colour=None):
  for _ in range(2000):
    n = num_shapes if num_shapes else random.choice([2, 3, 3, 4, 4, 5, 5])
    rr, cc = random.choice([(2, 2), (2, 3), (3, 2), (3, 3)])
    if rr * cc < n:
      continue
    slots = random.sample([(r, c) for r in range(rr) for c in range(cc)], n)
    used_r = sorted({s[0] for s in slots})
    used_c = sorted({s[1] for s in slots})
    slots = [(used_r.index(r), used_c.index(c)) for r, c in slots]
    nr, nc = len(used_r), len(used_c)
    sprites = [_random_sprite() for _ in range(n)]
    mh = max(len(s) for s in sprites)
    mw = max(len(s[0]) for s in sprites)
    cell_h = mh + 1 + random.randint(0, 2)
    cell_w = mw + 1 + random.randint(0, 2)
    reg_h = nr * cell_h - 1
    reg_w = nc * cell_w - 1
    kh = random.randint(max(5, 2 * nr + 1), 10)
    kw = random.randint(max(5, 2 * nc + 1), 10)
    drows = _axis(kh, nr, random.random() < 0.25)
    dcols = _axis(kw, nc, random.random() < 0.25)
    gap = random.randint(1, 3)
    side = random.choice(['left', 'right', 'top', 'bottom'])
    if side in ('left', 'right'):
      cont_h = max(reg_h, kh)
      cont_w = reg_w + gap + kw
      reg_top = random.randint(0, cont_h - reg_h)
      key_top = random.randint(0, cont_h - kh)
      if side == 'right':
        reg_left, key_left = 0, reg_w + gap
      else:
        key_left, reg_left = 0, kw + gap
    else:
      cont_w = max(reg_w, kw)
      cont_h = reg_h + gap + kh
      reg_left = random.randint(0, cont_w - reg_w)
      key_left = random.randint(0, cont_w - kw)
      if side == 'bottom':
        reg_top, key_top = 0, reg_h + gap
      else:
        key_top, reg_top = 0, kh + gap
    if requested_height is not None and requested_height < cont_h:
      continue
    if requested_width is not None and requested_width < cont_w:
      continue
    mt, mb, ml, mr = [random.randint(0, 2) for _ in range(4)]
    if requested_height is not None:
      mt = random.randint(0, requested_height-cont_h)
      mb = requested_height-cont_h-mt
    if requested_width is not None:
      ml = random.randint(0, requested_width-cont_w)
      mr = requested_width-cont_w-ml
    height = cont_h + mt + mb
    width = cont_w + ml + mr
    if height > 30 or width > 30:
      continue
    key = (key_top + mt, key_left + ml, kh, kw)
    shape_color = requested_colour if requested_colour is not None else random.choice(_PALETTE)
    colors = [shape_color] + random.sample([c for c in _PALETTE if c != shape_color], n)
    dots, shapes = [], []
    for i, (r, c) in enumerate(slots):
      dots.append((key[0] + drows[r], key[1] + dcols[c], colors[i + 1]))
      s = sprites[i]
      h, w = len(s), len(s[0])
      top = mt + reg_top + r * cell_h + random.randint(0, cell_h - 1 - h)
      left = ml + reg_left + c * cell_w + random.randint(0, cell_w - 1 - w)
      shapes.append((top, left, s, colors[i + 1]))
    sizes = [len(_cells(s)) for s in sprites]
    key_cells = kh * kw - n
    if max(sizes) >= key_cells:
      continue
    zeros = height * width - kh * kw - sum(sizes)
    if zeros <= key_cells or zeros <= sum(sizes):
      continue
    if _assignment_margin(key, dots, shapes) < 0.1:
      continue
    return width, height, key, dots, shape_color, shapes
  raise RuntimeError('could not sample a valid scene')


def generate(width=None, height=None, key=None, dots=None, shape_color=None,
             shapes=None, num_shapes=None):
  """Returns an input/output pair for task 1da012fc.

  Args:
    width: grid width (columns).
    height: grid height (rows).
    key: (top, left, height, width) of the colour-5 key rectangle.
    dots: list of (row, col, colour) key dots (absolute positions).
    shape_color: shared input colour of all shapes.
    shapes: list of (top, left, sprite, out_colour); sprite is a list of
      strings using '#' for filled cells, and out_colour is the colour the
      shape takes in the output (the colour of its matching dot).
    num_shapes: optional shape count (2..5) for random sampling only.
  If key is None a fresh random scene is sampled, respecting width/height
  and shape_color if provided. Key dots may lie on the border, as in train 1.
  """
  if key is None:
    if dots is not None or shapes is not None:
      raise ValueError('explicit dots/shapes require an explicit key')
    if num_shapes is not None and num_shapes not in range(2,6):
      raise ValueError('num_shapes must be 2..5')
    if shape_color is not None and shape_color not in _PALETTE:
      raise ValueError('shape_color must differ from background 0 and key colour 5')
    if any(v is not None and not 10 <= v <= 30 for v in (width,height)):
      raise ValueError('random canvas dimensions must be 10..30')
    width, height, key, dots, shape_color, shapes = _sample_scene(num_shapes,width,height,shape_color)
  elif any(v is None for v in (width,height,dots,shape_color,shapes)):
    raise ValueError('explicit key requires dimensions, dots, colour and shapes')
  grid = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  kr, kc, kh, kw = key
  for r in range(kr, kr + kh):
    for c in range(kc, kc + kw):
      grid[r][c] = 5
      out[r][c] = 5
  for r, c, col in dots:
    grid[r][c] = col
    out[r][c] = col
  for top, left, sprite, col in shapes:
    for dr, dc in _cells(sprite):
      grid[top + dr][left + dc] = shape_color
      out[top + dr][left + dc] = col
  return {'input': grid, 'output': out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=20, height=14, key=(6, 1, 6, 6),
               dots=[(6, 2, 2), (8, 4, 4), (10, 2, 6), (10, 5, 3)],
               shape_color=1,
               shapes=[(1, 9, ['####', '.##.'], 2),
                       (4, 13, ['.#.#.', '#####', '.#.#.'], 4),
                       (9, 8, ['.##.', '####', '.##.'], 6),
                       (9, 16, ['.#.', '###', '.#.'], 3)]),
      generate(width=22, height=19, key=(0, 16, 9, 6),
               dots=[(1, 17, 2), (4, 19, 3), (7, 17, 4)],
               shape_color=8,
               shapes=[(1, 1, ['######', '.####.', '##..##'], 2),
                       (6, 8, ['.###.', '#####', '#####', '.#.#.'], 3),
                       (13, 3, ['#...#', '#####', '.###.', '##.##'], 4)]),
  ]
  test = [
      generate(width=25, height=19, key=(9, 16, 10, 8),
               dots=[(10, 17, 3), (10, 21, 4), (13, 19, 8), (16, 17, 1),
                     (16, 21, 6)],
               shape_color=2,
               shapes=[(1, 2, ['.##.', '####', '.##.'], 3),
                       (1, 8, ['.###.', '#.#.#', '..#..'], 4),
                       (7, 5, ['.###.', '##.##', '.###.'], 8),
                       (13, 2, ['.#.', '###', '.#.'], 1),
                       (13, 9, ['.#..#.', '######', '..##..'], 6)]),
  ]
  return {'train': train, 'test': test}
