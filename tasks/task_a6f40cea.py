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

"""ARC task a6f40cea: look through a window at hidden rectangle outlines.

Rule:
  The input has one large frame, a rectangle drawn only as its 1-cell
  border. Its interior is the background or a separate fill colour. Other
  rectangle outlines cross the frame. The frame hides every part of them
  that lies inside the frame box. Each outline is either one colour, or two
  colours alternating on the absolute (y + x) checkerboard parity. Visible
  pieces that share a colour set belong to the same outline. That outline's
  full rectangle is the bounding box of its pieces. The output is the frame
  interior, with each outline's border redrawn where it passes through the
  window.

Scope:
  * Random grids are 16..30 per side by default. Requested sizes may be
    10..30. Three outlines need every given side >= 12, and four outlines
    need every given side >= 14. Frames are 5..22 per side, so windows are
    3..20 per side. Grids and frames beyond the fixtures are synthetic
    extensions.
  * By default each scene has 1..3 crossing outlines; num_outlines may
    request 1..4. Outline boxes are proposed in two ways:
    - generic boxes that overlap the window;
    - deliberate splits that span the whole frame vertically or
      horizontally, so the frame cuts them into two separate pieces (the
      mechanism of train pair 2). This works for any frame size.
    Each proposal is two-colour with probability 0.4 when colours allow.
    The realised two-colour rate is lower because of extra checks.
  * Optional distractors are smaller frame-coloured boxes, up to 7x8. Their
    border is strictly shorter than the frame's, and their centre may be
    filled. All of them sit on one side of the frame.
  * Optional decoys are complete outlines (one or two colours) lying
    entirely outside the frame. They never reach the window and leave no
    trace in the output. Their border is strictly shorter than the frame's.
  * Not supported: nested outlines; outlines whose boxes touch or overlap;
    outline edges lying on a frame row or column; non-checkerboard
    multicolour patterns; a second border-only object as large as the frame;
    two hidden rectangles sharing a colour set.

Fixture replay:
  Explicit latent arguments rebuild the fixture scenes: frame box, outline
  boxes and colours, and distractor boxes. Train pair 3 uses the labelled
  curated teaching correction from open (unmerged) ARC-AGI-2 PR #64. Under
  that correction the 9/8 outline follows its checkerboard parity inside the
  window. Output row 5 is [2,9,8,9,8,9,8,9] and row 6 is [2,8,2,...]. The
  uncorrected canonical file differs in those eight cells. A comparison
  against the canonical file therefore reports 3/4 by design, and 4/4
  against the teaching fixture. No other correction is made. Explicit scenes
  are checked against the same invariants as random scenes.
"""

import random

import common


def _border(box):
  y0, x0, y1, x1 = box
  cells = []
  for y in range(y0, y1 + 1):
    for x in range(x0, x1 + 1):
      if y in (y0, y1) or x in (x0, x1):
        cells.append((y, x))
  return cells


def _perimeter(box):
  return 2 * (box[2] - box[0] + 1) + 2 * (box[3] - box[1] + 1) - 4


def _inside(box, y, x):
  return box[0] <= y <= box[2] and box[1] <= x <= box[3]


def _colour(colors, y, x):
  if len(colors) == 1:
    return colors[0]
  return colors[(y + x) % 2]


def _separated(a, b, gap=1):
  return (a[2] + gap < b[0] or b[2] + gap < a[0] or
          a[3] + gap < b[1] or b[3] + gap < a[1])


def _touches_corner(box, height, width):
  return ((box[0] == 0 or box[2] == height - 1) and
          (box[1] == 0 or box[3] == width - 1))


def _components(cells):
  cellset = set(cells)
  seen = set()
  comps = []
  for start in cells:
    if start in seen:
      continue
    seen.add(start)
    stack = [start]
    comp = []
    while stack:
      y, x = stack.pop()
      comp.append((y, x))
      for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (y + dy, x + dx)
        if n in cellset and n not in seen:
          seen.add(n)
          stack.append(n)
    comps.append(comp)
  return comps


def _box_ok(box, height, width):
  y0, x0, y1, x1 = box
  return (0 <= y0 and y1 < height and 0 <= x0 and x1 < width and
          y1 - y0 >= 2 and x1 - x0 >= 2)


def _outline_ok(box, colors, frame, window):
  """Checks that a crossing outline can be recovered from its visible part."""
  if box[0] in (frame[0], frame[2]) or box[2] in (frame[0], frame[2]):
    return False
  if box[1] in (frame[1], frame[3]) or box[3] in (frame[1], frame[3]):
    return False
  border = _border(box)
  visible = [c for c in border if not _inside(frame, c[0], c[1])]
  if not visible:
    return False
  ys = [y for y, _ in visible]
  xs = [x for _, x in visible]
  if (min(ys), min(xs), max(ys), max(xs)) != tuple(box):
    return False
  if not any(_inside(window, y, x) for y, x in border):
    return False
  if len(colors) == 2:
    # Every visible piece must show both colours, so its colour set matches.
    for comp in _components(visible):
      if len(comp) < 2:
        return False
  return True


def _scene_error(height, width, bg, frame, fc, fill, outlines, distractors,
                 decoys):
  """Returns a description of the first violated invariant, or None."""
  if not (1 <= height <= 30 and 1 <= width <= 30):
    return 'grid size out of range'
  allc = [bg, fc, fill] + [c for _, cs in outlines for c in cs]
  allc += [i for _, i in distractors] + [c for _, cs in decoys for c in cs]
  for c in allc:
    if not (isinstance(c, int) and 0 <= c <= 9):
      return 'colour out of range'
  if fc == bg or fill == fc:
    return 'frame colour collides with background or fill'
  fy0, fx0, fy1, fx1 = frame
  if not (0 <= fy0 and fy1 < height and 0 <= fx0 and fx1 < width):
    return 'frame out of bounds'
  if fy1 - fy0 < 4 or fx1 - fx0 < 4:
    return 'frame too small'
  window = (fy0 + 1, fx0 + 1, fy1 - 1, fx1 - 1)
  fsize = _perimeter(frame)
  if not outlines:
    return 'no outlines'
  used = set()
  for box, colors in outlines:
    if len(colors) not in (1, 2) or len(set(colors)) != len(colors):
      return 'bad outline colours'
    for c in colors:
      if c in (bg, fc, fill) or c in used:
        return 'outline colour collision'
      used.add(c)
    if not _box_ok(box, height, width):
      return 'outline out of bounds'
    if not _outline_ok(box, colors, frame, window):
      return 'outline not recoverable'
  for i in range(len(outlines)):
    for j in range(i + 1, len(outlines)):
      if not _separated(outlines[i][0], outlines[j][0]):
        return 'outlines touch'
  inners = set()
  for box, inner in distractors:
    if not _box_ok(box, height, width):
      return 'distractor out of bounds'
    if _perimeter(box) >= fsize:
      return 'distractor not smaller than frame'
    if inner != bg and (inner in used or inner in (fc, fill)):
      return 'distractor inner colour collision'
    if inner != bg:
      inners.add(inner)
    if not _separated(box, frame):
      return 'distractor touches frame'
    if not all(_separated(box, b) for b, _ in outlines):
      return 'distractor touches outline'
  for i in range(len(distractors)):
    for j in range(i + 1, len(distractors)):
      if not _separated(distractors[i][0], distractors[j][0]):
        return 'distractors touch'
  if distractors:
    union = (min(b[0] for b, _ in distractors),
             min(b[1] for b, _ in distractors),
             max(b[2] for b, _ in distractors),
             max(b[3] for b, _ in distractors))
    if not _separated(union, frame, gap=0):
      return 'distractors straddle the frame'
  for k, (box, colors) in enumerate(decoys):
    if len(colors) not in (1, 2) or len(set(colors)) != len(colors):
      return 'bad decoy colours'
    for c in colors:
      if c in (bg, fc, fill) or c in used or c in inners:
        return 'decoy colour collision'
      used.add(c)
    if not _box_ok(box, height, width):
      return 'decoy out of bounds'
    if _perimeter(box) >= fsize:
      return 'decoy not smaller than frame'
    if not _separated(box, frame):
      return 'decoy touches frame'
    others = [b for b, _ in outlines] + [b for b, _ in distractors]
    others += [b for b, _ in decoys[:k]]
    if not all(_separated(box, b) for b in others):
      return 'decoy touches another object'
  return None


def _grid_error(g, bg):
  h, w = len(g), len(g[0])
  if any(g[y][x] != bg for y in (0, h - 1) for x in (0, w - 1)):
    return 'corner not background'
  counts = {}
  for row in g:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if any(c >= counts.get(bg, 0) for v, c in counts.items() if v != bg):
    return 'background not dominant'
  return None


def _render(height, width, background, frame, frame_color, fill, outlines,
            distractors, decoys):
  g = common.grid(width, height, background)
  for box, colors in list(outlines) + list(decoys):
    for y, x in _border(box):
      g[y][x] = _colour(colors, y, x)
  for box, inner in distractors:
    y0, x0, y1, x1 = box
    for y in range(y0, y1 + 1):
      for x in range(x0, x1 + 1):
        edge = y in (y0, y1) or x in (x0, x1)
        g[y][x] = frame_color if edge else inner
  fy0, fx0, fy1, fx1 = frame
  for y in range(fy0, fy1 + 1):
    for x in range(fx0, fx1 + 1):
      edge = y in (fy0, fy1) or x in (fx0, fx1)
      g[y][x] = frame_color if edge else fill
  window = (fy0 + 1, fx0 + 1, fy1 - 1, fx1 - 1)
  out = [[fill] * (fx1 - fx0 - 1) for _ in range(fy1 - fy0 - 1)]
  for box, colors in outlines:
    for y, x in _border(box):
      if _inside(window, y, x):
        out[y - window[0]][x - window[1]] = _colour(colors, y, x)
  return {'input': g, 'output': out}


def _propose_box(hh, ww, frame, window):
  """Proposes a crossing outline box: generic, or split by the frame."""
  fy0, fx0, fy1, fx1 = frame
  r = random.random()
  if r < 0.15:
    # Spans the frame vertically; the side columns run through the window.
    y0 = random.randint(max(0, fy0 - 4), fy0 - 1)
    y1 = random.randint(fy1 + 1, min(hh - 1, fy1 + 4))
    x0 = random.randint(fx0 + 1, fx1 - 3)
    x1 = random.randint(x0 + 2, fx1 - 1)
    return (y0, x0, y1, x1)
  if r < 0.3:
    # Spans the frame horizontally; the top/bottom rows cross the window.
    x0 = random.randint(max(0, fx0 - 4), fx0 - 1)
    x1 = random.randint(fx1 + 1, min(ww - 1, fx1 + 4))
    y0 = random.randint(fy0 + 1, fy1 - 3)
    y1 = random.randint(y0 + 2, fy1 - 1)
    return (y0, x0, y1, x1)
  h = random.randint(3, min(hh, 16))
  w = random.randint(3, min(ww, 16))
  y0 = random.randint(max(0, window[0] - h + 1), min(window[2], hh - h))
  x0 = random.randint(max(0, window[1] - w + 1), min(window[3], ww - w))
  return (y0, x0, y0 + h - 1, x0 + w - 1)


def _sample_distractors(hh, ww, frame, outlines, pool, bg):
  fy0, fx0, fy1, fx1 = frame
  regions = []
  if fy0 - 1 >= 3:
    regions.append((0, 0, fy0 - 2, ww - 1))
  if hh - (fy1 + 2) >= 3:
    regions.append((fy1 + 2, 0, hh - 1, ww - 1))
  if fx0 - 1 >= 3:
    regions.append((0, 0, hh - 1, fx0 - 2))
  if ww - (fx1 + 2) >= 3:
    regions.append((0, fx1 + 2, hh - 1, ww - 1))
  if not regions:
    return []
  ry0, rx0, ry1, rx1 = random.choice(regions)
  inner = pool.pop() if pool and random.random() < 0.5 else bg
  fsize = _perimeter(frame)
  count = random.randint(1, 2)
  distractors = []
  for _ in range(80):
    if len(distractors) >= count:
      break
    dh = random.randint(3, min(7, ry1 - ry0 + 1))
    dw = random.randint(3, min(8, rx1 - rx0 + 1))
    if 2 * dh + 2 * dw - 4 >= fsize:
      continue
    dy0 = random.randint(ry0, ry1 - dh + 1)
    dx0 = random.randint(rx0, rx1 - dw + 1)
    box = (dy0, dx0, dy0 + dh - 1, dx0 + dw - 1)
    if _touches_corner(box, hh, ww):
      continue
    if not _separated(box, frame):
      continue
    if not all(_separated(box, b) for b, _ in outlines):
      continue
    if not all(_separated(box, b) for b, _ in distractors):
      continue
    distractors.append((box, inner))
  return distractors


def _sample_decoys(hh, ww, frame, outlines, distractors, pool, count):
  fsize = _perimeter(frame)
  decoys = []
  for _ in range(200):
    if len(decoys) >= count or not pool:
      break
    dh = random.randint(3, min(8, hh))
    dw = random.randint(3, min(8, ww))
    if 2 * dh + 2 * dw - 4 >= fsize:
      continue
    y0 = random.randint(0, hh - dh)
    x0 = random.randint(0, ww - dw)
    box = (y0, x0, y0 + dh - 1, x0 + dw - 1)
    if _touches_corner(box, hh, ww):
      continue
    if not _separated(box, frame):
      continue
    others = [b for b, _ in outlines] + [b for b, _ in distractors]
    others += [b for b, _ in decoys]
    if not all(_separated(box, b) for b in others):
      continue
    alt = len(pool) >= 2 and random.random() < 0.35
    colors = (pool[0], pool[1]) if alt else (pool[0],)
    del pool[:len(colors)]
    decoys.append((box, colors))
  return decoys


def _sample(height, width, background, frame_color, fill, num_outlines,
            num_decoys):
  for _ in range(600):
    hh = height if height is not None else random.randint(16, 30)
    ww = width if width is not None else random.randint(16, 30)
    pool = list(range(10))
    random.shuffle(pool)
    if background is not None:
      bg = background
    else:
      bg = [c for c in pool if c != frame_color][0]
    pool.remove(bg)
    if frame_color is not None:
      fc = frame_color
    else:
      fc = [c for c in pool if c != fill][0]
    pool.remove(fc)
    if fill is not None:
      fl = fill
      if fl in pool:
        pool.remove(fl)
    elif random.random() < 0.5:
      fl = bg
    else:
      fl = pool.pop()
    fh = random.randint(5, min(22, hh - 4))
    fw = random.randint(5, min(22, ww - 4))
    fy0 = random.randint(2, hh - fh - 2)
    fx0 = random.randint(2, ww - fw - 2)
    frame = (fy0, fx0, fy0 + fh - 1, fx0 + fw - 1)
    window = (fy0 + 1, fx0 + 1, frame[2] - 1, frame[3] - 1)
    want = num_outlines if num_outlines is not None else random.choice(
        [1, 2, 2, 3, 3])
    outlines = []
    for _ in range(400):
      if len(outlines) >= want or not pool:
        break
      box = _propose_box(hh, ww, frame, window)
      if not _box_ok(box, hh, ww):
        continue
      if not all(_separated(box, b) for b, _ in outlines):
        continue
      alt = len(pool) >= 2 and random.random() < 0.4
      colors = (pool[0], pool[1]) if alt else (pool[0],)
      if not _outline_ok(box, colors, frame, window):
        continue
      del pool[:len(colors)]
      outlines.append((box, colors))
    if len(outlines) != want:
      continue
    distractors = []
    if random.random() < 0.4:
      distractors = _sample_distractors(hh, ww, frame, outlines, pool, bg)
    want_dec = num_decoys if num_decoys is not None else random.choice(
        [0, 0, 0, 0, 1, 1, 2])
    decoys = []
    if want_dec:
      decoys = _sample_decoys(hh, ww, frame, outlines, distractors, pool,
                              want_dec)
      if len(decoys) != want_dec:
        continue
    if _scene_error(hh, ww, bg, frame, fc, fl, outlines, distractors,
                    decoys):
      continue
    pair = _render(hh, ww, bg, frame, fc, fl, outlines, distractors, decoys)
    if _grid_error(pair['input'], bg):
      continue
    return pair
  raise RuntimeError('could not construct a valid scene')


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_colour(name, value):
  if value is not None and not (_is_int(value) and 0 <= value <= 9):
    raise ValueError(name + ' must be a colour 0..9')


def _as_box(name, box):
  if not (isinstance(box, (tuple, list)) and len(box) == 4 and
          all(_is_int(v) for v in box)):
    raise ValueError(name + ' must be four integers (y0, x0, y1, x1)')
  return tuple(box)


def _as_colors(name, colors):
  if not (isinstance(colors, (tuple, list)) and
          all(_is_int(v) for v in colors)):
    raise ValueError(name + ' colours must be a tuple of integers')
  return tuple(colors)


def _as_pairs(name, items):
  if not isinstance(items, (tuple, list)):
    raise ValueError(name + ' must be a list of (box, value) pairs')
  for item in items:
    if not (isinstance(item, (tuple, list)) and len(item) == 2):
      raise ValueError(name + ' entries must be (box, value) pairs')
  return items


def generate(height=None, width=None, background=None, frame=None,
             frame_color=None, fill=None, outlines=None, distractors=None,
             decoys=None, num_outlines=None, num_decoys=None):
  """Generates one window/hidden-outline pair.

  Args:
    height: grid height. Random mode samples 16..30 and accepts 10..30.
    width: grid width. Random mode samples 16..30 and accepts 10..30.
    background: background colour.
    frame: (y0, x0, y1, x1) box of the frame border. Supplying frame and
      outlines selects explicit (fixture) rendering. Explicit rendering also
      needs height, width, background, frame_color and fill. Supplying only
      one of frame/outlines is rejected.
    frame_color: colour of the frame and of any distractor boxes. It must
      differ from background and fill.
    fill: colour of the frame interior. It may equal the background. Random
      mode honours it when given.
    outlines: list of ((y0, x0, y1, x1), colors) crossing outlines. colors
      is (c,) for a single-colour outline, or (even, odd) for an outline
      coloured by the parity (y + x) % 2. Explicit mode only.
    distractors: list of ((y0, x0, y1, x1), inner_colour). These are small
      frame-coloured boxes. Explicit mode only; defaults to none.
    decoys: list of ((y0, x0, y1, x1), colors). These are complete outlines
      lying fully outside the frame. Explicit mode only; defaults to none.
    num_outlines: number of crossing outlines in random mode (1..4). Three
      need every given side >= 12, and four need every given side >= 14.
      In explicit mode it must be None or equal len(outlines).
    num_decoys: number of decoy outlines in random mode (0..2). Decoys need
      some given side >= 14 when both sides are given. In explicit mode it
      must be None or equal len(decoys).
  """
  for name, value in (('background', background),
                      ('frame_color', frame_color), ('fill', fill)):
    _check_colour(name, value)
  if frame_color is not None and frame_color in (background, fill):
    raise ValueError('frame_color must differ from background and fill')
  for name, value in (('height', height), ('width', width),
                      ('num_outlines', num_outlines),
                      ('num_decoys', num_decoys)):
    if value is not None and not _is_int(value):
      raise ValueError(name + ' must be an integer')
  if (frame is None) != (outlines is None):
    raise ValueError('frame and outlines must be supplied together')
  if frame is not None:
    if None in (height, width, background, frame_color, fill):
      raise ValueError('explicit mode needs height, width, background, '
                       'frame_color and fill')
    fbox = _as_box('frame', frame)
    outs = [(_as_box('outline', b), _as_colors('outline', c))
            for b, c in _as_pairs('outlines', outlines)]
    dists = []
    for b, c in _as_pairs('distractors', distractors or []):
      if not _is_int(c):
        raise ValueError('distractor inner colour must be an integer')
      dists.append((_as_box('distractor', b), c))
    decs = [(_as_box('decoy', b), _as_colors('decoy', c))
            for b, c in _as_pairs('decoys', decoys or [])]
    if num_outlines is not None and num_outlines != len(outs):
      raise ValueError('num_outlines does not match outlines')
    if num_decoys is not None and num_decoys != len(decs):
      raise ValueError('num_decoys does not match decoys')
    err = _scene_error(height, width, background, fbox, frame_color, fill,
                       outs, dists, decs)
    if err:
      raise ValueError('invalid explicit scene: ' + err)
    pair = _render(height, width, background, fbox, frame_color, fill, outs,
                   dists, decs)
    err = _grid_error(pair['input'], background)
    if err:
      raise ValueError('invalid explicit scene: ' + err)
    return pair
  if distractors is not None or decoys is not None:
    raise ValueError('distractors and decoys are only supported in '
                     'explicit mode')
  for name, value in (('height', height), ('width', width)):
    if value is not None and not 10 <= value <= 30:
      raise ValueError(name + ' must be 10..30 in random mode')
  if num_outlines is not None and not 1 <= num_outlines <= 4:
    raise ValueError('num_outlines must be 1..4')
  if num_decoys is not None and not 0 <= num_decoys <= 2:
    raise ValueError('num_decoys must be 0..2')
  given = [v for v in (height, width) if v is not None]
  if num_outlines == 3 and any(v < 12 for v in given):
    raise ValueError('three outlines need every given side >= 12')
  if num_outlines == 4 and any(v < 14 for v in given):
    raise ValueError('four outlines need every given side >= 14')
  if num_decoys and len(given) == 2 and max(given) < 14:
    raise ValueError('decoys need a given side >= 14')
  return _sample(height, width, background, frame_color, fill, num_outlines,
                 num_decoys)


def validate():
  """Rebuilds the teaching-corrected fixtures from explicit latent args."""
  train = [
      generate(height=20, width=20, background=8, frame=(6, 4, 11, 12),
               frame_color=3, fill=8,
               outlines=[((3, 8, 9, 14), (2,)), ((9, 2, 13, 6), (4,))]),
      generate(height=30, width=30, background=1, frame=(11, 10, 25, 25),
               frame_color=3, fill=6,
               outlines=[((3, 6, 19, 13), (2,)), ((8, 18, 27, 21), (8,))]),
      # Labelled teaching correction (open ARC-AGI-2 PR #64): the 9/8
      # outline keeps its checkerboard parity inside the window.
      generate(height=22, width=22, background=2, frame=(7, 5, 15, 14),
               frame_color=3, fill=2,
               outlines=[((3, 3, 10, 9), (5, 4)), ((13, 7, 17, 16), (9, 8))]),
  ]
  test = [
      generate(height=24, width=24, background=1, frame=(5, 5, 14, 16),
               frame_color=3, fill=7,
               outlines=[((7, 2, 15, 9), (0,)), ((4, 11, 8, 18), (8,)),
                         ((11, 13, 20, 18), (4, 9))],
               distractors=[((20, 3, 22, 5), 6), ((20, 8, 23, 11), 6)]),
  ]
  return {'train': train, 'test': test}
