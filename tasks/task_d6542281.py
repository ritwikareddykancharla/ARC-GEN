"""ARC task d6542281: complete fragments into full copies of their templates.

Rule: the grid has one background colour, which is the strict plurality colour.
It also has some multicoloured 8-connected shapes (templates) and some
single-colour 8-connected pieces (fragments). Each fragment is an exact
translated copy of a same-colour part of one template. There is no rotation.
The output keeps the input and stamps the whole template at the translation
where the fragment, together with its sibling fragments, fits.

Erase quirk: before stamping, any non-background colour that occurs exactly
once in the input is erased. This comes from training pair 3, where the
template's single 3-cell disappears but the stamped copies still carry their 3.

Arrangement semantics (what makes an input determined). An arrangement is a
set of stamps (a template copied at a translation) such that:
  * every footprint lies inside the grid and neither overlaps nor 8-touches
    any template cell;
  * every non-background input cell inside a footprint is a fragment cell
    with the colour of the template cell there, and every fragment component
    that meets a footprint lies wholly inside it (the stamp covers it);
  * every fragment component is covered by exactly one stamp;
  * no two footprints overlap or 8-touch.
Every emitted scene has exactly one arrangement, and it equals the latent
stamps. An exhaustive search certifies this within a node budget. A scene
whose search runs out of budget is rejected; it is never reported as unique.
Uniquely matching one site's union on its own is not enough. The search
also rules out alternative arrangements that explain the siblings
separately.

Scope:
- Templates: 1-3 random 8-connected templates by default, or 1-4 on request.
  Each fits in a box of up to 5x5, has 3-12 cells and 2-4 colours, and sits on
  a random background.
- Stamp sites: each template gets 1-3 sites. The count is reduced on crowded
  grids. A site shows one single-colour fragment of 1-3 cells, or sometimes
  two separated fragments of the same stamp. Templates with several shown
  sites act as competing candidates for every fragment.
- Joint resolution (train pair 2 mechanism): one site shows a fragment that
  fits two or more places on its own. A separated sibling fragment of the same
  stamp makes the union fit exactly once.
    * 'other' (hard): the ambiguous fragment avoids the template's row-major
      first cell (its seed). Its alternative placements may lie in the same
      template or in other templates, and the sibling may itself be ambiguous.
      The final scene is checked as well: the ambiguous component must still
      have two or more admissible stamps, so only the joint arrangement fixes
      it. Attempts first prefer cases where the true placement is not the
      first one met in template scan order, which misleads first-match
      readers. Canonical train pair 2 is this kind.
    * 'seed' (easy): the ambiguous fragment covers the seed cell, and its
      colour is used by no other template.
- Default mix (joint=None, joint_anchor=None). Each scene-level sample picks:
    * 'other' with probability 0.55;
    * 'seed' with probability 0.15;
    * no joint site with probability 0.30.
  A sample that keeps failing is redrawn whole. joint=True without an anchor
  means 'other'. An explicitly requested anchor is never replaced: if it
  cannot be built, generate() raises ValueError.
- Distractor (synthetic extension): with two or more templates, about 30% of
  random scenes leave one template without any fragment. It stays unchanged
  and is never stamped.
- Erase quirk: in about a quarter of random scenes, one unshown template cell
  gets a fresh marker colour that occurs exactly once, so the quirk is
  exercised. Otherwise no colour occurs exactly once.
- Layout: all object bounding boxes keep a background gap between them. Stamps
  lie fully inside the grid, and no completed object touches another one.
- Grid sides: 10-30 by default, 6-30 on request. Sides above 24 and the
  random blob templates are synthetic extensions of the fixtures.

Not supported:
- Scenes whose fragments admit several arrangements. They are rejected.
- Rotated or reflected fragments.
"""

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

import random

import common

_DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# The smallest random template box is 2x2. With its gap it covers 3x3 = 9
# cells (counted on a (rows+1) x (cols+1) board).
_MIN_BOX_AREA = 9
# Preferred and hard crowding limits, as fractions of the padded board area.
_SOFT_FILL = 0.55
_HARD_FILL = 0.8
# Node budget of the global arrangement search. A scene that exhausts it is
# rejected and is never reported as uniquely determined.
_SEARCH_BUDGET = 50000
# Default joint mix for each scene-level sample: 'other', then 'seed'; the
# rest has no joint site.
_P_OTHER = 0.55
_P_SEED = 0.15


class _Exhausted(Exception):
  """Raised when the arrangement search exceeds its node budget."""


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _parse(pattern):
  cells = {}
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch != '.':
        cells[(r, c)] = int(ch)
  return cells


def _to_pattern(cells):
  h = max(r for r, _ in cells) + 1
  w = max(c for _, c in cells) + 1
  rows = []
  for r in range(h):
    rows.append(''.join(str(cells[(r, c)]) if (r, c) in cells else '.'
                        for c in range(w)))
  return rows


def _dims(cells):
  return (max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1)


def _neighbors(r, c):
  for dr, dc in _DIRS:
    yield (r + dr, c + dc)


def _components(cells):
  """8-connected components of a dict position -> colour."""
  seen, comps = set(), []
  for p in sorted(cells):
    if p in seen:
      continue
    seen.add(p)
    stack, comp = [p], []
    while stack:
      q = stack.pop()
      comp.append(q)
      for n in _neighbors(*q):
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
    comps.append(comp)
  return comps


def _placements(piece, templates):
  """All (template, dr, dc) where piece fits on same-colour template cells."""
  items = sorted(piece.items())
  (r0, c0), col0 = items[0]
  found = []
  for ti, t in enumerate(templates):
    for (tr, tc), tcol in t.items():
      if tcol != col0:
        continue
      dr, dc = r0 - tr, c0 - tc
      if all(t.get((r - dr, c - dc)) == col for (r, c), col in items):
        found.append((ti, dr, dc))
  return found


def _match_count(piece, templates):
  return len(_placements(piece, templates))


def _random_template(bg, max_h, max_w):
  """Random 8-connected shape with 2-4 colours inside max_h x max_w."""
  for _ in range(100):
    h = random.randint(min(2, max_h), max_h)
    w = random.randint(min(2, max_w), max_w)
    if h * w < 3:
      continue
    n = random.randint(3, min(12, h * w))
    shape = {(random.randrange(h), random.randrange(w))}
    for _ in range(400):
      if len(shape) >= n:
        break
      r, c = random.choice(sorted(shape))
      dr, dc = random.choice(_DIRS)
      if 0 <= r + dr < h and 0 <= c + dc < w:
        shape.add((r + dr, c + dc))
    if len(shape) < 3:
      continue
    mr = min(r for r, _ in shape)
    mc = min(c for _, c in shape)
    shape = sorted((r - mr, c - mc) for r, c in shape)
    if len(shape) >= 6:
      k = random.choice([2, 2, 3, 3, 4])
    elif len(shape) >= 4:
      k = random.choice([2, 2, 3])
    else:
      k = 2
    colours = random.sample([c for c in range(10) if c != bg], k)
    cells = list(shape)
    random.shuffle(cells)
    weights = [3, 1, 1, 1][:k]
    t = {}
    for i, p in enumerate(cells):
      t[p] = colours[i] if i < k else random.choices(colours, weights)[0]
    return t
  return None


def _random_piece(t, forbidden):
  """A connected single-colour piece of template t avoiding forbidden cells."""
  colour = random.choice(sorted(set(t.values())))
  options = [p for p, cl in t.items() if cl == colour and p not in forbidden]
  if not options:
    return None
  piece = {random.choice(sorted(options))}
  size = random.randint(1, 3)
  for _ in range(10):
    if len(piece) >= size:
      break
    cand = sorted({n for p in piece for n in _neighbors(*p)
                   if t.get(n) == colour and n not in piece
                   and n not in forbidden})
    if not cand:
      break
    piece.add(random.choice(cand))
  return piece


def _random_visible(t, templates):
  """Fragment cells for one stamp. Each component must match exactly once."""
  for _ in range(40):
    first = _random_piece(t, set())
    if first is None:
      continue
    visible = set(first)
    if random.random() < 0.25:
      forbidden = set(first)
      for p in first:
        forbidden.update(_neighbors(*p))
      second = _random_piece(t, forbidden)
      if second:
        visible |= second
    vis = {p: t[p] for p in visible}
    ok = True
    for comp in _components(vis):
      piece = {p: vis[p] for p in comp}
      if len(set(piece.values())) != 1 or _match_count(piece, templates) != 1:
        ok = False
        break
    if ok:
      return sorted(visible)
  return None


def _prepare_joint(t, others, bg):
  """Recolours t in place so a seed-anchored joint site is possible.

  Afterwards the colour of t's row-major first cell (its seed) is used by no
  other template and occurs at least twice in t.
  """
  seed = min(t)
  old = t[seed]
  used_else = {c for o in others for c in o.values()}
  if old in used_else:
    own = set(t.values()) - {old}
    free = [c for c in range(10)
            if c != bg and c not in used_else and c not in own]
    if not free:
      return False
    new = random.choice(free)
    for p in t:
      if t[p] == old:
        t[p] = new
  col = t[seed]
  if sum(1 for v in t.values() if v == col) >= 2:
    return True
  cand = sorted(p for p in t if p != seed and t[p] != col)
  random.shuffle(cand)
  for p in cand:
    prev = t[p]
    t[p] = col
    if len(set(t.values())) >= 2:
      return True
    t[p] = prev
  return False


def _random_joint_visible(t, ti, templates):
  """Seed-anchored joint stamp: returns (visible cells, ambiguous cells).

  The ambiguous component contains the template's seed cell and fits two or
  more places, all inside template ti. A separated sibling component fits
  exactly once, so the union fits exactly once.
  """
  seed = min(t)
  colour = t[seed]
  for _ in range(40):
    piece = {seed}
    if random.random() < 0.4:
      cand = sorted(n for n in _neighbors(*seed) if t.get(n) == colour)
      if cand:
        piece.add(random.choice(cand))
    found = _placements({p: colour for p in piece}, templates)
    if len(found) < 2 or any(f[0] != ti for f in found):
      continue
    forbidden = set(piece)
    for p in piece:
      forbidden.update(_neighbors(*p))
    second = _random_piece(t, forbidden)
    if not second:
      continue
    if _match_count({p: t[p] for p in second}, templates) != 1:
      continue
    return sorted(piece | second), sorted(piece)
  return None


def _random_joint_visible_other(t, ti, templates):
  """Hard joint stamp away from the seed: (visible cells, ambiguous cells).

  The ambiguous component avoids t's row-major first cell and fits two or
  more places in any template. A separated sibling component, which may
  itself be ambiguous, is added. Together with it, the union of the visible
  cells fits only the true placement (template ti, zero relative shift). The
  first attempts insist that the true placement is not the first candidate
  in template scan order (a decoy comes first).
  """
  seed = min(t)
  tally = {}
  for v in t.values():
    tally[v] = tally.get(v, 0) + 1
  colours = sorted(c for c, n in tally.items() if n >= 2)
  if not colours:
    return None
  for attempt in range(60):
    colour = random.choice(colours)
    options = sorted(p for p, cl in t.items() if cl == colour and p != seed)
    if not options:
      continue
    start = random.choice(options)
    piece = {start}
    if random.random() < 0.4:
      cand = sorted(n for n in _neighbors(*start)
                    if t.get(n) == colour and n != seed)
      if cand:
        piece.add(random.choice(cand))
    found = _placements({p: colour for p in piece}, templates)
    if len(found) < 2:
      continue
    if attempt < 30 and found[0] == (ti, 0, 0):
      continue
    forbidden = set(piece)
    for p in piece:
      forbidden.update(_neighbors(*p))
    second = _random_piece(t, forbidden)
    if not second:
      continue
    union = piece | second
    vis = {p: t[p] for p in union}
    if _placements(vis, templates) != [(ti, 0, 0)]:
      continue
    return sorted(union), sorted(piece)
  return None


def _separated(a, b):
  return (a[0] > b[2] + 1 or b[0] > a[2] + 1 or
          a[1] > b[3] + 1 or b[1] > a[3] + 1)


def _add_marker(tmaps, sites, counts, bg):
  """Recolour one unshown template cell to a fresh colour occurring once."""
  free = [c for c in range(10) if c != bg and c not in counts]
  if not free:
    return False
  options = []
  for ti, t in enumerate(tmaps):
    shown = set()
    for sti, vis in sites:
      if sti == ti:
        shown.update(vis)
    for p, col in t.items():
      # The old colour must still occur at least twice afterwards.
      if p not in shown and counts[col] >= 3:
        options.append((ti, p))
  if not options:
    return False
  ti, p = random.choice(options)
  marker = random.choice(free)
  counts[tmaps[ti][p]] -= 1
  tmaps[ti][p] = marker
  counts[marker] = 1
  return True


def _place(tmaps, sites, height, width):
  """Place template and stamp boxes with background gaps between them."""
  items = [('t', i) for i in range(len(tmaps))]
  items += [('s', j) for j in range(len(sites))]
  random.shuffle(items)
  placed, pos = [], {}
  for kind, idx in items:
    ti = idx if kind == 't' else sites[idx][0]
    h, w = _dims(tmaps[ti])
    if h > height or w > width:
      return None
    found = None
    for _ in range(150):
      top = random.randint(0, height - h)
      left = random.randint(0, width - w)
      box = (top, left, top + h - 1, left + w - 1)
      if all(_separated(box, o) for o in placed):
        found = box
        break
    if found is None:
      return None
    placed.append(found)
    pos[(kind, idx)] = (found[0], found[1])
  return pos


def _try_scene(rows, cols, bg, nt, want_marker, want_distractor, mode):
  """One construction attempt with fixed size, background, count and mode.

  mode is None (no joint site), 'seed' or 'other'. Returns
  ((rows, cols, bg, templates, stamps), joint_info) or None. joint_info is
  (stamp index, template-relative ambiguous cells) for the joint site.
  """
  cap = min(5, (max(rows, cols) - 1) // 2, rows, cols)
  tmaps = []
  for _ in range(nt):
    t = _random_template(bg, cap, cap)
    if t is None:
      return None
    tmaps.append(t)
  dims = [_dims(t) for t in tmaps]
  per = [random.choice([1, 1, 2, 2, 3]) for _ in range(nt)]
  if want_distractor:
    per[random.randrange(nt)] = 0
  area = (rows + 1) * (cols + 1)

  def need():
    return sum((h + 1) * (w + 1) * (1 + k) for (h, w), k in zip(dims, per))

  while need() > _SOFT_FILL * area:
    cand = [i for i, k in enumerate(per) if k > 1]
    if not cand:
      break
    per[random.choice(cand)] -= 1
  if need() > _HARD_FILL * area:
    return None
  joint_t = None
  if mode is not None:
    cand = [i for i, k in enumerate(per) if k >= 1]
    if not cand:
      return None
    joint_t = random.choice(cand)
    if mode == 'seed':
      others = [tmaps[i] for i in range(nt) if i != joint_t]
      if not _prepare_joint(tmaps[joint_t], others, bg):
        return None
  sites, joint_info = [], None
  for ti in range(nt):
    for k in range(per[ti]):
      if ti == joint_t and k == 0:
        if mode == 'seed':
          res = _random_joint_visible(tmaps[ti], ti, tmaps)
        else:
          res = _random_joint_visible_other(tmaps[ti], ti, tmaps)
        if res is None:
          return None
        vis, amb = res
        joint_info = (len(sites), amb)
      else:
        vis = _random_visible(tmaps[ti], tmaps)
        if vis is None:
          return None
      sites.append((ti, vis))
  if not sites:
    return None
  counts = {}
  for t in tmaps:
    for col in t.values():
      counts[col] = counts.get(col, 0) + 1
  for ti, vis in sites:
    for p in vis:
      counts[tmaps[ti][p]] = counts.get(tmaps[ti][p], 0) + 1
  if any(n == 1 for n in counts.values()):
    return None
  # Recolouring an unshown cell only removes match candidates. The scene-level
  # check in _certified rejects a marker that removes the joint ambiguity.
  if want_marker and not _add_marker(tmaps, sites, counts, bg):
    return None
  # The background must be the strict plurality colour.
  if rows * cols - sum(counts.values()) <= max(counts.values()):
    return None
  pos = _place(tmaps, sites, rows, cols)
  if pos is None:
    return None
  templates = [(pos[('t', i)][0], pos[('t', i)][1], _to_pattern(tmaps[i]))
               for i in range(nt)]
  stamps = [(ti, pos[('s', j)][0], pos[('s', j)][1], vis)
            for j, (ti, vis) in enumerate(sites)]
  return (rows, cols, bg, templates, stamps), joint_info


def _admissible(foot, height, width, t_halo, frag, comp_of, comps):
  """Fragment components covered by a candidate footprint, or None."""
  cov = set()
  for p, v in foot.items():
    if not (0 <= p[0] < height and 0 <= p[1] < width):
      return None
    if p in t_halo:
      return None
    if p in frag:
      if frag[p] != v:
        return None
      cov.add(comp_of[p])
  for k in cov:
    if not all(q in foot for q in comps[k]):
      return None
  return frozenset(cov) if cov else None


def _analyse(height, width, templates, tmaps, stamps):
  """Enumerates the full arrangements of the input picture of a latent scene.

  Only the picture is used: template cells, fragment cells and colours.
  Returns the fragment components, the admissible stamp options of each
  component, the candidate footprints, up to two arrangements, and whether
  the search finished within its budget.
  """
  tcells = set()
  for (top, left, _), t in zip(templates, tmaps):
    for r, c in t:
      tcells.add((top + r, left + c))
  frag = {}
  for ti, top, left, visible in stamps:
    for r, c in visible:
      frag[(top + r, left + c)] = tmaps[ti][(r, c)]
  comps = [frozenset(comp) for comp in _components(frag)]
  comp_of = {}
  for k, comp in enumerate(comps):
    for p in comp:
      comp_of[p] = k
  t_halo = set(tcells)
  for p in tcells:
    t_halo.update(_neighbors(*p))
  seen, foots, cells, halos, covers = set(), [], [], [], []
  options = [[] for _ in comps]
  for comp in comps:
    r0, c0 = min(comp)
    col0 = frag[(r0, c0)]
    for t in tmaps:
      for (tr, tc), tcol in t.items():
        if tcol != col0:
          continue
        top, left = r0 - tr, c0 - tc
        foot = {(top + r, left + c): v for (r, c), v in t.items()}
        key = frozenset(foot.items())
        if key in seen:
          continue
        seen.add(key)
        cov = _admissible(foot, height, width, t_halo, frag, comp_of, comps)
        if cov is None:
          continue
        sid = len(foots)
        foots.append(key)
        cells.append(set(foot))
        halo = set(foot)
        for p in foot:
          halo.update(_neighbors(*p))
        halos.append(halo)
        covers.append(cov)
        for kk in cov:
          options[kk].append(sid)
  solutions, nodes = [], [0]
  n = len(comps)

  def search(covered, chosen):
    nodes[0] += 1
    if nodes[0] > _SEARCH_BUDGET:
      raise _Exhausted()
    if len(covered) == n:
      solutions.append(list(chosen))
      return len(solutions) >= 2
    best = None
    for k in range(n):
      if k in covered:
        continue
      opts = [s for s in options[k]
              if covers[s].isdisjoint(covered) and
              all(halos[s].isdisjoint(cells[o]) for o in chosen)]
      if not opts:
        return False
      if best is None or len(opts) < len(best):
        best = opts
    for s in best:
      chosen.append(s)
      if search(covered | covers[s], chosen):
        return True
      chosen.pop()
    return False

  try:
    search(frozenset(), [])
    finished = True
  except _Exhausted:
    finished = False
  return {'comps': comps, 'options': options, 'foots': foots,
          'solutions': solutions, 'finished': finished}


def _certified(scene, joint_info):
  """Full latent check plus scene-level ambiguity of a joint fragment."""
  rows, cols, bg, templates, stamps = scene
  tlist, slist = _normalise(templates, stamps)
  tmaps = [_parse(p) for _, _, p in tlist]
  try:
    info = _check_scene(rows, cols, bg, tlist, slist, tmaps)
  except ValueError:
    return False
  if joint_info is None:
    return True
  j, amb = joint_info
  _, top, left, _ = slist[j]
  cells = frozenset((top + r, left + c) for r, c in amb)
  for k, comp in enumerate(info['comps']):
    if comp == cells:
      # The true stamp plus at least one admissible alternative.
      return len(info['options'][k]) >= 2
  return False


def _random_scene(height, width, background, num_templates, erase_marker,
                  distractor, joint, joint_anchor):
  # The outer loop samples the scene-level settings, and the inner loop keeps
  # them fixed. Rejections therefore barely bias the sampled settings.
  fixed = (height is not None and width is not None and
           num_templates is not None)
  if joint is False:
    forced = 'none'
  elif joint_anchor is not None:
    forced = joint_anchor
  elif joint is True:
    forced = 'other'
  else:
    forced = None
  for _ in range(60):
    rows = height if height is not None else random.randint(10, 30)
    cols = width if width is not None else random.randint(10, 30)
    bg = background if background is not None else random.randint(0, 9)
    nt = num_templates
    if nt is None:
      nt = random.choice([2, 2, 3]) if distractor else random.choice(
          [1, 2, 2, 3])
    want_distractor = distractor
    if want_distractor is None:
      want_distractor = nt >= 2 and random.random() < 0.3
    # Necessary condition: every template box and every stamp box (at least
    # one per non-distractor template) needs a padded 3x3 area.
    boxes = 2 * nt - (1 if want_distractor else 0)
    if boxes * _MIN_BOX_AREA > _HARD_FILL * (rows + 1) * (cols + 1):
      if fixed and distractor is not None:
        raise ValueError('grid too small for %d templates' % nt)
      if fixed and not want_distractor:
        raise ValueError('grid too small for %d templates' % nt)
      continue
    want_marker = erase_marker
    if want_marker is None:
      want_marker = random.random() < 0.25
    if forced is None:
      u = random.random()
      if u < _P_OTHER:
        mode = 'other'
      elif u < _P_OTHER + _P_SEED:
        mode = 'seed'
      else:
        mode = None
    else:
      mode = None if forced == 'none' else forced
    for _ in range(40):
      built = _try_scene(rows, cols, bg, nt, want_marker, want_distractor,
                         mode)
      if built is not None and _certified(*built):
        return built[0]
  if forced in ('other', 'seed'):
    raise ValueError('could not build a d6542281 scene with a %r-anchored '
                     'joint site under these settings; no other anchor is '
                     'substituted. Try a larger grid or fewer templates'
                     % forced)
  raise ValueError('could not fit a d6542281 scene with these settings; '
                   'try a larger grid or fewer templates')


def _normalise(templates, stamps):
  """Type-checks explicit latent parameters; returns tuples/lists copies."""
  if not isinstance(templates, (list, tuple)) or not templates:
    raise ValueError('templates must be a non-empty list')
  if not isinstance(stamps, (list, tuple)) or not stamps:
    raise ValueError('stamps must be a non-empty list')
  tlist = []
  for item in templates:
    if not isinstance(item, (list, tuple)) or len(item) != 3:
      raise ValueError('each template is (top, left, pattern)')
    top, left, pattern = item
    if not _is_int(top) or not _is_int(left):
      raise ValueError('template top/left must be integers')
    if (not isinstance(pattern, (list, tuple)) or not pattern or
        not all(isinstance(s, str) for s in pattern)):
      raise ValueError('template pattern must be a list of strings')
    for s in pattern:
      for ch in s:
        if ch != '.' and ch not in '0123456789':
          raise ValueError('pattern characters must be digits or a dot')
    tlist.append((top, left, list(pattern)))
  slist = []
  for item in stamps:
    if not isinstance(item, (list, tuple)) or len(item) != 4:
      raise ValueError('each stamp is (template_index, top, left, visible)')
    ti, top, left, visible = item
    if not (_is_int(ti) and _is_int(top) and _is_int(left)):
      raise ValueError('stamp index/top/left must be integers')
    if not isinstance(visible, (list, tuple)) or not visible:
      raise ValueError('each stamp needs at least one visible cell')
    cells = []
    for p in visible:
      if (not isinstance(p, (list, tuple)) or len(p) != 2 or
          not _is_int(p[0]) or not _is_int(p[1])):
        raise ValueError('visible cells are (row, col) integer pairs')
      cells.append((p[0], p[1]))
    if len(set(cells)) != len(cells):
      raise ValueError('duplicate visible cell')
    slist.append((ti, top, left, cells))
  return tlist, slist


def _check_scene(height, width, background, templates, stamps, tmaps):
  """Raises ValueError unless the latent scene is a valid, determined input.

  Returns the arrangement analysis of the input picture.
  """
  for name, v, lo, hi in (('height', height, 1, 30),
                          ('width', width, 1, 30),
                          ('background', background, 0, 9)):
    if not _is_int(v) or not lo <= v <= hi:
      raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))
  owner, colour_at = {}, {}
  for i, ((top, left, _), t) in enumerate(zip(templates, tmaps)):
    if not t:
      raise ValueError('empty template')
    if len(set(t.values())) < 2:
      raise ValueError('each template needs two or more colours')
    if background in t.values():
      raise ValueError('template uses the background colour')
    if len(_components(t)) != 1:
      raise ValueError('each template must be 8-connected')
    for (r, c), col in t.items():
      p = (top + r, left + c)
      if not (0 <= p[0] < height and 0 <= p[1] < width):
        raise ValueError('template cell outside the grid')
      if p in owner:
        raise ValueError('templates overlap')
      owner[p] = ('t', i)
      colour_at[p] = col
  for j, (ti, top, left, visible) in enumerate(stamps):
    if not 0 <= ti < len(tmaps):
      raise ValueError('stamp refers to a missing template')
    t = tmaps[ti]
    vis, absolute = {}, {}
    for r, c in visible:
      if (r, c) not in t:
        raise ValueError('visible cell is not a template cell')
      p = (top + r, left + c)
      if not (0 <= p[0] < height and 0 <= p[1] < width):
        raise ValueError('visible cell outside the grid')
      if p in owner:
        raise ValueError('visible cell overlaps another object')
      owner[p] = ('s', j)
      colour_at[p] = t[(r, c)]
      vis[(r, c)] = t[(r, c)]
      absolute[p] = t[(r, c)]
    for comp in _components(vis):
      if len({vis[q] for q in comp}) != 1:
        raise ValueError('a fragment component must be single-coloured')
    # The visible cells together must determine template and shift.
    if _placements(absolute, tmaps) != [(ti, top, left)]:
      raise ValueError('stamp %d is not uniquely determined by its '
                       'visible cells' % j)
  for p, who in owner.items():
    for n in _neighbors(*p):
      if n in owner and owner[n] != who:
        raise ValueError('distinct objects touch (8-connectivity)')
  # Completed layout: footprints in the grid, disjoint and non-touching.
  out_owner = {}
  for i, ((top, left, _), t) in enumerate(zip(templates, tmaps)):
    for r, c in t:
      out_owner[(top + r, left + c)] = ('t', i)
  for j, (ti, top, left, _) in enumerate(stamps):
    for r, c in tmaps[ti]:
      p = (top + r, left + c)
      if not (0 <= p[0] < height and 0 <= p[1] < width):
        raise ValueError('stamp footprint leaves the grid')
      if p in out_owner:
        raise ValueError('stamp would overwrite another object or stamp')
      out_owner[p] = ('s', j)
  for p, who in out_owner.items():
    for n in _neighbors(*p):
      if n in out_owner and out_owner[n] != who:
        raise ValueError('completed objects would touch (8-connectivity)')
  counts = {}
  for col in colour_at.values():
    counts[col] = counts.get(col, 0) + 1
  if counts and height * width - len(colour_at) <= max(counts.values()):
    raise ValueError('background must be the strict plurality colour')
  # Global determinacy: the whole picture must admit exactly one arrangement.
  info = _analyse(height, width, templates, tmaps, stamps)
  if not info['finished']:
    raise ValueError('arrangement search exhausted its budget; uniqueness '
                     'is not certified')
  if len(info['solutions']) != 1:
    raise ValueError('the fragments admit %s full arrangements' %
                     ('no' if not info['solutions'] else 'several'))
  latent = set()
  for ti, top, left, _ in stamps:
    latent.add(frozenset(((top + r, left + c), v)
                         for (r, c), v in tmaps[ti].items()))
  if {info['foots'][s] for s in info['solutions'][0]} != latent:
    raise ValueError('the unique arrangement differs from the latent stamps')
  return info


def generate(height=None, width=None, background=None, templates=None,
             stamps=None, num_templates=None, erase_marker=None,
             distractor=None, joint=None, joint_anchor=None):
  """Returns an input/output pair for task d6542281.

  Args:
    height: number of grid rows. Random mode: 6-30, sampled from 10-30 if
      None. Explicit mode: 1-30, required.
    width: number of grid columns. Same ranges as height.
    background: background colour (0-9). Sampled if None in random mode;
      required with templates.
    templates: list of (top, left, pattern) multicoloured shapes. Each pattern
      is a list of strings, with digits for colours and '.' for empty cells.
      None means build a random scene.
    stamps: list of (template_index, top, left, visible). visible lists the
      template-relative cells shown as fragments in the input. The output
      stamps the full template at (top, left). Required with templates and
      rejected without them. The visible cells must together determine the
      template and shift uniquely. The footprint must lie in the grid without
      touching other objects. The whole picture must admit exactly one
      arrangement (see the module docstring).
    num_templates: random mode only. Number of templates (1-4).
    erase_marker: random mode only. True forces a once-occurring marker cell
      in a template, which is erased in the output. False forbids it. None
      picks one at random (about 25%).
    distractor: random mode only. True forces exactly one template with no
      fragment, which needs 2 or more templates. False forbids it. None picks
      one at random (about 30% when there are 2 or more templates).
    joint: random mode only. True forces one stamp whose ambiguous fragment
      is resolved jointly with a sibling fragment. Without joint_anchor this
      is the hard 'other' style. False makes every fragment component unique
      on its own. None samples the default mix: about 55% 'other', 15%
      'seed' and 30% no joint site.
    joint_anchor: random mode only. 'other' (hard) keeps the ambiguous
      fragment off the template's row-major first cell, with candidates in
      any template, like canonical train pair 2. 'seed' (easy) anchors it on
      that cell with a template-private colour. An explicit anchor is never
      replaced by another one: ValueError is raised if it cannot be built.
      Incompatible with joint=False.
  """
  if templates is None:
    if stamps is not None:
      raise ValueError('stamps require explicit templates')
    for name, v, lo, hi in (('height', height, 6, 30),
                            ('width', width, 6, 30),
                            ('background', background, 0, 9),
                            ('num_templates', num_templates, 1, 4)):
      if v is not None and (not _is_int(v) or not lo <= v <= hi):
        raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))
    for name, v in (('erase_marker', erase_marker),
                    ('distractor', distractor), ('joint', joint)):
      if v is not None and not isinstance(v, bool):
        raise ValueError('%s must be True, False or None' % name)
    if joint_anchor is not None and joint_anchor not in ('seed', 'other'):
      raise ValueError("joint_anchor must be 'seed', 'other' or None")
    if joint_anchor is not None and joint is False:
      raise ValueError('joint_anchor needs a joint site; do not pass '
                       'joint=False')
    if distractor and num_templates == 1:
      raise ValueError('a distractor needs num_templates >= 2')
    height, width, background, templates, stamps = _random_scene(
        height, width, background, num_templates, erase_marker, distractor,
        joint, joint_anchor)
  else:
    if stamps is None or height is None or width is None or background is None:
      raise ValueError('explicit templates need height, width, background and '
                       'stamps')
    if (num_templates is not None or erase_marker is not None or
        distractor is not None or joint is not None or
        joint_anchor is not None):
      raise ValueError('num_templates/erase_marker/distractor/joint/'
                       'joint_anchor are random-mode controls')
  templates, stamps = _normalise(templates, stamps)
  tmaps = [_parse(p) for _, _, p in templates]
  _check_scene(height, width, background, templates, stamps, tmaps)
  grid = common.grid(width, height, background)
  if len(grid) != height or any(len(row) != width for row in grid):
    raise ValueError('common.grid returned an unexpected shape')
  for (top, left, _), t in zip(templates, tmaps):
    for (r, c), col in t.items():
      grid[top + r][left + c] = col
  for ti, top, left, visible in stamps:
    for r, c in visible:
      grid[top + r][left + c] = tmaps[ti][(r, c)]
  output = [row[:] for row in grid]
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  for r in range(height):
    for c in range(width):
      v = grid[r][c]
      if v != background and counts[v] == 1:
        output[r][c] = background
  for ti, top, left, _ in stamps:
    for (r, c), col in tmaps[ti].items():
      output[top + r][left + c] = col
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=19, width=19, background=2,
               templates=[(2, 3, ['11.', '14.', '..1']),
                          (12, 6, ['3.8', '38.', '333'])],
               stamps=[(0, 9, 13, [(1, 1)]),
                       (1, 3, 11, [(0, 2), (1, 1)])]),
      generate(height=13, width=13, background=1,
               templates=[(1, 1, ['22..', '24..', '..42', '..28'])],
               stamps=[(0, 8, 5, [(1, 1), (3, 3)])]),
      generate(height=13, width=13, background=8,
               templates=[(1, 0, ['1...', '.2.1', '..21', '.113'])],
               stamps=[(0, 2, 9, [(1, 1), (2, 2)]),
                       (0, 7, 4, [(1, 1), (2, 2)])]),
  ]
  test = [
      generate(height=24, width=24, background=8,
               templates=[(4, 1, ['6....', '.66..', '.646.', '..66.',
                                  '....6']),
                          (8, 9, ['11..', '13..', '..39', '..99']),
                          (13, 1, ['555', '525', '555'])],
               stamps=[(2, 3, 11, [(1, 1)]),
                       (2, 9, 20, [(1, 1)]),
                       (0, 16, 8, [(2, 2)]),
                       (1, 17, 17, [(1, 1), (2, 2)])]),
      generate(height=23, width=23, background=7,
               templates=[(1, 12, ['...8', '.88.', '.18.', '8...']),
                          (3, 2, ['44..', '423.', '.328', '..88'])],
               stamps=[(0, 9, 5, [(2, 1)]),
                       (0, 18, 17, [(2, 1)]),
                       (1, 9, 13, [(1, 1), (2, 2)]),
                       (1, 16, 2, [(1, 1), (2, 2)])]),
  ]
  return {'train': train, 'test': test}
