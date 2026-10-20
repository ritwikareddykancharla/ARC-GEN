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

'''ARC-GEN style generator for ARC task b6f77b65.

Rule:
- Row 0 is a legend. Its non-background cells name the colours to delete.
- Below the legend is a scaffold of single-colour sticks.
- A vertical run of two or more cells is a pole. A pole and a horizontal
  foot leaving its bottom cell form one rigid piece.
- Every other horizontal run is a separate rigid piece. This covers free
  beams and also top bars hanging off a pole: a top bar is NOT rigidly
  joined to its pole.

Quirk kept from the verified program: a pole whose bottom tip sits
directly on a free beam of another colour is lengthened by one cell into
that beam. A free beam is a beam whose object has no pole. The extension
cell stays hidden under the beam until the beam is deleted.

Pieces of legend colours are deleted, then gravity runs. A piece is
supported when any of these holds:
- it touches the floor;
- it rests on, or overlaps, a supported piece;
- one of its horizontal runs is wedged between supported cells at both
  ends.
All unsupported pieces drop one row together until everything is
supported. If no legend colour occurs in the scaffold, the grid is
returned unchanged.

Corrections to the task explanation prose. These are documentation
fixes only; the canonical fixtures are reproduced unchanged.
- Test 1 (legend 7): only the 7 cells vanish and nothing moves. The 8
  pole at x=6 stands on the 5 top bar at (6, 6), and that support does
  not involve colour 7.
- Train pair 2 (legend 4): the 2 pole at x=5 carries a hidden extension
  cell at (6, 5) under the free 4 beam. That pole drops 2 rows (rows 2..6
  become 4..8, so column 5 shows five 2 cells). The 5 beam and the 8 pole
  drop 3 rows.

Controls (the mode argument):
- 'identity': the legend colours are absent and the output equals the
  input.
- 'delete': legend colours are erased and nothing moves.
- 'motion': at least one remaining piece falls.
- 'reveal': a free beam under a pole of another colour is deleted. The
  pole's hidden extension cell becomes visible, and something falls.
- 'foot': a pole-with-foot (L) piece falls. This includes the wedged L
  that drops once one of its wedging poles is deleted.
Reveal, foot and part of the motion samples are built constructively.
A supporter object and the object it carries are picked from the latent
layout and given a legend colour and a kept colour respectively. The
generator's own latent physics then confirms the requested property.
Default target weights are identity 6, delete 9, motion 45, reveal 20
and foot 20. After 250 failed attempts the default path relaxes to
motion, and after 450 to any present deletion. The expected default mix
is therefore about 6% identity, about 9% pure deletion and about 85%
with movement. These are design targets, not measured rates. With an
explicit legend and no mode, the generator targets motion 85% of the
time and pure deletion 15%.

Scope:
- Random scenes are built bottom-up from bands. Band heights and band
  counts scale with the grid height, and tall grids are steered toward
  using at least 45% of the vertical span.
- Each band holds poles standing on the floor, on the deck of the band
  below, or on the foot of a hanging L from that band.
- Poles in a band are flush with the deck, one row shorter, or 1..2 rows
  taller. The deck is built from free beams, top bars, or open slots that
  the next band fills with a wedged rigid L.
- Some poles get feet, and occasionally a loose plank lies on top.
- Legends have 1..3 distinct colours, written from x=0.
- The answer is computed from latent pieces, never by parsing the grid.

Sizes:
- Random sizes are 10..18 per side by default. Any explicit width or
  height in 9..30 is honoured, with or without the other dimension.
- Explicit latent scaffolds accept 3..30 per side.
- The 12x12 fixture size is not intrinsic to the task.
'''

import itertools
import random

import common


_MODES = ('identity', 'delete', 'motion', 'reveal', 'foot')
_DEFAULT_MODE_WEIGHTS = (('identity', 6), ('delete', 9), ('motion', 45),
                         ('reveal', 20), ('foot', 20))
_SIZE_WEIGHTS = {1: 75, 2: 20, 3: 5}
_BASE_BIAS = {'slot': 0.25, 'fill': 0.7, 'deckbar': 0.45, 'foot': 0.35,
              'plank': 0.35}


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _object_cells(obj):
  '''Cells of a latent object.

  obj is ('post', colour, x, top, bottom, topbar, foot) or
  ('bar', colour, y, x0, x1). topbar and foot are (x0, x1) or None.
  '''
  if obj[0] == 'post':
    _, _, x, top, bottom, topbar, foot = obj
    cells = {(y, x) for y in range(top, bottom + 1)}
    if topbar:
      cells |= {(top, xx) for xx in range(topbar[0], topbar[1] + 1)}
    if foot:
      cells |= {(bottom, xx) for xx in range(foot[0], foot[1] + 1)}
    return cells
  _, _, y, x0, x1 = obj
  return {(y, xx) for xx in range(x0, x1 + 1)}


def _pieces(objects):
  '''Rigid pieces of the latent objects, including the pole-tip extension.'''
  pieces = []
  for obj in objects:
    if obj[0] == 'post':
      _, c, x, top, bottom, topbar, foot = obj
      h = set()
      if foot:
        h = {(bottom, xx) for xx in range(foot[0], foot[1] + 1)}
      pieces.append({'c': c, 'v': {(y, x) for y in range(top, bottom + 1)},
                     'h': h, 'bar': False, 'ext': None, 'ext_c': None})
      if topbar:
        pieces.append({'c': c, 'v': set(), 'bar': False, 'ext': None,
                       'ext_c': None,
                       'h': {(top, xx)
                             for xx in range(topbar[0], topbar[1] + 1)}})
    else:
      _, c, y, x0, x1 = obj
      pieces.append({'c': c, 'v': set(), 'bar': True, 'ext': None,
                     'ext_c': None,
                     'h': {(y, xx) for xx in range(x0, x1 + 1)}})
  for p in pieces:
    if p['v']:
      y, x = max(p['v'])
      for q in pieces:
        if (y + 1, x) in q['h'] and q['c'] != p['c'] and q['bar']:
          p['ext'] = (y + 1, x)
          p['ext_c'] = q['c']
          break
  for p in pieces:
    if p['ext'] is not None:
      p['v'].add(p['ext'])
  return pieces


def _runs(values):
  out = []
  for v in sorted(values):
    if not out or v != out[-1][-1] + 1:
      out.append([])
    out[-1].append(v)
  return out


def _stable(pieces, height):
  '''Indices of pieces supported by floor, contact, overlap or wedging.'''
  stable = set()
  while True:
    occ = set()
    for i in stable:
      occ |= pieces[i]['v'] | pieces[i]['h']
    added = set()
    for i, p in enumerate(pieces):
      if i in stable:
        continue
      cells = p['v'] | p['h']
      ok = any(y == height - 1 or (y + 1, x) in occ or (y, x) in occ
               for y, x in cells)
      if not ok:
        for y in {y for y, _ in cells}:
          for xs in _runs([x for yy, x in cells if yy == y]):
            if (y, xs[0] - 1) in occ and (y, xs[-1] + 1) in occ:
              ok = True
      if ok:
        added.add(i)
    if not added:
      return stable
    stable |= added


def _settle(pieces, height):
  for _ in range(height * (len(pieces) + 1) + 1):
    stable = _stable(pieces, height)
    if len(stable) == len(pieces):
      return pieces
    for i, p in enumerate(pieces):
      if i not in stable:
        p['v'] = {(y + 1, x) for y, x in p['v']}
        p['h'] = {(y + 1, x) for y, x in p['h']}
  raise ValueError('gravity did not settle')


def _render(width, height, legend, pieces):
  out = common.grid(width, height, 0)
  for field in ('v', 'h'):
    for p in pieces:
      for y, x in p[field]:
        out[y][x] = p['c']
  for i, c in enumerate(legend):
    out[0][i] = c
  return out


def _paint(width, height, legend, objects):
  inp = common.grid(width, height, 0)
  for i, c in enumerate(legend):
    inp[0][i] = c
  for o in objects:
    for y, x in _object_cells(o):
      inp[y][x] = o[1]
  return inp


def _simulate(objects, legend, height):
  '''Deletes legend colours and settles the latent pieces.

  Returns (remaining pieces, info), where info records whether a legend
  colour is present, whether anything moved, whether a hidden extension
  is revealed, whether a footed pole moved, and the survivor count.
  '''
  removed = set(legend)
  info = {'present': any(o[1] in removed for o in objects),
          'moved': False, 'reveal': False, 'foot': False, 'survivors': 0}
  allp = _pieces(objects)
  for p in allp:
    if (p['ext'] is not None and p['ext_c'] in removed and
        p['c'] not in removed):
      info['reveal'] = True
  pieces = [p for p in allp if p['c'] not in removed]
  info['survivors'] = len(pieces)
  if info['present'] and pieces:
    before = [p['v'] | p['h'] for p in pieces]
    _settle(pieces, height)
    for p, cells in zip(pieces, before):
      if (p['v'] | p['h']) != cells:
        info['moved'] = True
        if p['v'] and p['h']:
          info['foot'] = True
  return pieces, info


def _matches(info, mode):
  if mode == 'identity':
    return not info['present']
  if not info['present'] or not info['survivors']:
    return False
  if mode == 'delete':
    return not info['moved']
  if mode == 'motion':
    return info['moved']
  if mode == 'reveal':
    return info['reveal'] and info['moved']
  if mode == 'foot':
    return info['foot']
  return True  # 'any': some legend colour present and something survives


def _choose_legend(objects, height, width, mode):
  '''Picks a legend of distinct colours that realises the mode, or None.'''
  present = sorted({o[1] for o in objects})
  if mode == 'identity':
    absent = [c for c in range(1, 10) if c not in present]
    if not absent:
      return None
    k = 2 if (len(absent) >= 2 and width >= 2 and
              random.random() < 0.15) else 1
    return random.sample(absent, k)
  sizes = [k for k, need in ((1, 2), (2, 4), (3, 6))
           if len(present) >= need and k <= width]
  if not sizes:
    return None
  first = random.choices(sizes, [_SIZE_WEIGHTS[k] for k in sizes])[0]
  for k in [first] + [s for s in sizes if s != first]:
    combos = list(itertools.combinations(present, k))
    random.shuffle(combos)
    for combo in combos[:12]:
      leg = list(combo)
      random.shuffle(leg)
      if _matches(_simulate(objects, leg, height)[1], mode):
        return leg
  return None


def _sample_default_mode():
  modes = [m for m, _ in _DEFAULT_MODE_WEIGHTS]
  weights = [w for _, w in _DEFAULT_MODE_WEIGHTS]
  return random.choices(modes, weights)[0]


def _bias(mode):
  b = dict(_BASE_BIAS)
  if mode == 'foot':
    b.update(slot=0.5, fill=0.95, foot=0.55)
  elif mode == 'reveal':
    b.update(deckbar=0.75)
  return b


def _pick_columns(ground, count):
  cands = list(ground)
  random.shuffle(cands)
  chosen = []
  for x in cands:
    if all(abs(x - c) >= 2 for c in chosen):
      chosen.append(x)
      if len(chosen) == count:
        break
  return sorted(chosen)


def _band0_columns(width):
  '''Floor poles spread over a random horizontal offset (gaps >= 2).

  Occasionally one gap is long (6..10), which gives a long wedged beam.
  '''
  count = random.randint(2, max(3, (width - 2) // 3))
  gaps = [random.randint(2, 5) for _ in range(count - 1)]
  if gaps and random.random() < 0.3:
    gaps[random.randrange(len(gaps))] = random.randint(6, 10)
  while len(gaps) > 1 and sum(gaps) > width - 3:
    gaps.pop()
  if sum(gaps) > width - 3:
    gaps = [width - 3]
  span = sum(gaps)
  x = random.randint(1, width - 2 - span)
  cols = [x]
  for g in gaps:
    x += g
    cols.append(x)
  return cols


def _random_layout(width, height, bias):
  '''Builds an uncoloured banded scaffold as a list of latent objects.'''
  layout = []
  ground_row = height
  ground = list(range(1, width - 1))
  blocked = set()
  slots = []
  bands = 0
  if height <= 9:
    max_hb = 3
  elif height < 18:
    max_hb = 4
  else:
    max_hb = min(8, max(5, height // 4 + 1))
  lo = 2 if height < 20 else max(2, (height - 2) // 7)
  hi = max(5, (height - 2) // 3)
  for band in range(random.randint(lo, hi)):
    bottom = ground_row - 1
    hb = min(random.randint(3, max_hb), bottom - 1)
    if hb < 3:
      break
    top = bottom - hb + 1
    # lfeet: columns of poles that descend into a deck slot of the band
    # below, mapped to the foot that fills the rest of that slot.
    lfeet = {}
    if band == 0:
      cols = _band0_columns(width)
    else:
      for a, b in slots:
        if random.random() < bias['fill']:
          if random.random() < 0.5:
            lfeet[a] = (a + 1, b)
          else:
            lfeet[b] = (a, b - 1)
      base = set(ground)
      for f0, f1 in lfeet.values():
        base.update(range(f0, f1 + 1))
      cand = sorted(x for x in base
                    if all(abs(x - l) >= 2 for l in lfeet))
      picked = []
      if cand:
        picked = _pick_columns(cand,
                               random.randint(1, max(3, len(cand) // 4)))
      cols = sorted(set(picked) | set(lfeet))
    if not cols:
      break
    n = len(cols)
    # Per-pole top offset: <0 tall (passes the deck), 1 short, 0 flush.
    shifts = []
    for _ in cols:
      r = random.random()
      if r < 0.15 and top >= 3:
        shifts.append(-random.randint(1, min(2, top - 2)))
      elif r < 0.3:
        shifts.append(1)
      else:
        shifts.append(0)
    topbars = [None] * n
    feet = [None] * n
    deck = {x for x, s in zip(cols, shifts) if s <= 0}
    deck_bars = []
    new_slots = []
    for i in range(n - 1):
      a, b = cols[i] + 1, cols[i + 1] - 1
      if shifts[i] == 1 and cols[i] not in deck:
        a = cols[i]
      if shifts[i + 1] == 1:
        b = cols[i + 1]
      if b - a + 1 > 9 or random.random() < 0.15:
        continue
      if (shifts[i] == 0 and shifts[i + 1] == 0 and 2 <= b - a + 1 <= 7
          and random.random() < bias['slot']):
        # Leave the deck open between two flush poles. The next band may
        # fill it with a wedged rigid L.
        new_slots.append((a, b))
        continue
      owners = [j for j in (i, i + 1)
                if topbars[j] is None and shifts[j] == 0]
      if random.random() < bias['deckbar'] or not owners:
        deck_bars.append((a, b))
      else:
        topbars[random.choice(owners)] = (a, b)
      deck.update(range(a, b + 1))
    used = set(cols) | blocked
    for j, x in enumerate(cols):
      if x in lfeet:
        feet[j] = lfeet[x]
        continue
      if random.random() < bias['foot']:
        side = random.choice((-1, 1))
        length = random.randint(1, 3)
        xs = [x + side * k for k in range(1, length + 1)]
        if all(1 <= xx <= width - 2 and xx not in used for xx in xs):
          feet[j] = (min(xs), max(xs))
          used.update(xs)
    for j, x in enumerate(cols):
      bot = bottom + 1 if x in lfeet else bottom
      layout.append(['post', None, x, top + shifts[j], bot, topbars[j],
                     feet[j]])
    for a, b in deck_bars:
      layout.append(['bar', None, top, a, b])
    bands += 1
    tall = {x for x, s in zip(cols, shifts) if s < 0}
    blocked = tall
    ground_row = top
    ground = sorted(deck - tall)
    slots = new_slots
  if bands < 2:
    return None
  if random.random() < bias['plank'] and ground_row - 1 >= 2 and ground:
    anchor = random.choice(ground)
    length = random.randint(2, 5)
    x0 = anchor - random.randint(0, length - 1)
    x1 = x0 + length - 1
    plank = ['bar', None, ground_row - 1, x0, x1]
    taken = set()
    for o in layout:
      taken |= _object_cells(o)
    if x0 >= 1 and x1 <= width - 2 and not (_object_cells(plank) & taken):
      layout.append(plank)
  min_objs = 4 if width * height < 120 else 5
  if len(layout) < min_objs:
    return None
  return layout


def _graph(layout, width, height):
  '''Cell owners and 8-neighbour adjacency of layout objects, or None.'''
  owner = {}
  for i, o in enumerate(layout):
    for cell in _object_cells(o):
      if cell in owner or not (1 <= cell[0] < height and
                               0 <= cell[1] < width):
        return None
      owner[cell] = i
  adj = [set() for _ in layout]
  for (y, x), i in owner.items():
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        j = owner.get((y + dy, x + dx))
        if j is not None and j != i:
          adj[i].add(j)
  return owner, adj


def _support_of(cells, owner, i):
  '''Objects directly below the cells or at the ends of their row runs.'''
  sup = set()
  for y, x in cells:
    j = owner.get((y + 1, x))
    if j is not None and j != i:
      sup.add(j)
  for y in {y for y, _ in cells}:
    for xs in _runs([x for yy, x in cells if yy == y]):
      for cell in ((y, xs[0] - 1), (y, xs[-1] + 1)):
        j = owner.get(cell)
        if j is not None and j != i:
          sup.add(j)
  return sorted(sup)


def _target_pairs(layout, owner, height, mode):
  '''(object to delete, object to keep) pairs that can realise the mode.'''
  pairs = []
  for i, o in enumerate(layout):
    if mode == 'reveal':
      if o[0] != 'post':
        continue
      j = owner.get((o[4] + 1, o[2]))
      if j is not None and layout[j][0] == 'bar':
        pairs.append((j, i))
    elif mode == 'foot':
      if o[0] != 'post' or o[6] is None:
        continue
      cells = {(y, o[2]) for y in range(o[3], o[4] + 1)}
      cells |= {(o[4], xx) for xx in range(o[6][0], o[6][1] + 1)}
      pairs.extend((j, i) for j in _support_of(cells, owner, i))
    elif mode == 'motion':
      cells = _object_cells(o)
      if max(y for y, _ in cells) == height - 1:
        continue
      pairs.extend((j, i) for j in _support_of(cells, owner, i))
  return pairs


def _palette(legend, mode):
  '''Returns (preferred palette, fallback colours) for colouring.'''
  allc = list(range(1, 10))
  if legend is None:
    if mode == 'identity':
      pal = random.sample(allc, random.randint(5, 8))
      return pal, pal
    return random.sample(allc, random.randint(5, 9)), allc
  others = [c for c in allc if c not in legend]
  if mode == 'identity':
    pal = random.sample(others, min(len(others), random.randint(5, 9)))
    return pal, others
  pal = random.sample(allc, random.randint(5, 9))
  if not any(c in legend for c in pal):
    pal[0] = random.choice(legend)
  if not any(c not in legend for c in pal):
    pal[-1] = random.choice(others)
  return pal, allc


def _fixed_colours(pair, legend):
  d, k = pair
  if legend is None:
    cd = random.randint(1, 9)
    ck = random.choice([c for c in range(1, 10) if c != cd])
  else:
    cd = random.choice(legend)
    ck = random.choice([c for c in range(1, 10) if c not in legend])
  return {d: cd, k: ck}


def _colour(adj, palette, fallback, fixed):
  '''Colours objects so that 8-adjacent objects never share a colour.'''
  n = len(adj)
  colours = [None] * n
  for i, c in fixed.items():
    colours[i] = c
  for i, c in fixed.items():
    if any(colours[j] == c for j in adj[i]):
      return None
  for i in random.sample(range(n), n):
    if colours[i] is not None:
      continue
    banned = {colours[j] for j in adj[i]}
    opts = [c for c in palette if c not in banned]
    if not opts:
      opts = [c for c in fallback if c not in banned]
    if not opts:
      return None
    colours[i] = random.choice(opts)
  return colours


def _check_size(value, name, low):
  if not _is_int(value) or not low <= value <= 30:
    raise ValueError(name + ' must be an integer in %d..30' % low)


def _check_objects(width, height, objects):
  '''Rejects explicit scaffolds whose grid parse could differ from latents.'''
  if not objects:
    raise ValueError('objects must be a non-empty list')
  owner = {}
  for i, obj in enumerate(objects):
    if not isinstance(obj, (list, tuple)) or not obj:
      raise ValueError('each latent object must be a tuple or list')
    kind = obj[0]
    if isinstance(kind, str) and kind == 'post' and len(obj) == 7:
      _, c, x, top, bottom, topbar, foot = obj
      if not all(_is_int(v) for v in (c, x, top, bottom)):
        raise ValueError('post fields must be integers')
      if not (0 <= x < width and 1 <= top and bottom < height):
        raise ValueError('post outside the scaffold area')
      if bottom - top < 1:
        raise ValueError('a post needs a pole of at least two cells')
      for arm in (topbar, foot):
        if arm is not None:
          if (not isinstance(arm, (list, tuple)) or len(arm) != 2 or
              not all(_is_int(v) for v in arm)):
            raise ValueError('a topbar/foot is None or a pair of integers')
          a, b = arm
          if not 0 <= a <= b < width:
            raise ValueError('a topbar/foot lies outside the grid')
          if not (b == x - 1 or a == x + 1):
            raise ValueError('a topbar/foot must leave the pole sideways')
      if topbar and foot and bottom == top + 1:
        if max(topbar[0], foot[0]) <= min(topbar[1], foot[1]):
          raise ValueError('topbar and foot would form an extra pole')
    elif isinstance(kind, str) and kind == 'bar' and len(obj) == 5:
      _, c, y, x0, x1 = obj
      if not all(_is_int(v) for v in (c, y, x0, x1)):
        raise ValueError('bar fields must be integers')
      if x0 > x1:
        raise ValueError('bar needs x0 <= x1')
      if not (1 <= y < height and 0 <= x0 and x1 < width):
        raise ValueError('bar outside the scaffold area')
    else:
      raise ValueError('unknown latent object ' + repr(obj))
    if not 1 <= c <= 9:
      raise ValueError('object colours must be 1..9')
    for cell in _object_cells(obj):
      if cell in owner:
        raise ValueError('objects overlap')
      owner[cell] = i
  bare = [o[0] == 'post' and o[5] is None and o[6] is None for o in objects]
  for (y, x), i in owner.items():
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
      j = owner.get((y + dy, x + dx))
      if j is None or j == i or objects[j][1] != objects[i][1]:
        continue
      if dy == 0 or dx == 0:
        raise ValueError('same-colour objects touch orthogonally')
      if not (bare[i] and bare[j]):
        # Under 8-connectivity this would merge objects and could change
        # foot attachment or the free-beam flag; only bare poles are safe.
        raise ValueError('same-colour objects touch diagonally')


def _build(width, height, legend, objects):
  inp = _paint(width, height, legend, objects)
  pieces, info = _simulate(objects, legend, height)
  if not info['present']:
    return {'input': inp, 'output': [row[:] for row in inp]}
  return {'input': inp, 'output': _render(width, height, legend, pieces)}


def _generate_explicit(width, height, objects, legend, mode):
  if (not isinstance(objects, (list, tuple)) or
      not all(isinstance(o, (list, tuple)) for o in objects)):
    raise ValueError('objects must be a list of tuples')
  if width is None or height is None:
    raise ValueError('width and height are required with objects')
  _check_size(width, 'width', 3)
  _check_size(height, 'height', 3)
  objs = [tuple(o) for o in objects]
  _check_objects(width, height, objs)
  initial = _pieces(objs)
  if len(_stable(initial, height)) != len(initial):
    raise ValueError('explicit scaffold is not stable before deletion')
  if legend is not None:
    leg = legend
    if mode is not None and not _matches(
        _simulate(objs, leg, height)[1], mode):
      raise ValueError('legend does not produce the requested mode')
  elif mode is not None:
    leg = _choose_legend(objs, height, width, mode)
    if leg is None:
      raise ValueError('requested mode is not achievable for this scaffold')
  else:
    leg = None
    for m in (_sample_default_mode(), 'motion', 'any', 'identity'):
      leg = _choose_legend(objs, height, width, m)
      if leg is not None:
        break
    if leg is None:
      raise ValueError('no valid legend exists for this scaffold')
  if len(leg) > width:
    raise ValueError('legend longer than the grid width')
  pair = _build(width, height, leg, objs)
  counts = [0] * 10
  for row in pair['input']:
    for v in row:
      counts[v] += 1
  if any(counts[c] >= counts[0] for c in range(1, 10)):
    raise ValueError('background 0 must be the most frequent colour')
  return pair


def _generate_random(width, height, legend, mode):
  if width is not None:
    _check_size(width, 'width', 9)
  if height is not None:
    _check_size(height, 'height', 9)
  if legend is not None:
    if width is not None and len(legend) > width:
      raise ValueError('legend longer than the grid width')
    if len(legend) >= 9:
      raise ValueError('a random scene needs a colour outside the legend')
  if mode is not None:
    base = mode
  elif legend is None:
    base = _sample_default_mode()
  else:
    base = 'motion' if random.random() < 0.85 else 'delete'
  extra = len(legend) if legend is not None else 3
  for attempt in range(600):
    cur = base
    if mode is None and attempt >= 250:
      cur = 'motion' if (legend is None and attempt < 450) else 'any'
    w = width if width is not None else random.randint(10, 18)
    h = height if height is not None else random.randint(10, 18)
    layout = _random_layout(w, h, _bias(cur))
    if layout is None:
      continue
    graph = _graph(layout, w, h)
    if graph is None:
      continue
    owner, adj = graph
    if h >= 16 and attempt < 300:
      top = min(y for y, _ in owner)
      if h - top < 0.45 * (h - 1):
        continue
    if (len(owner) + extra) * 2 >= w * h:
      continue
    pairs = []
    if cur in ('reveal', 'foot', 'motion'):
      pairs = _target_pairs(layout, owner, h, cur)
      if cur != 'motion' and not pairs:
        continue
    for _ in range(6):
      pal, fallback = _palette(legend, cur)
      fixed = {}
      if pairs and (cur != 'motion' or random.random() < 0.5):
        fixed = _fixed_colours(random.choice(pairs), legend)
      colours = _colour(adj, pal, fallback, fixed)
      if colours is None:
        continue
      objs = [tuple([o[0], c] + list(o[2:]))
              for o, c in zip(layout, colours)]
      initial = _pieces(objs)
      if len(_stable(initial, h)) != len(initial):
        continue
      if legend is not None:
        leg = list(legend)
        if not _matches(_simulate(objs, leg, h)[1], cur):
          continue
      else:
        leg = _choose_legend(objs, h, w, cur)
        if leg is None or len(leg) > w:
          continue
      return _build(w, h, leg, objs)
  raise ValueError('could not build a scene for the requested controls')


def generate(width=None, height=None, objects=None, legend=None, mode=None):
  '''Returns {'input': grid, 'output': grid} for task b6f77b65.

  Args:
    width: grid width. Sampled from 10..18 when None. Explicit values
      must be 9..30 for random scenes and 3..30 with objects. Required
      when objects is given.
    height: grid height, with the same ranges and requirement as width.
    objects: optional explicit latent scaffold, as a list of
      ('post', colour, x, top, bottom, topbar, foot) and
      ('bar', colour, y, x0, x1) tuples. topbar and foot are (x0, x1)
      or None. The scaffold must lie inside the grid below row 0, be
      stable before deletion, and leave 0 the strict plurality colour.
      Same-colour objects may touch only diagonally, and only when both
      are bare posts.
    legend: optional list of 1..9 DISTINCT colours in 1..9, written in
      row 0 from x=0. Duplicates are rejected. When None, a legend is
      chosen from the scene to realise the mode. In random scenes an
      explicit legend must leave at least one colour outside it.
    mode: optional control, one of 'identity', 'delete', 'motion',
      'reveal' or 'foot' (see the module docstring). When None, random
      scenes sample a target mode, and explicit scaffolds with an
      explicit legend are rendered as given. An explicitly requested
      mode that cannot be realised raises ValueError.
  '''
  if mode is not None and (not isinstance(mode, str) or mode not in _MODES):
    raise ValueError('mode must be None or one of ' + ', '.join(_MODES))
  if legend is not None:
    if not isinstance(legend, (list, tuple)):
      raise ValueError('legend must be a list of colours')
    legend = list(legend)
    if (not legend or len(legend) > 9 or
        not all(_is_int(c) and 1 <= c <= 9 for c in legend)):
      raise ValueError('legend must hold 1..9 integer colours in 1..9')
    if len(set(legend)) != len(legend):
      raise ValueError('legend colours must be distinct')
  if objects is not None:
    return _generate_explicit(width, height, objects, legend, mode)
  return _generate_random(width, height, legend, mode)


def validate():
  '''Reconstructs the canonical fixtures from explicit latent scaffolds.'''
  scaffold_a = [
      ('post', 5, 4, 2, 4, None, None),
      ('post', 1, 8, 2, 4, (5, 7), None),
      ('post', 6, 2, 5, 7, None, None),
      ('post', 3, 5, 5, 7, (3, 4), None),
      ('post', 5, 7, 5, 7, (8, 8), None),
      ('post', 7, 9, 5, 7, None, None),
      ('bar', 2, 8, 2, 9),
      ('post', 4, 1, 8, 11, None, None),
      ('post', 7, 10, 8, 11, None, None),
  ]
  scaffold_b = [
      ('post', 2, 5, 2, 5, None, None),
      ('bar', 5, 2, 6, 8),
      ('post', 8, 9, 2, 5, None, None),
      ('post', 9, 2, 6, 8, None, None),
      ('bar', 4, 6, 3, 5),
      ('post', 7, 6, 6, 9, None, (7, 9)),
      ('post', 2, 8, 6, 8, None, None),
      ('post', 3, 10, 6, 8, (9, 9), None),
      ('post', 6, 1, 9, 11, None, None),
      ('post', 5, 3, 9, 11, (2, 2), None),
      ('post', 1, 5, 9, 11, None, None),
      ('post', 4, 10, 9, 11, None, None),
  ]
  scaffold_c = [
      ('post', 4, 2, 2, 5, None, None),
      ('post', 3, 4, 2, 5, (3, 3), None),
      ('post', 8, 6, 3, 5, None, None),
      ('post', 7, 9, 3, 8, (7, 8), None),
      ('post', 6, 2, 6, 8, None, None),
      ('post', 5, 7, 6, 8, (3, 6), None),
      ('post', 3, 1, 9, 11, None, None),
      ('post', 1, 4, 9, 11, (2, 3), None),
      ('post', 2, 6, 9, 11, (7, 9), None),
      ('post', 9, 10, 9, 11, None, None),
  ]
  train = [
      generate(12, 12, scaffold_a, [9]),
      generate(12, 12, scaffold_b, [4]),
      generate(12, 12, scaffold_b, [6]),
      generate(12, 12, scaffold_a, [4]),
      generate(12, 12, scaffold_a, [7]),
  ]
  test = [
      generate(12, 12, scaffold_c, [7]),
      generate(12, 12, scaffold_c, [2, 1]),
  ]
  return {'train': train, 'test': test}
