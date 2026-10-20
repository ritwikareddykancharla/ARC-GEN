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

"""ARC task 8a6d367c: complete a coarse glyph inside a frame.

Rule: a row of small glyphs sits near the top of the grid. All glyphs share
one bounding-box size, and each glyph touches all four sides of that box.
Each glyph has its own colour and may be split into several pieces. Lower
down there is a rectangular frame drawn in one colour. Its interior is a
coarse grid of cells, each (interior size / glyph size) pixels. A few cells
are solidly painted in one fill colour. These cells are partial evidence:
they are filled cells of exactly one glyph. The output is the frame cropped
out of the grid, with that unique glyph drawn inside it at cell scale.
Filled glyph cells take the fill colour and empty glyph cells take the
background colour.

Scope:
  * The background defaults to 8, as in every example. It can be overridden.
  * Canvases are sampled up to 30x30. Both tight and roomy layouts are drawn,
    so 21x27 canvases like the fixtures are inside the support. The glyph row
    offset, the glyph gaps (1 or 2 columns), the frame position and the
    margins all vary.
  * Glyph sizes are 3x3, 4x3 and 3x4, as in the fixtures. 4x4 is a synthetic
    extension.
  * Random cell sizes are 2..4 per axis, as in the fixtures. Non-square cells
    are a synthetic extension. Cell sizes 1 and 5..6 are available only on
    request (cell_h / cell_w) and are also synthetic extensions.
  * There are 2..5 glyphs by default (2..6 on request), each with a full
    bounding box and a distinct colour. Some distractors are small mutations
    of the target, so they compete closely with it.
  * By default there are 2..4 hint cells. They form a proper subset of the
    target and are contained in no other glyph. Most samples prefer hint sets
    in which every hint cell is also filled in some distractor, so no single
    hint identifies the target on its own. Requesting num_hints=1 selects
    an easier regime: that one cell must identify the target by itself.
  * Structural guards in both modes: every glyph and the total hint area are
    strictly smaller than the frame border, so the frame is the largest
    single-colour object, and the background is strictly the most common
    colour.
  * Not supported: frames above or beside the glyph row, glyphs of mixed
    sizes, several fill colours, or hint blocks that are not whole cells.
"""

import itertools
import random

import common

_SHAPES = ((3, 3), (3, 3), (3, 3), (4, 3), (4, 3), (3, 4), (3, 4), (3, 4),
           (4, 4))
_CELLS = (2, 3, 4)


def _is_int(v):
  """True for a real Python int (bool, float and numpy scalars excluded)."""
  return type(v) is int


def _render(width, height, bg, glyphs, colors, glyph_cols, glyph_top,
            frame_top, frame_left, cell_h, cell_w, frame_color, fill_color,
            target, hints):
  """Draw the input and output grids from the latent scene."""
  ph, pw = len(glyphs[0]), len(glyphs[0][0])
  fh, fw = ph * cell_h + 2, pw * cell_w + 2
  grid = common.grid(width, height, bg)
  for pat, col, x0 in zip(glyphs, colors, glyph_cols):
    for r in range(ph):
      for c in range(pw):
        if pat[r][c] == '1':
          grid[glyph_top + r][x0 + c] = col
  for r in range(fh):
    for c in range(fw):
      if r in (0, fh - 1) or c in (0, fw - 1):
        grid[frame_top + r][frame_left + c] = frame_color
  for (i, j) in hints:
    for r in range(cell_h):
      for c in range(cell_w):
        y = frame_top + 1 + i * cell_h + r
        x = frame_left + 1 + j * cell_w + c
        grid[y][x] = fill_color
  out = common.grid(fw, fh, frame_color)
  pat = glyphs[target]
  for r in range(1, fh - 1):
    for c in range(1, fw - 1):
      i, j = (r - 1) // cell_h, (c - 1) // cell_w
      out[r][c] = fill_color if pat[i][j] == '1' else bg
  return {'input': grid, 'output': out}


def _cells(pat):
  return {(r, c) for r in range(len(pat)) for c in range(len(pat[0]))
          if pat[r][c] == '1'}


def _full_box(p):
  """True if the glyph touches all four sides of its bounding box."""
  return ('1' in p[0] and '1' in p[-1] and any(r[0] == '1' for r in p) and
          any(r[-1] == '1' for r in p))


def _pattern_ok(p):
  """Random-mode glyph validity: full box, not solid, at least 3 cells."""
  cnt = sum(r.count('1') for r in p)
  return 3 <= cnt < len(p) * len(p[0]) and _full_box(p)


def _rand_pattern(ph, pw, min_cells=3):
  """Return a random non-solid glyph with a full ph x pw bounding box."""
  area = ph * pw
  hi = max(0.75, min(0.95, (min_cells + 1.0) / area))
  for _ in range(200):
    dens = random.uniform(0.4, hi)
    p = tuple(''.join('1' if random.random() < dens else '0'
                      for _ in range(pw)) for _ in range(ph))
    cnt = sum(r.count('1') for r in p)
    if cnt < max(min_cells, 0.35 * area):
      continue
    if _pattern_ok(p):
      return p
  return None


def _mutate(pat):
  """Return a close distractor: the pattern with one to three cells flipped."""
  ph, pw = len(pat), len(pat[0])
  for _ in range(50):
    rows = [list(r) for r in pat]
    for _ in range(random.randint(1, 3)):
      r, c = random.randrange(ph), random.randrange(pw)
      rows[r][c] = '1' if rows[r][c] == '0' else '0'
    p = tuple(''.join(r) for r in rows)
    if p != pat and _pattern_ok(p):
      return p
  return None


def _check_scene(s, bg):
  """Return an error string if the latent scene is invalid or ambiguous."""
  g = s['glyphs']
  n = len(g)
  if n < 2:
    return 'need at least two glyphs'
  ph = len(g[0])
  pw = len(g[0][0]) if ph else 0
  if ph < 1 or pw < 1:
    return 'empty glyph'
  for p in g:
    if len(p) != ph or any(len(r) != pw for r in p):
      return 'glyphs must share one size'
    if any(ch not in '01' for r in p for ch in r):
      return 'glyph rows must be 0/1 strings'
    if not _full_box(p):
      return 'each glyph must fill its whole bounding box'
  if len(set(g)) != n:
    return 'glyph patterns must be distinct'
  w, h = s['width'], s['height']
  if not (1 <= w <= 30 and 1 <= h <= 30):
    return 'grid must be 1..30 per side'
  cols = list(s['colors'])
  if len(cols) != n:
    return 'need one colour per glyph'
  pal = [bg, s['frame_color'], s['fill_color']] + cols
  if any(not 0 <= c <= 9 for c in pal) or len(set(pal)) != len(pal):
    return 'bg, frame, fill and glyph colours must be distinct colours 0..9'
  gc = list(s['glyph_cols'])
  if len(gc) != n or gc[0] < 0 or gc[-1] + pw > w:
    return 'glyph columns out of range'
  if any(gc[k + 1] < gc[k] + pw + 1 for k in range(n - 1)):
    return 'glyphs must be ordered and separated by at least one column'
  gt = s['glyph_top']
  ch, cw = s['cell_h'], s['cell_w']
  if gt < 0 or ch < 1 or cw < 1:
    return 'bad glyph_top or cell size'
  fh, fw = ph * ch + 2, pw * cw + 2
  ft, fl = s['frame_top'], s['frame_left']
  if ft < gt + ph + 1:
    return 'frame must lie below the glyph row with a blank gap'
  if fl < 0 or fl + fw > w or ft + fh > h:
    return 'frame out of bounds'
  t = s['target']
  if not 0 <= t < n:
    return 'target out of range'
  hs = [tuple(x) for x in s['hints']]
  hset = set(hs)
  if not hs or len(hset) != len(hs):
    return 'hints must be non-empty and distinct'
  if not hset < _cells(g[t]):
    return 'hints must be a proper subset of the target glyph'
  for k in range(n):
    if k != t and hset <= _cells(g[k]):
      return 'hints are consistent with more than one glyph'
  border = 2 * fw + 2 * (fh - 2)
  hint_area = len(hs) * ch * cw
  if hint_area >= border:
    return 'hint area must stay smaller than the frame border'
  sizes = [len(_cells(p)) for p in g]
  if max(sizes) >= border:
    return 'every glyph must have fewer cells than the frame border'
  bg_count = w * h - border - hint_area - sum(sizes)
  if bg_count <= max([border, hint_area] + sizes):
    return 'background must be the most common colour'
  return None


def _choose_hints(glyphs, target, ch, cw, fh, fw, num_hints):
  """Pick an identifying hint subset of the target glyph, or None."""
  tcells = sorted(_cells(glyphs[target]))
  others = [_cells(q) for k, q in enumerate(glyphs) if k != target]
  border = 2 * fw + 2 * (fh - 2)
  if num_hints is not None:
    sizes = [num_hints]
  else:
    sizes = list(range(2, min(len(tcells) - 1, 4) + 1))
  by_size = {}
  for k in sizes:
    if k >= len(tcells) or k * ch * cw >= border:
      continue
    for sub in itertools.combinations(tcells, k):
      sset = set(sub)
      if all(not sset <= o for o in others):
        by_size.setdefault(k, []).append(sub)
  if not by_size:
    return None
  strong = {}
  for k, subs in by_size.items():
    good = [sub for sub in subs
            if all(any(c in o for o in others) for c in sub)]
    if good:
      strong[k] = good
  pool = strong if strong and random.random() < 0.75 else by_size
  k = random.choice(sorted(pool))
  return list(random.choice(pool[k]))


def _feasible_combos(cell_h, cell_w, glyph_h, glyph_w, num_glyphs,
                     num_hints):
  """Return the (glyph shape -> [(cell_h, cell_w)]) options that can fit."""
  chs = (cell_h,) if cell_h is not None else _CELLS
  cws = (cell_w,) if cell_w is not None else _CELLS
  n0 = 2 if num_glyphs is None else num_glyphs
  combos = {}
  for (ph, pw) in sorted(set(_SHAPES)):
    if glyph_h is not None and ph != glyph_h:
      continue
    if glyph_w is not None and pw != glyph_w:
      continue
    if n0 * pw + (n0 - 1) + 2 > 30:
      continue
    opts = []
    for ch in chs:
      for cw in cws:
        fh, fw = ph * ch + 2, pw * cw + 2
        if 1 + ph + 1 + fh > 30 or fw + 2 > 30:
          continue
        border = 2 * fw + 2 * (fh - 2)
        if num_hints is not None and (num_hints * ch * cw >= border or
                                      num_hints > ph * pw - 2):
          continue
        opts.append((ch, cw))
    if opts:
      combos[(ph, pw)] = opts
  shape_list = [s for s in _SHAPES if s in combos]
  return combos, shape_list


def _sample_scene(bg, combos, shape_list, cell_w, num_glyphs, num_hints,
                  frame_color, fill_color):
  """Sample an unambiguous latent scene that honours the given controls."""
  min_cells = 3 if num_hints is None else max(3, num_hints + 1)
  for _ in range(400):
    ph, pw = random.choice(shape_list)
    opts = combos[(ph, pw)]
    ch = random.choice(sorted({a for a, _ in opts}))
    cws = [b for a, b in opts if a == ch]
    if cell_w is None and ch in cws and random.random() < 0.6:
      cw = ch
    else:
      cw = random.choice(cws)
    n = num_glyphs if num_glyphs is not None else random.randint(2, 5)
    glyph_top = random.choice((1, 1, 1, 2))
    gaps = [1 if random.random() < 0.75 else 2 for _ in range(n - 1)]
    span = n * pw + sum(gaps)
    fh, fw = ph * ch + 2, pw * cw + 2
    min_ft = glyph_top + ph + 1
    lo_w = max(fw + 2, span + 2, 10)
    if min_ft + fh > 30 or lo_w > 30:
      continue
    hi_w = 30 if random.random() < 0.5 else min(30, lo_w + 5)
    width = random.randint(lo_w, hi_w)
    if random.random() < 0.5:
      hi_ft = 30 - fh
    else:
      hi_ft = min(30 - fh, min_ft + 3)
    frame_top = random.randint(min_ft, hi_ft)
    lo_h = max(frame_top + fh, 10)
    hi_h = 30 if random.random() < 0.5 else min(30, lo_h + 4)
    height = random.randint(lo_h, hi_h)
    start = random.randint(1, width - 1 - span)
    glyph_cols = [start]
    for gap in gaps:
      glyph_cols.append(glyph_cols[-1] + pw + gap)
    if random.random() < 0.2:
      frame_left = random.randint(0, width - fw)
    else:
      frame_left = random.randint(1, width - fw - 1)
    pal = [c for c in range(10) if c not in (bg, frame_color, fill_color)]
    random.shuffle(pal)
    fc = frame_color if frame_color is not None else pal.pop()
    fl = fill_color if fill_color is not None else pal.pop()
    if len(pal) < n:
      continue
    colors = pal[:n]
    tpat = _rand_pattern(ph, pw, min_cells)
    if tpat is None:
      continue
    target = random.randrange(n)
    glyphs = [None] * n
    glyphs[target] = tpat
    ok = True
    for k in range(n):
      if k == target:
        continue
      for _ in range(30):
        p = _mutate(tpat) if random.random() < 0.5 else _rand_pattern(ph, pw)
        if (p is not None and p not in glyphs and
            not _cells(tpat) <= _cells(p)):
          glyphs[k] = p
          break
      else:
        ok = False
        break
    if not ok:
      continue
    hints = _choose_hints(glyphs, target, ch, cw, fh, fw, num_hints)
    if hints is None:
      continue
    scene = dict(width=width, height=height, glyphs=glyphs, colors=colors,
                 glyph_cols=glyph_cols, glyph_top=glyph_top,
                 frame_top=frame_top, frame_left=frame_left, cell_h=ch,
                 cell_w=cw, frame_color=fc, fill_color=fl, target=target,
                 hints=hints)
    if _check_scene(scene, bg) is None:
      return scene
  raise ValueError('could not sample a scene for the requested controls')


def _norm_glyph(pat):
  """Normalise a glyph given as '0'/'1' strings or 0/1 int rows."""
  if not isinstance(pat, (list, tuple)) or not pat:
    raise ValueError('glyph must be a non-empty list of rows')
  rows = []
  for row in pat:
    if not isinstance(row, (str, list, tuple)) or not row:
      raise ValueError('glyph rows must be non-empty strings or cell lists')
    chars = []
    for v in row:
      if isinstance(v, str) and v in ('0', '1'):
        chars.append(v)
      elif _is_int(v) and v in (0, 1):
        chars.append(str(v))
      else:
        raise ValueError('glyph cells must be 0/1')
    rows.append(''.join(chars))
  return tuple(rows)


def generate(width=None, height=None, glyphs=None, colors=None,
             glyph_cols=None, glyph_top=None, frame_top=None,
             frame_left=None, cell_h=None, cell_w=None, frame_color=None,
             fill_color=None, target=None, hints=None, bg=None,
             glyph_h=None, glyph_w=None, num_glyphs=None, num_hints=None):
  """Returns an input/output pair.

  Args:
    width: grid width in columns (explicit mode only).
    height: grid height in rows (explicit mode only).
    glyphs: list of same-sized glyph patterns, each a list of '0'/'1' rows.
      If this is given, the scene is explicit and all scene arguments
      (width, height, colors, glyph_cols, frame_top, frame_left, cell_h,
      cell_w, frame_color, fill_color, target, hints) are required. Explicit
      glyphs may have any shared size, provided each fills its bounding box
      and has fewer cells than the frame border.
    colors: distinct colour for each glyph (explicit mode only).
    glyph_cols: left column of each glyph, ascending (explicit mode only).
    glyph_top: top row shared by all glyphs (explicit mode, default 1).
    frame_top: top row of the frame's outer border (explicit mode only).
    frame_left: left column of the frame's outer border (explicit mode only).
    cell_h: height of one coarse interior cell. Random mode accepts 1..6
      (default 2..4).
    cell_w: width of one coarse interior cell. Random mode accepts 1..6
      (default 2..4).
    frame_color: colour of the frame border. Honoured in both modes.
    fill_color: colour of the hint blocks and of the output glyph. Honoured
      in both modes.
    target: index of the glyph that the hints identify (explicit mode only).
    hints: list of (row, col) coarse cells painted with fill_color
      (explicit mode only).
    bg: background colour (default 8). Honoured in both modes.
    glyph_h: glyph rows. In random mode this must be 3 or 4. In explicit
      mode it must agree with glyphs.
    glyph_w: glyph columns. In random mode this must be 3 or 4. In explicit
      mode it must agree with glyphs.
    num_glyphs: number of glyphs. In random mode this must be 2..6. In
      explicit mode it must agree with glyphs.
    num_hints: number of hint cells. In random mode this must be 1..6
      (default 2..4). In explicit mode it must agree with hints.

  All scalar controls must be Python ints (bools and floats are rejected).
  In random mode (glyphs is None), passing any explicit-only argument raises
  ValueError instead of being silently ignored. Controls whose geometry or
  hint area cannot fit raise ValueError before sampling.
  """
  bg = 8 if bg is None else bg
  if not _is_int(bg) or not 0 <= bg <= 9:
    raise ValueError('bg must be an int 0..9')
  if glyphs is None:
    explicit_only = dict(width=width, height=height, colors=colors,
                         glyph_cols=glyph_cols, glyph_top=glyph_top,
                         frame_top=frame_top, frame_left=frame_left,
                         target=target, hints=hints)
    given = sorted(k for k, v in explicit_only.items() if v is not None)
    if given:
      raise ValueError('arguments %s need an explicit glyphs scene' % given)
    for name, v in (('glyph_h', glyph_h), ('glyph_w', glyph_w)):
      if v is not None and (not _is_int(v) or v not in (3, 4)):
        raise ValueError('%s must be 3 or 4' % name)
    for name, v in (('cell_h', cell_h), ('cell_w', cell_w)):
      if v is not None and (not _is_int(v) or not 1 <= v <= 6):
        raise ValueError('%s must be an int 1..6' % name)
    if num_glyphs is not None and (not _is_int(num_glyphs) or
                                   not 2 <= num_glyphs <= 6):
      raise ValueError('num_glyphs must be an int 2..6')
    if num_hints is not None and (not _is_int(num_hints) or
                                  not 1 <= num_hints <= 6):
      raise ValueError('num_hints must be an int 1..6')
    for name, v in (('frame_color', frame_color), ('fill_color', fill_color)):
      if v is not None and (not _is_int(v) or not 0 <= v <= 9 or v == bg):
        raise ValueError('%s must be an int 0..9 and differ from bg' % name)
    if (frame_color is not None and fill_color is not None and
        frame_color == fill_color):
      raise ValueError('frame_color and fill_color must differ')
    combos, shape_list = _feasible_combos(cell_h, cell_w, glyph_h, glyph_w,
                                          num_glyphs, num_hints)
    if not shape_list:
      raise ValueError('requested controls cannot fit in a 30x30 grid')
    scene = _sample_scene(bg, combos, shape_list, cell_w, num_glyphs,
                          num_hints, frame_color, fill_color)
  else:
    required = dict(width=width, height=height, colors=colors,
                    glyph_cols=glyph_cols, frame_top=frame_top,
                    frame_left=frame_left, cell_h=cell_h, cell_w=cell_w,
                    frame_color=frame_color, fill_color=fill_color,
                    target=target, hints=hints)
    missing = sorted(k for k, v in required.items() if v is None)
    if missing:
      raise ValueError('explicit scene is missing %s' % missing)
    gt = 1 if glyph_top is None else glyph_top
    scalars = dict(width=width, height=height, glyph_top=gt,
                   frame_top=frame_top, frame_left=frame_left, cell_h=cell_h,
                   cell_w=cell_w, frame_color=frame_color,
                   fill_color=fill_color, target=target)
    bad = sorted(k for k, v in scalars.items() if not _is_int(v))
    if bad:
      raise ValueError('arguments %s must be ints' % bad)
    if not isinstance(colors, (list, tuple)) or not all(
        _is_int(c) for c in colors):
      raise ValueError('colors must be ints')
    if not isinstance(glyph_cols, (list, tuple)) or not all(
        _is_int(c) for c in glyph_cols):
      raise ValueError('glyph_cols must be ints')
    if not isinstance(hints, (list, tuple)):
      raise ValueError('hints must be a list of coordinate pairs')
    hint_list = []
    for x in hints:
      if (not isinstance(x, (list, tuple)) or len(x) != 2 or
          not all(_is_int(v) for v in x)):
        raise ValueError('each hint must be a (row, col) pair of ints')
      hint_list.append(tuple(x))
    if not isinstance(glyphs, (list, tuple)) or not glyphs:
      raise ValueError('glyphs must be non-empty patterns')
    for name, v in (('glyph_h', glyph_h), ('glyph_w', glyph_w),
                    ('num_glyphs', num_glyphs), ('num_hints', num_hints)):
      if v is not None and not _is_int(v):
        raise ValueError('%s must be an int' % name)
    pats = [_norm_glyph(p) for p in glyphs]
    if glyph_h is not None and glyph_h != len(pats[0]):
      raise ValueError('glyph_h disagrees with glyphs')
    if glyph_w is not None and glyph_w != len(pats[0][0]):
      raise ValueError('glyph_w disagrees with glyphs')
    if num_glyphs is not None and num_glyphs != len(pats):
      raise ValueError('num_glyphs disagrees with glyphs')
    if num_hints is not None and num_hints != len(hint_list):
      raise ValueError('num_hints disagrees with hints')
    scene = dict(width=width, height=height, glyphs=pats, colors=list(colors),
                 glyph_cols=list(glyph_cols), glyph_top=gt,
                 frame_top=frame_top, frame_left=frame_left, cell_h=cell_h,
                 cell_w=cell_w, frame_color=frame_color,
                 fill_color=fill_color, target=target, hints=hint_list)
  err = _check_scene(scene, bg)
  if err:
    raise ValueError(err)
  return _render(bg=bg, **scene)


def validate():
  """Reconstructs the canonical examples from explicit latent parameters."""
  train = [
      generate(width=21, height=27,
               glyphs=[['101', '010', '011'], ['110', '010', '111'],
                       ['100', '111', '001'], ['110', '011', '100'],
                       ['101', '111', '100']],
               colors=[1, 2, 3, 4, 6], glyph_cols=[1, 5, 9, 13, 17],
               glyph_top=1, frame_top=9, frame_left=3, cell_h=4, cell_w=4,
               frame_color=9, fill_color=5, target=3,
               hints=[(0, 0), (0, 1), (1, 2)]),
      generate(width=21, height=27,
               glyphs=[['111', '001', '110', '011'],
                       ['101', '110', '011', '001'],
                       ['010', '110', '011', '010'],
                       ['110', '001', '111', '001'],
                       ['110', '100', '011', '011']],
               colors=[1, 2, 4, 9, 6], glyph_cols=[1, 5, 9, 13, 17],
               glyph_top=1, frame_top=9, frame_left=3, cell_h=3, cell_w=3,
               frame_color=3, fill_color=0, target=0,
               hints=[(0, 0), (0, 1), (0, 2)]),
      generate(width=21, height=27,
               glyphs=[['1111', '0110', '1111'], ['1000', '1111', '0101']],
               colors=[1, 2], glyph_cols=[2, 7], glyph_top=1, frame_top=7,
               frame_left=2, cell_h=2, cell_w=2, frame_color=4, fill_color=3,
               target=0, hints=[(2, 2), (2, 3)]),
  ]
  test = [
      generate(width=21, height=27,
               glyphs=[['1011', '1010', '0110'], ['0010', '1111', '1010'],
                       ['1010', '0111', '1001'], ['1101', '0101', '0111']],
               colors=[2, 1, 6, 4], glyph_cols=[1, 6, 11, 16], glyph_top=1,
               frame_top=13, frame_left=2, cell_h=4, cell_w=4, frame_color=9,
               fill_color=7, target=2, hints=[(0, 2), (2, 3)]),
  ]
  return {'train': train, 'test': test}
