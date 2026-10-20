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

"""ARC task 9f669b64: a projectile block splits a rectangle and flies to the edge.

Rule: the background is 7. The projectile is a solid rectangle. The first
object it meets in one of the four axis directions is the target. The target
is a solid rectangle that is wider than the projectile across the path and
overhangs it by the same positive margin on both sides. In the output:
  * the projectile is erased and redrawn flush against the grid edge in that
    direction, keeping its across-path position;
  * the target is cut at its across-path centre, and each half moves outward
    by half the projectile width, opening a gap exactly as wide as the
    projectile;
  * every other object is unchanged.

Scope: each scene is built in a canonical frame and then mapped to one of the
four travel directions. In that frame, u is the distance from the destination
edge and v is the across-path coordinate. Along the path lie, in order, the
target, the projectile and usually a collinear distractor on the far side.
The distractor is one of:
  * a bar of the same width as the projectile;
  * a stepped or ragged non-rectangle;
  * an off-centre rectangle or stack;
  * a hard-negative rectangle whose two margins differ.
An optional lateral decoy is placed beside the column of objects. It removes
the "middle of three collinear objects" shortcut. The decoy kinds are:
  * 'twin': a solid block with exactly the projectile's along-path extent;
  * 'isolated': a solid block in an along-path band that no other object uses;
  * 'shape': an L shape or a hollow frame.
When a decoy is present, the far-side distractor is sometimes omitted. The
scene then still has three objects, but the projectile is not in the middle.

The fixtures are 10x10. Random sides are 7..24. Any explicit side in 1..30
that fits the requested geometry is accepted. Dimensions and directions are
sampled conditioned on the minimum that the fixed parameters need, so 3x6
up/down scenes always work. Impossible requests raise ValueError before any
sampling. The following scale with the grid: the projectile width (even), the
projectile length, the target thickness (up to 2/5 of the path, so up to 4 on
a 10-cell path), the margin, both gaps, the distractor depth and overhang,
and the decoy size.

The unique (projectile, direction) pair follows from the geometry; see the
_attempt docstring. A local re-implementation of the selection condition only
asserts this and raises RuntimeError on violation. It never filters scenes.
"""

import random

import common

BG = 7
DIRS = ('up', 'down', 'left', 'right')
STEPS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
DECOYS = ('isolated', 'twin', 'shape')
SIDES = ('low', 'high')
MAX_TRIES = 600


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _dflt(x, d):
  return d if x is None else x


def _to_rc(direction, u, v, height, width):
  if direction == 'up':
    return u, v
  if direction == 'down':
    return height - 1 - u, v
  if direction == 'left':
    return v, u
  return v, width - 1 - u


def _paint(g, direction, cells, color):
  height, width = len(g), len(g[0])
  for u, v in cells:
    r, c = _to_rc(direction, u, v, height, width)
    g[r][c] = color


def _rect(u0, u1, v0, v1):
  return [(u, v) for u in range(u0, u1 + 1) for v in range(v0, v1 + 1)]


def _components(g):
  h, w = len(g), len(g[0])
  seen = set()
  objs = []
  for r in range(h):
    for c in range(w):
      if g[r][c] == BG or (r, c) in seen:
        continue
      col = g[r][c]
      stack = [(r, c)]
      seen.add((r, c))
      cells = []
      while stack:
        y, x = stack.pop()
        cells.append((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          ny, nx = y + dy, x + dx
          if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen:
            if g[ny][nx] == col:
              seen.add((ny, nx))
              stack.append((ny, nx))
      ys = [q[0] for q in cells]
      xs = [q[1] for q in cells]
      box = (min(ys), min(xs), max(ys), max(xs))
      objs.append({'colour': col, 'cells': cells, 'box': box})
  return objs


def _is_rect(o):
  y0, x0, y1, x1 = o['box']
  return len(o['cells']) == (y1 - y0 + 1) * (x1 - x0 + 1)


def _valid_choices(g):
  """Lists every (projectile colour, direction) meeting the selection rule."""
  objs = _components(g)
  found = []
  for p in objs:
    if not _is_rect(p):
      continue
    py0, px0, py1, px1 = p['box']
    for name in DIRS:
      dy, dx = STEPS[name]
      best = None
      for t in objs:
        if t is p:
          continue
        ty0, tx0, ty1, tx1 = t['box']
        if dy != 0:
          if tx1 < px0 or tx0 > px1:
            continue
          dist = (py0 - ty1) if dy < 0 else (ty0 - py1)
        else:
          if ty1 < py0 or ty0 > py1:
            continue
          dist = (px0 - tx1) if dx < 0 else (tx0 - px1)
        if dist <= 0:
          continue
        if best is None or dist < best[0]:
          best = (dist, t)
      if best is None or not _is_rect(best[1]):
        continue
      ty0, tx0, ty1, tx1 = best[1]['box']
      if dy != 0:
        a0, a1, b0, b1 = px0, px1, tx0, tx1
      else:
        a0, a1, b0, b1 = py0, py1, ty0, ty1
      if b0 < a0 and b1 > a1 and (a0 - b0) == (b1 - a1):
        found.append((p['colour'], name))
  return found


def _parse_colors(colors):
  """Checks the palette and materialises it exactly once."""
  if colors is None:
    return None
  if not isinstance(colors, (list, tuple)):
    raise ValueError('colors must be a list or tuple')
  cols = tuple(colors)
  if len(cols) not in (3, 4):
    raise ValueError('colors must hold 3 or 4 entries')
  if not all(_is_int(c) and 0 <= c <= 9 for c in cols):
    raise ValueError('colours must be integers in 0..9')
  if BG in cols or len(set(cols)) != len(cols):
    raise ValueError('colours must be distinct and differ from 7')
  return cols


def _parse_layers(layers):
  """Converts layers to (k_left, k_right, thickness) triples, once."""
  if layers is None:
    return None
  if not isinstance(layers, (list, tuple)):
    raise ValueError('layers must be a list or tuple')
  out = []
  for item in layers:
    if not isinstance(item, (list, tuple)):
      raise ValueError('each layer must be a list or tuple')
    if not all(_is_int(x) for x in item):
      raise ValueError('layer entries must be integers')
    if len(item) == 2:
      lay = (item[0], item[0], item[1])
    elif len(item) == 3:
      lay = (item[0], item[1], item[2])
    else:
      raise ValueError('each layer must be (k, thickness) or '
                       '(k_left, k_right, thickness)')
    if lay[2] < 1:
      raise ValueError('layer thickness must be at least 1')
    out.append(lay)
  return out


def _layers_ok(lays, pw):
  """Checks that a non-empty distractor profile is connected and never valid.

  A layer (kl, kr, th) covers the across-path range -kl .. pw-1+kr relative
  to the projectile's first column. The near layer must overlap the
  projectile's lane, and consecutive layers must overlap. If the profile is a
  single rectangle, it must have unequal margins or be a same-width bar. This
  excludes equal positive margins (a second valid target) and equal negative
  margins (the projectile would be a valid target for it).
  """
  if not lays:
    return False
  spans = []
  for kl, kr, th in lays:
    if th < 1:
      return False
    a, b = -kl, pw - 1 + kr
    if a > b:
      return False
    spans.append((a, b))
  a0, b0 = spans[0]
  if max(a0, 0) > min(b0, pw - 1):
    return False
  for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
    if max(a1, a2) > min(b1, b2):
      return False
  shapes = set((kl, kr) for kl, kr, _ in lays)
  if len(shapes) >= 2:
    return True
  kl, kr = shapes.pop()
  return kl != kr or kl == 0


def _check_scalars(direction, height, width, proj_u, proj_v, proj_w, proj_l,
                   gap, thickness, margin, dgap):
  if direction is not None and direction not in DIRS:
    raise ValueError('direction must be one of %s' % (DIRS,))
  named = (('height', height), ('width', width), ('proj_u', proj_u),
           ('proj_v', proj_v), ('proj_w', proj_w), ('proj_l', proj_l),
           ('gap', gap), ('thickness', thickness), ('margin', margin),
           ('dgap', dgap))
  for name, val in named:
    if val is not None and not _is_int(val):
      raise ValueError('%s must be an integer' % name)
  for name, val in (('height', height), ('width', width)):
    if val is not None and not 1 <= val <= 30:
      raise ValueError('%s must be in 1..30' % name)
  if proj_w is not None and (proj_w < 2 or proj_w % 2):
    raise ValueError('proj_w must be even and at least 2')
  for name, val, low in (('proj_l', proj_l, 1), ('thickness', thickness, 1),
                         ('margin', margin, 1), ('gap', gap, 0),
                         ('dgap', dgap, 0), ('proj_u', proj_u, 0),
                         ('proj_v', proj_v, 0)):
    if val is not None and val < low:
      raise ValueError('%s must be at least %d' % (name, low))


def _min_dims(p, lays, kind):
  """Returns the minimal (along, across) for fixed parameters, or None."""
  t = _dflt(p['thickness'], 1)
  g = _dflt(p['gap'], 0)
  pl = _dflt(p['proj_l'], 1)
  dg = _dflt(p['dgap'], 0)
  if lays is None:
    depth, kl, kr = 1, 0, 0
  else:
    depth = sum(th for _, _, th in lays)
    kl = max([0] + [a for a, _, _ in lays])
    kr = max([0] + [b for _, b, _ in lays])
  amin = t + g + pl + dg + depth
  if p['proj_u'] is not None:
    if p['proj_u'] < t + g:
      return None
    amin = max(amin, p['proj_u'] + pl + dg + depth)
  if kind == 'isolated':
    amin = max(amin, t + pl + depth + 1)
  if kind == 'shape':
    amin = max(amin, 2)
  pw = _dflt(p['proj_w'], 2)
  m = _dflt(p['margin'], 1)
  s = pw // 2
  ext_l, ext_r = max(m + s, kl), max(m + s, kr)
  cmin = ext_l + pw + ext_r
  if p['proj_v'] is not None:
    if p['proj_v'] < ext_l:
      return None
    cmin = max(cmin, p['proj_v'] + pw + ext_r)
  if kind is not None:
    cmin += 3 if kind == 'shape' else 2
  return amin, cmin


def _rand_dim(minimum):
  lo = max(minimum, 7)
  return random.randint(lo, max(lo, 24))


def _budget(total, fixed, caps, lows):
  """Samples the along-path sizes so that their sum fits into total."""
  vals = dict(fixed)
  keys = [k for k in ('t', 'pl', 'g', 'dg', 'depth') if k not in vals]
  rem = total - sum(vals.values())
  random.shuffle(keys)
  for i, key in enumerate(keys):
    rest = sum(lows[k] for k in keys[i + 1:])
    top = min(caps[key], rem - rest)
    if top < lows[key]:
      return None
    vals[key] = random.randint(lows[key], top)
    rem -= vals[key]
  return vals if rem >= 0 else None


def _split(total, n):
  cuts = sorted(random.sample(range(1, total), n - 1))
  bounds = [0] + cuts + [total]
  return [bounds[i + 1] - bounds[i] for i in range(n)]


def _profile(kind, pw, m, k_cap, depth):
  neg = -(pw - 1)
  if kind == 'bar':
    return [(0, 0, depth)]
  if kind == 'step':
    if depth < 2:
      return None
    n = random.randint(2, min(4, depth, k_cap + 1))
    k0 = random.choice([0, 0, 1])
    if k0 + n - 1 > k_cap:
      k0 = 0
    ks = [k0 + i for i in range(n)]
    if random.random() < 0.3:
      ks.reverse()
    return [(k, k, th) for k, th in zip(ks, _split(depth, n))]
  if kind == 'ragged':
    if depth < 2:
      return None
    n = random.randint(2, min(5, depth))
    ks = [random.randint(0, k_cap) for _ in range(n)]
    if len(set(ks)) == 1:
      i = random.randrange(n)
      ks[i] = (ks[i] + random.randint(1, k_cap)) % (k_cap + 1)
    return [(k, k, th) for k, th in zip(ks, _split(depth, n))]
  if kind == 'offset':
    n = random.randint(1, min(3, depth))
    ths = _split(depth, n)
    for _ in range(30):
      lays = [(random.randint(neg, k_cap), random.randint(neg, k_cap), th)
              for th in ths]
      if any(a != b for a, b, _ in lays) and _layers_ok(lays, pw):
        return lays
    return None
  # Hard negative: overhangs on both sides, margins differ by 1 or 2.
  base = m if random.random() < 0.6 else random.randint(1, k_cap - 1)
  delta = random.randint(1, min(2, k_cap - base))
  kl, kr = base, base + delta
  if random.random() < 0.5:
    kl, kr = kr, kl
  return [(kl, kr, depth)]


def _sample_layers(pw, m, k_cap, depth):
  """Samples a far-side distractor of total depth; extents are <= k_cap."""
  kinds = ['bar', 'step', 'ragged', 'offset', 'near']
  for _ in range(20):
    kind = random.choices(kinds, [2, 2, 1.5, 2.5, 2])[0]
    lays = _profile(kind, pw, m, k_cap, depth)
    if lays and _layers_ok(lays, pw):
      return lays
  return [(0, 0, depth)]


def _shape_cells(u0, a, v0, b):
  """Builds a connected non-rectangle (L or frame) with a full a x b box."""
  cells = set(_rect(u0, u0 + a - 1, v0, v0 + b - 1))
  if a >= 3 and b >= 3 and random.random() < 0.35:
    cells -= set(_rect(u0 + 1, u0 + a - 2, v0 + 1, v0 + b - 2))
  else:
    ra, rb = random.randint(1, a - 1), random.randint(1, b - 1)
    cu = u0 if random.random() < 0.5 else u0 + a - ra
    cv = v0 if random.random() < 0.5 else v0 + b - rb
    cells -= set(_rect(cu, cu + ra - 1, cv, cv + rb - 1))
  return sorted(cells)


def _attempt(d, p, lays, cols, forced, need_decoy, allow_decoy, decoy_side):
  """Draws one scene; returns None when a random draw does not fit.

  Uniqueness argument. The target, projectile and distractor occupy disjoint
  along-path ranges inside one across-path column. Any decoy sits outside
  that column, with a one-cell gap. Hence:
    * projectile -> target: only the target lies in the lane, with equal
      positive margins, so this pair is valid;
    * projectile -> far side: the distractor is a same-width bar, a
      non-rectangle or an unequal-margin rectangle, so it is never valid;
    * target -> projectile side: the narrower projectile is hit first;
    * rectangular distractor -> projectile: the projectile is hit first, and
      _layers_ok excludes equal negative margins;
    * sideways moves of column objects can only meet the decoy. A twin has the
      projectile's exact along extent (zero margin). An isolated block shares
      no along range with anything. A shape decoy is not a rectangle;
    * a twin moving sideways meets the projectile with zero margin, an
      isolated block meets nothing, and no lane of any decoy contains another
      object.
  """
  vert = d in ('up', 'down')
  fa, fc = (p['height'], p['width']) if vert else (p['width'], p['height'])
  if forced is not None:
    kind = forced
  elif need_decoy or (allow_decoy and random.random() < 0.45):
    kind = random.choice(DECOYS)
  else:
    kind = None
  mins = _min_dims(p, lays, kind)
  if mins is None or max(mins) > 30:
    return None
  amin, cmin = mins
  along = fa if fa is not None else _rand_dim(amin)
  across = fc if fc is not None else _rand_dim(cmin)
  if along < amin or across < cmin:
    return None
  dmin = 2 if kind == 'shape' else 1
  avail = across - (dmin + 1 if kind is not None else 0)

  if p['proj_w'] is not None:
    pw = p['proj_w']
  else:
    top = min((avail - 2 * _dflt(p['margin'], 1)) // 2, max(2, across // 3))
    if top < 2:
      return None
    pw = 2 * random.randint(1, top // 2)
  s = pw // 2
  if p['margin'] is not None:
    m = p['margin']
  else:
    top = min((avail - 2 * pw) // 2, max(1, across // 4))
    if top < 1:
      return None
    m = random.randint(1, top)
  k_cap = m + s

  fixed = {}
  for key, name in (('t', 'thickness'), ('pl', 'proj_l'), ('g', 'gap'),
                    ('dg', 'dgap')):
    if p[name] is not None:
      fixed[key] = p[name]
  if lays is not None:
    fixed['depth'] = sum(th for _, _, th in lays)
  elif kind is not None and random.random() < 0.3:
    fixed['depth'] = 0
  caps = {'t': max(1, along * 2 // 5), 'pl': max(1, along // 3),
          'g': along * 2 // 5, 'dg': along // 5,
          'depth': max(1, along // 3)}
  lows = {'t': 1, 'pl': 1, 'g': 0, 'dg': 0, 'depth': 1}
  extra = 1 if kind == 'isolated' else 0
  vals = _budget(along - extra, fixed, caps, lows)
  if vals is None:
    return None
  t, pl, g = vals['t'], vals['pl'], vals['g']
  dg, depth = vals['dg'], vals['depth']
  if p['proj_u'] is not None:
    pu = p['proj_u']
    e = pu - g - t
    if e < 0 or pu + pl + dg + depth > along:
      return None
  else:
    e = random.randint(0, along - (t + g + pl + dg + depth))
    pu = e + t + g

  if lays is not None:
    lay = lays
  elif depth == 0:
    lay = []
  else:
    lay = _sample_layers(pw, m, k_cap, depth)
  if lay and not _layers_ok(lay, pw):
    return None
  ext_l = max([m + s] + [kl for kl, _, _ in lay])
  ext_r = max([m + s] + [kr for _, kr, _ in lay])
  slack = across - pw - ext_l - ext_r
  if slack < 0:
    return None
  lo, hi = ext_l, across - pw - ext_r
  side, dw = None, 0
  if kind is not None:
    top = min(slack - 1, max(dmin, across // 4))
    if top < dmin:
      return None
    dw = random.randint(dmin, top)
    sides = [decoy_side] if decoy_side is not None else list(SIDES)
    if p['proj_v'] is not None:
      pv0 = p['proj_v']
      sides = [sd for sd in sides
               if (sd == 'low' and lo + dw + 1 <= pv0 <= hi) or
               (sd == 'high' and lo <= pv0 <= hi - dw - 1)]
    if not sides:
      return None
    side = random.choice(sides)
    if side == 'low':
      lo += dw + 1
    else:
      hi -= dw + 1
  if p['proj_v'] is not None:
    pv = p['proj_v']
    if not lo <= pv <= hi:
      return None
  else:
    pv = random.randint(lo, hi)

  pool = [c for c in range(10) if c != BG]
  cx = None
  if cols is not None:
    cp, ct, cd = cols[0], cols[1], cols[2]
    if kind is not None:
      if len(cols) == 4:
        cx = cols[3]
      else:
        cx = random.choice([c for c in pool if c not in cols])
  else:
    cp, ct, cd, cx = random.sample(pool, 4)

  proj = _rect(pu, pu + pl - 1, pv, pv + pw - 1)
  tgt = _rect(e, e + t - 1, pv - m, pv + pw - 1 + m)
  dist = []
  start = pu + pl + dg
  for kl, kr, th in lay:
    dist += _rect(start, start + th - 1, pv - kl, pv + pw - 1 + kr)
    start += th
  dec = []
  if kind is not None:
    cl, cr = pv - ext_l, pv + pw - 1 + ext_r
    if side == 'low':
      v0 = random.randint(0, cl - dw - 1)
    else:
      v0 = random.randint(cr + 2, across - dw)
    if kind == 'twin':
      dec = _rect(pu, pu + pl - 1, v0, v0 + dw - 1)
    elif kind == 'isolated':
      ds = pu + pl + dg
      bands = [(0, e - 1), (e + t, pu - 1)]
      if lay:
        bands += [(pu + pl, ds - 1), (ds + depth, along - 1)]
      else:
        bands.append((pu + pl, along - 1))
      bands = [b for b in bands if b[1] >= b[0]]
      b0, b1 = random.choice(bands)
      a = random.randint(1, min(b1 - b0 + 1, max(1, along // 3)))
      u0 = random.randint(b0, b1 - a + 1)
      dec = _rect(u0, u0 + a - 1, v0, v0 + dw - 1)
    else:
      a = random.randint(2, max(2, min(along, along // 3)))
      u0 = random.randint(0, along - a)
      dec = _shape_cells(u0, a, v0, dw)

  h, w = (along, across) if vert else (across, along)
  inp = common.grid(w, h, BG)
  _paint(inp, d, dist, cd)
  _paint(inp, d, tgt, ct)
  _paint(inp, d, proj, cp)
  if dec:
    _paint(inp, d, dec, cx)
  counts = {}
  for row in inp:
    for val in row:
      counts[val] = counts.get(val, 0) + 1
  if any(val != BG and n >= counts.get(BG, 0) for val, n in counts.items()):
    return None  # 7 must stay the majority (background) colour.
  if _valid_choices(inp) != [(cp, d)]:
    raise RuntimeError('construction invariant violated: selection is not '
                       'unique for this scene')

  left = _rect(e, e + t - 1, pv - m - s, pv - 1)
  right = _rect(e, e + t - 1, pv + pw, pv + pw - 1 + m + s)
  landed = _rect(0, pl - 1, pv, pv + pw - 1)
  out = common.grid(w, h, BG)
  _paint(out, d, dist, cd)
  _paint(out, d, left, ct)
  _paint(out, d, right, ct)
  _paint(out, d, landed, cp)
  if dec:
    _paint(out, d, dec, cx)
  return {'input': inp, 'output': out}


def generate(direction=None, height=None, width=None, colors=None,
             proj_u=None, proj_v=None, proj_w=None, proj_l=None, gap=None,
             thickness=None, margin=None, layers=None, dgap=None,
             decoy=None, decoy_side=None):
  """Builds one projectile-splits-target scene.

  Args:
    direction: 'up', 'down', 'left' or 'right', the projectile's travel.
    height: grid height (integer 1..30; random 7..24 conditioned on fit).
    width: grid width (integer 1..30; random 7..24 conditioned on fit).
    colors: list/tuple (projectile, target, distractor[, decoy]) of
      distinct colours other than 7. Giving a 4th colour requests a decoy.
    proj_u: distance from the destination edge to the projectile's near side.
    proj_v: across-path start coordinate of the projectile.
    proj_w: projectile width across the path (even, at least 2).
    proj_l: projectile length along the path.
    gap: number of empty cells between the target and the projectile.
    thickness: target thickness along the path.
    margin: target overhang on each side of the projectile.
    layers: list/tuple of far-side distractor layers, ordered from near to
      far. Each layer is a (half extension, thickness) pair or a (left
      extension, right extension, thickness) triple, and extensions may be
      negative. An empty list means there is no distractor.
    dgap: number of empty cells between the projectile and the distractor.
    decoy: None (random), 'none', 'twin', 'isolated' or 'shape'.
    decoy_side: 'low' or 'high' across-path side for the decoy.
  """
  cols = _parse_colors(colors)
  lays = _parse_layers(layers)
  _check_scalars(direction, height, width, proj_u, proj_v, proj_w, proj_l,
                 gap, thickness, margin, dgap)
  if decoy is not None and decoy != 'none' and decoy not in DECOYS:
    raise ValueError('decoy must be None, none, twin, isolated or shape')
  if decoy_side is not None and decoy_side not in SIDES:
    raise ValueError('decoy_side must be low or high')
  if decoy == 'none' and (decoy_side is not None or
                          (cols is not None and len(cols) == 4)):
    raise ValueError('decoy_side or a 4th colour conflicts with decoy=none')
  forced = decoy if decoy in DECOYS else None
  need_decoy = (forced is not None or decoy_side is not None or
                (cols is not None and len(cols) == 4))
  allow_decoy = decoy != 'none'
  if lays:
    widths = [proj_w] if proj_w is not None else list(range(2, 29, 2))
    if not any(_layers_ok(lays, wv) for wv in widths):
      raise ValueError('layers must form one connected distractor that is a '
                       'same-width bar, a non-rectangle or unequal-margin')
  p = {'height': height, 'width': width, 'proj_u': proj_u, 'proj_v': proj_v,
       'proj_w': proj_w, 'proj_l': proj_l, 'gap': gap,
       'thickness': thickness, 'margin': margin, 'dgap': dgap}
  req = forced if forced is not None else ('twin' if need_decoy else None)
  mins = _min_dims(p, lays, req)
  if mins is None:
    raise ValueError('proj_u/proj_v conflict with the fixed geometry')
  amin, cmin = mins
  feas = []
  for d in ([direction] if direction is not None else list(DIRS)):
    fa, fc = (height, width) if d in ('up', 'down') else (width, height)
    if amin > 30 or cmin > 30:
      continue
    if (fa is not None and fa < amin) or (fc is not None and fc < cmin):
      continue
    feas.append(d)
  if not feas:
    raise ValueError('requested dimensions cannot hold the scene geometry')
  for _ in range(MAX_TRIES):
    res = _attempt(random.choice(feas), p, lays, cols, forced, need_decoy,
                   allow_decoy, decoy_side)
    if res is not None:
      return res
  raise ValueError('could not construct a valid scene with these parameters')


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(direction='up', height=10, width=10, colors=(3, 9, 8),
               proj_u=4, proj_v=4, proj_w=2, proj_l=2, gap=0, thickness=2,
               margin=1, layers=[(0, 4)], dgap=0, decoy='none'),
      generate(direction='down', height=10, width=10, colors=(1, 8, 6),
               proj_u=4, proj_v=4, proj_w=2, proj_l=3, gap=0, thickness=4,
               margin=2, layers=[(0, 1), (1, 2)], dgap=0, decoy='none'),
      generate(direction='left', height=10, width=10, colors=(1, 4, 2),
               proj_u=6, proj_v=4, proj_w=2, proj_l=2, gap=4, thickness=1,
               margin=1, layers=[(1, 1), (2, 1)], dgap=0, decoy='none'),
  ]
  test = [
      generate(direction='right', height=10, width=10, colors=(9, 8, 2),
               proj_u=4, proj_v=2, proj_w=2, proj_l=2, gap=2, thickness=2,
               margin=1, layers=[(0, 2), (1, 1), (2, 1)], dgap=0,
               decoy='none'),
  ]
  return {'train': train, 'test': test}
