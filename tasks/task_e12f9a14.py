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

"""ARC-GEN style generator for task e12f9a14 (curated teaching copy).

Rule: every 2x2 coloured seed sits inside a 12-cell frame ring.  Each ring
cell that shows the background (a gap) fires a ray of the seed colour away
from the seed.  Side gaps fire orthogonally and corner gaps fire diagonally.

Rays merge as follows:
  * Rays of different seeds that come within Chebyshev distance 1 merge.
  * The earliest meeting is resolved first.  It is ranked by (max distance,
    summed distance, first distance, second distance, ray indices).
  * Both ray groups advance to that meeting.
  * Their direction vectors are added and reduced by their gcd.
  * The groups then continue together.  Non-unit slopes such as (2,1) step
    with a phase counter, and a zero sum stops the rays.

When no meeting remains, every live ray is extended to the border.  Only
background cells are ever painted.

Random scenes are a synthetic extension of the four demonstrations:
  * Grid sides are 8..30 by default (6..30 when given explicitly) and need
    not be square.
  * The background and frame colours are sampled.
  * There are one to five seeds by default; num_seeds may request up to 8.
    Seed colours are distinct.
  * Frames are separated by at least one empty cell.  They may be clipped by
    the grid border, as in the third demonstration.
  * Each seed has one to four gaps, never two orthogonally adjacent ones.
  * Later seeds are biased to fire towards earlier seeds.  About 75% of
    multi-seed scenes are required (best effort) to contain a merge that
    changes direction.

Seeds are added one at a time, and the whole scene is re-simulated after each
addition.  A candidate is kept only if the simulation stays inside
demonstrated behaviour:
  * no ray passes through a frame or seed;
  * no ray paints over another ray;
  * no ray touches a segment of another seed's ray except at a merge point.
    This includes segments painted before an earlier merge, so there are no
    silent crossings of old ray history;
  * no tie between meetings with equal (max, sum) but different outcomes;
  * no zero-sum (head-on) merge;
  * every merged slope has a major component of at most 2;
  * a non-unit slope is never merged into another non-unit slope;
  * no bundle strand hits the border while advancing to a meeting.

The output is computed from the latent seed list by simulating the rays.  The
generator never parses a grid.  Explicit seed lists are reproduced exactly and
bypass the cleanliness filter.

validate() rebuilds the curated teaching fixtures from explicit latent seeds.
Their train[2] output carries the documented six-cell correction (one extra
4-coloured diagonal ray).  No other correction is made.
"""

import random
from math import gcd

import common

RING = tuple(
    (dr, dc) for dr in range(-1, 3) for dc in range(-1, 3)
    if dr in (-1, 2) or dc in (-1, 2)
)

CORNERS = ((-1, -1), (-1, 2), (2, -1), (2, 2))

GAP_COUNTS = (1, 2, 3, 4)
GAP_WEIGHTS = (2, 3, 4, 2)

SIMULATION_BUDGET = 300

FLAGS = ("zero_sum", "steep", "rephase", "tie", "blocked", "overlap",
         "clipped", "contact")


def _sign(value):
  return (value > 0) - (value < 0)


def _direction(offset):
  """Outward unit direction of the ray fired by a ring offset."""
  dr, dc = offset
  vr = -1 if dr == -1 else (1 if dr == 2 else 0)
  vc = -1 if dc == -1 else (1 if dc == 2 else 0)
  return vr, vc


def _non_unit(dr, dc):
  major, minor = max(abs(dr), abs(dc)), min(abs(dr), abs(dc))
  return 0 < minor < major


def _trace(row, col, phase, dr, dc, height, width):
  """Cells (with phase) visited by a ray from its current cell to the border."""
  points = [(row, col, phase)]
  vert, horiz = abs(dr), abs(dc)
  step_r, step_c = _sign(dr), _sign(dc)
  while True:
    if vert >= horiz:
      row += step_r
      phase += horiz
      if horiz and phase >= vert:
        col += step_c
        phase -= vert
    else:
      col += step_c
      phase += vert
      if vert and phase >= horiz:
        row += step_r
        phase -= horiz
    if not (0 <= row < height and 0 <= col < width):
      return points
    points.append((row, col, phase))


def _first_meeting(active, traces, rays):
  """Smallest meeting key, plus whether an equally early meeting differs."""
  lookups, boxes = {}, {}
  for i in active:
    lookup = {}
    for d, (r, c, _) in enumerate(traces[i]):
      lookup.setdefault((r, c), []).append(d)
    lookups[i] = lookup
    rows = [p[0] for p in traces[i]]
    cols = [p[1] for p in traces[i]]
    boxes[i] = (min(rows), max(rows), min(cols), max(cols))
  best, tied = None, []
  for pos, i in enumerate(active):
    for j in active[:pos]:
      a, b = rays[i], rays[j]
      if a["group"] == b["group"] or a["seed"] == b["seed"]:
        continue
      bi, bj = boxes[i], boxes[j]
      if (bi[0] > bj[1] + 1 or bj[0] > bi[1] + 1 or
          bi[2] > bj[3] + 1 or bj[2] > bi[3] + 1):
        continue
      lookup = lookups[j]
      for d1, (r, c, _) in enumerate(traces[i]):
        if best is not None and d1 > best[0]:
          break
        for rr in (r - 1, r, r + 1):
          for cc in (c - 1, c, c + 1):
            for d2 in lookup.get((rr, cc), ()):
              key = (max(d1, d2), d1 + d2, d1, d2, i, j)
              if best is None or key[:2] < best[:2]:
                best, tied = key, [key]
              elif key[:2] == best[:2]:
                tied.append(key)
                if key < best:
                  best = key
  if best is None:
    return None, False

  def signature(key):
    _, _, d1, d2, i, j = key
    return frozenset(((rays[i]["group"], d1), (rays[j]["group"], d2)))

  reference = signature(best)
  ambiguous = any(signature(key) != reference for key in tied)
  return best, ambiguous


def _contact_ok(cell, index, rays, meta, joins, epoch, current):
  """True if a newly painted cell touches no foreign ray history.

  Allowed neighbours are: own-seed cells; cells painted in this same
  iteration (the meeting minimality guarantees those touch only at the merge
  point); current ray heads (covered by meeting detection); and, for rays
  already merged into the same group, cells painted after the merge or within
  one cell of the partner's merge endpoint.
  """
  r, c = cell
  for rr in (r - 1, r, r + 1):
    for cc in (c - 1, c, c + 1):
      entry = meta.get((rr, cc))
      if entry is None:
        continue
      other, painted = entry
      if other == index or rays[other]["seed"] == rays[index]["seed"]:
        continue
      if painted == epoch or (rr, cc) in current:
        continue
      if rays[other]["group"] != rays[index]["group"]:
        return False
      joined = joins.get((index, other))
      if joined is None:
        return False
      join_epoch, end = joined
      if painted <= join_epoch and max(abs(rr - end[0]), abs(cc - end[1])) > 1:
        return False
  return True


def _paint(output, grid, background, index, rays, path, state, info):
  """Paints background cells of a path; flags obstacles, overpaint, contact."""
  owner, meta, joins, epoch, current = state
  color = rays[index]["color"]
  for r, c, _ in path:
    if grid[r][c] != background:
      info["blocked"] = True
    elif output[r][c] != background:
      info["overlap"] = True
    else:
      if not _contact_ok((r, c), index, rays, meta, joins, epoch, current):
        info["contact"] = True
      output[r][c] = color
      owner[(r, c)] = index
      meta[(r, c)] = (index, epoch)


def _simulate(grid, background, seeds, height, width):
  """Fires, merges and extends rays from the latent (sorted) seed list.

  Returns the output grid and a dict of statistics and ambiguity flags.
  """
  output = [row[:] for row in grid]
  owner, meta, joins = {}, {}, {}
  info = {"merges": 0, "bends": 0}
  for flag in FLAGS:
    info[flag] = False
  rays = []
  for index, (color, top, left, gaps) in enumerate(seeds):
    for offset in RING:
      if offset not in gaps:
        continue
      row, col = top + offset[0], left + offset[1]
      vr, vc = _direction(offset)
      owner[(row, col)] = len(rays)
      meta[(row, col)] = (len(rays), -1)
      rays.append({"seed": index, "color": color, "row": row, "col": col,
                   "dr": vr, "dc": vc, "group": len(rays), "phase": 0,
                   "done": False})
      output[row][col] = color
  for epoch in range(len(rays)):
    active = [i for i, ray in enumerate(rays) if not ray["done"]]
    current = {(rays[i]["row"], rays[i]["col"]) for i in active}
    state = (owner, meta, joins, epoch, current)
    traces = {}
    for i in active:
      ray = rays[i]
      traces[i] = _trace(ray["row"], ray["col"], ray["phase"], ray["dr"],
                         ray["dc"], height, width)
    meeting, ambiguous = _first_meeting(active, traces, rays)
    if meeting is None:
      for i in active:
        _paint(output, grid, background, i, rays, traces[i][1:], state, info)
        rays[i]["done"] = True
      break
    info["merges"] += 1
    if ambiguous:
      info["tie"] = True
    _, _, dist1, dist2, first, second = meeting
    group1, group2 = rays[first]["group"], rays[second]["group"]
    members1 = [k for k in active if rays[k]["group"] == group1]
    members2 = [k for k in active if rays[k]["group"] == group2]
    for members, distance in ((members1, dist1), (members2, dist2)):
      for i in members:
        path = traces[i]
        if distance > len(path) - 1:
          info["clipped"] = True
        end = min(distance, len(path) - 1)
        _paint(output, grid, background, i, rays, path[1:end + 1], state,
               info)
        rays[i]["row"], rays[i]["col"], rays[i]["phase"] = path[end]
    for a in members1:
      for b in members2:
        joins[(a, b)] = (epoch, (rays[b]["row"], rays[b]["col"]))
        joins[(b, a)] = (epoch, (rays[a]["row"], rays[a]["col"]))
    old1 = (rays[first]["dr"], rays[first]["dc"])
    old2 = (rays[second]["dr"], rays[second]["dc"])
    dr, dc = old1[0] + old2[0], old1[1] + old2[1]
    divisor = gcd(abs(dr), abs(dc))
    if divisor:
      dr, dc = dr // divisor, dc // divisor
    if dr == 0 and dc == 0:
      info["zero_sum"] = True
    elif (dr, dc) not in (old1, old2):
      info["bends"] += 1
    if max(abs(dr), abs(dc)) > 2:
      info["steep"] = True
    if _non_unit(dr, dc) and (_non_unit(*old1) or _non_unit(*old2)):
      info["rephase"] = True
    merged = min(group1, group2)
    for i in members1 + members2:
      ray = rays[i]
      was_axis = (ray["dr"] == 0) != (ray["dc"] == 0)
      ray["group"], ray["dr"], ray["dc"] = merged, dr, dc
      major, minor = max(abs(dr), abs(dc)), min(abs(dr), abs(dc))
      ray["phase"] = -minor if was_axis and 0 < minor < major else 0
      if dr == 0 and dc == 0:
        ray["done"] = True
  for (r, c), k in owner.items():
    for rr in (r - 1, r, r + 1):
      for cc in (c - 1, c, c + 1):
        other = owner.get((rr, cc))
        if (other is not None and rays[other]["seed"] != rays[k]["seed"]
            and rays[other]["group"] != rays[k]["group"]):
          info["contact"] = True
  return output, info


def _is_clean(info):
  return not any(info[flag] for flag in FLAGS)


def _boxes_clear(top, left, placed):
  """Frames (4x4 boxes) must keep at least one empty cell between them."""
  for _, other_top, other_left, _ in placed:
    if abs(top - other_top) <= 4 and abs(left - other_left) <= 4:
      return False
  return True


def _check_color(name, value):
  if not isinstance(value, int) or not 0 <= value <= 9:
    raise ValueError("%s must be a colour 0..9" % name)


def _build_grid(width, height, background, frame_color, seeds):
  grid = common.grid(width, height, background)
  for color, top, left, gaps in seeds:
    for dr, dc in RING:
      r, c = top + dr, left + dc
      if 0 <= r < height and 0 <= c < width and (dr, dc) not in gaps:
        grid[r][c] = frame_color
    for dr in (0, 1):
      for dc in (0, 1):
        grid[top + dr][left + dc] = color
  return grid


def _background_dominant(grid, background):
  counts = {}
  for row in grid:
    for cell in row:
      counts[cell] = counts.get(cell, 0) + 1
  bg_count = counts.get(background, 0)
  return all(n < bg_count for c, n in counts.items() if c != background)


def _normalise_seeds(width, height, background, frame_color, seeds):
  """Validates explicit seeds and returns them sorted in reading order."""
  colors = [entry[0] for entry in seeds]
  if len(set(colors)) != len(colors):
    raise ValueError("seed colours must be distinct")
  result = []
  for entry in seeds:
    color, top, left, gaps = entry
    _check_color("seed colour", color)
    if color in (background, frame_color):
      raise ValueError("seed colour collides with background/frame colour")
    if not (0 <= top <= height - 2 and 0 <= left <= width - 2):
      raise ValueError("2x2 seed must lie fully inside the grid")
    gap_set = set()
    for gap in gaps:
      gap = tuple(gap)
      if gap not in RING:
        raise ValueError("gap %r is not a ring offset" % (gap,))
      if not (0 <= top + gap[0] < height and 0 <= left + gap[1] < width):
        raise ValueError("gap %r lies outside the grid" % (gap,))
      gap_set.add(gap)
    if not _boxes_clear(top, left, result):
      raise ValueError("frames must be separated by an empty cell")
    result.append((color, top, left, tuple(sorted(gap_set))))
  if not any(entry[3] for entry in result):
    raise ValueError("at least one gap is required (otherwise output == input)")
  result.sort(key=lambda s: (s[1], s[2]))
  return result


def _sample_position(w, h, placed):
  for _ in range(50):
    if random.random() < 0.85:
      top = random.randint(1, h - 3)
      left = random.randint(1, w - 3)
    else:
      top = random.randint(0, h - 2)
      left = random.randint(0, w - 2)
    if _boxes_clear(top, left, placed):
      return top, left
  return None


def _sample_gaps(w, h, top, left, placed):
  """Chooses 1..4 non-adjacent gaps, often aimed at earlier seeds."""
  ring = [o for o in RING if 0 <= top + o[0] < h and 0 <= left + o[1] < w]
  pool = ring
  roll = random.random()
  if placed and roll < 0.45:
    toward = []
    for offset in ring:
      vr, vc = _direction(offset)
      for _, other_top, other_left, _ in placed:
        if vr * (other_top - top) + vc * (other_left - left) > 0:
          toward.append(offset)
          break
    pool = toward or ring
  elif roll >= 0.7:
    pool = [o for o in ring if o in CORNERS] or ring
  wanted = random.choices(GAP_COUNTS, weights=GAP_WEIGHTS)[0]
  order = pool[:]
  random.shuffle(order)
  gaps = []
  for offset in order:
    if len(gaps) >= wanted:
      break
    if any(abs(offset[0] - g[0]) + abs(offset[1] - g[1]) == 1 for g in gaps):
      continue
    gaps.append(offset)
  return tuple(sorted(gaps))


def _random_scene(width, height, background, frame_color, num_seeds, budget):
  """Builds one scene seed by seed; returns None if it cannot be completed."""
  w = width if width is not None else random.randint(8, 30)
  h = height if height is not None else random.randint(8, 30)
  bg = background if background is not None else random.randint(0, 9)
  if frame_color is not None:
    fc = frame_color
  else:
    fc = random.choice([c for c in range(10) if c != bg])
  palette = [c for c in range(10) if c not in (bg, fc)]
  if num_seeds is not None:
    count = num_seeds
  elif budget[0] < 60:
    count = 1
  else:
    count = random.randint(1, max(1, min(5, (w * h) // 80)))
  placed = []
  result = None
  for color in random.sample(palette, count):
    for _ in range(25):
      if budget[0] <= 0:
        return None
      position = _sample_position(w, h, placed)
      if position is None:
        continue
      top, left = position
      gaps = _sample_gaps(w, h, top, left, placed)
      candidate = sorted(placed + [(color, top, left, gaps)],
                         key=lambda s: (s[1], s[2]))
      grid = _build_grid(w, h, bg, fc, candidate)
      if not _background_dominant(grid, bg):
        continue
      budget[0] -= 1
      output, info = _simulate(grid, bg, candidate, h, w)
      if _is_clean(info):
        placed = candidate
        result = (grid, output, info)
        break
    else:
      return None
  return result + (count,)


def generate(width=None, height=None, background=None, frame_color=None,
             num_seeds=None, seeds=None):
  """Returns an input/output pair.

  Args:
    width: grid width (columns).  Random in 8..30 if None.  Explicit values
      must be 6..30 for random scenes and 2..30 with explicit seeds.
    height: grid height (rows).  Same ranges as width.
    background: background colour.  Random if None.
    frame_color: colour of the 12-cell frame rings.  It must differ from
      background.  Random if None.
    num_seeds: number of seeds in a random scene.  Random in
      1..min(5, area // 80) if None.  At most 8, because seed colours are
      distinct and avoid the background and frame colours.  A request that
      cannot be placed cleanly within the bounded budget raises ValueError.
      With explicit seeds it must equal len(seeds).
    seeds: explicit list of (color, top, left, gaps).  (top, left) is the
      top-left cell of the 2x2 seed.  gaps lists ring offsets (dr, dc)
      relative to (top, left), with dr and dc in -1..2, that show background
      instead of frame.  Ring cells outside the grid are clipped and may not
      be gaps.  When seeds is given, width, height, background and
      frame_color are all required.  Explicit scenes skip the random-scene
      cleanliness filter.
  """
  for name, value in (("background", background),
                      ("frame_color", frame_color)):
    if value is not None:
      _check_color(name, value)
  if (background is not None and frame_color is not None
      and background == frame_color):
    raise ValueError("frame_color must differ from background")
  if seeds is not None:
    if None in (width, height, background, frame_color):
      raise ValueError("explicit seeds need width, height, background and "
                       "frame_color")
    if not (2 <= width <= 30 and 2 <= height <= 30):
      raise ValueError("grid sides must be 2..30")
    if num_seeds is not None and num_seeds != len(seeds):
      raise ValueError("num_seeds disagrees with the explicit seed list")
    seeds = _normalise_seeds(width, height, background, frame_color, seeds)
    grid = _build_grid(width, height, background, frame_color, seeds)
    if not _background_dominant(grid, background):
      raise ValueError("background must be the most common colour")
    output, _ = _simulate(grid, background, seeds, height, width)
    return {"input": grid, "output": output}
  for name, value in (("width", width), ("height", height)):
    if value is not None and not 6 <= value <= 30:
      raise ValueError("%s must be 6..30 for random scenes" % name)
  if num_seeds is not None and not 1 <= num_seeds <= 8:
    raise ValueError("num_seeds must be 1..8")
  want_bend = random.random() < 0.75
  budget = [SIMULATION_BUDGET]
  fallback = None
  for _ in range(40):
    if budget[0] <= 0:
      break
    scene = _random_scene(width, height, background, frame_color, num_seeds,
                          budget)
    if scene is None:
      continue
    grid, output, info, count = scene
    pair = {"input": grid, "output": output}
    if count < 2 or not want_bend or info["bends"] > 0:
      return pair
    if fallback is None:
      fallback = pair
  if fallback is not None:
    return fallback
  if num_seeds is None:
    # Seed count was not requested, so a single-seed scene (always clean:
    # one seed cannot block, overlap or merge) is a valid bounded fallback.
    for _ in range(10):
      scene = _random_scene(width, height, background, frame_color, 1,
                            [SIMULATION_BUDGET])
      if scene is not None:
        grid, output, _, _ = scene
        return {"input": grid, "output": output}
  raise ValueError("could not build an unambiguous scene; reduce num_seeds "
                   "or enlarge the grid")


def validate():
  """Rebuilds the curated teaching fixtures from explicit latent scenes."""
  corners = [(-1, -1), (-1, 2), (2, -1), (2, 2)]
  train = [
      generate(width=24, height=24, background=8, frame_color=3, seeds=[
          (9, 10, 4, corners), (1, 10, 12, corners),
          (4, 10, 18, [(-1, 0), (2, 0)]), (6, 20, 2, [(0, 2)])]),
      generate(width=8, height=8, background=8, frame_color=3, seeds=[
          (4, 3, 2, [(-1, 1), (1, 2), (2, -1)])]),
      generate(width=20, height=20, background=8, frame_color=3, seeds=[
          (2, 6, 4, [(0, 2), (1, -1)]),
          (4, 11, 12, [(-1, 1), (0, -1), (2, 2)]),
          (7, 18, 6, [(0, -1)])]),
      generate(width=12, height=12, background=8, frame_color=3, seeds=[
          (6, 3, 2, [(-1, 0), (-1, 2), (2, -1)])]),
  ]
  test = [
      generate(width=30, height=30, background=0, frame_color=8, seeds=[
          (2, 7, 23, [(-1, -1), (-1, 2), (2, 2)]),
          (3, 11, 5, [(-1, -1), (-1, 2), (2, 0), (2, 2)]),
          (4, 11, 11, [(-1, -1), (-1, 2), (2, -1), (2, 1)]),
          (7, 25, 24, [(-1, 2), (1, 2), (2, 0)])]),
      generate(width=30, height=30, background=8, frame_color=3, seeds=[
          (2, 5, 4, [(-1, 0), (0, -1), (2, 2)]),
          (4, 5, 15, [(-1, -1), (0, 2), (2, 0)]),
          (6, 14, 23, [(-1, 0), (-1, 2), (2, 2)]),
          (7, 20, 22, [(0, 2), (2, 2)]),
          (9, 25, 1, [(-1, 1), (2, 2)])]),
  ]
  return {"train": train, "test": test}
