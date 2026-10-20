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

"""ARC-GEN style generator for task 2b83f449 (ladder / amidakuji puzzle).

Rule: even rows are horizontal tracks of colour 8, possibly split into
segments by 0 gaps. Odd rows are background rows holding horizontal orange
bars 7 7 7. Each bar is a rung joining the track above to the track below at
the bar's middle column. In the output every bar becomes 8 6 8, and magenta 6
is also painted in the middle column on both neighbouring tracks, giving a
vertical connector three cells tall. Green markers (3) start at the outer ends
of every track except the last one. Every segment endpoint is paired by a
ladder walk. The walk goes inward from the endpoint. At the nearest rung ahead
it crosses to the other track and reverses direction. When no rung remains
ahead inside the current segment, it stops at that segment's end. For a pair
whose ends lie on the same track, the markers stay where they are. Otherwise
all of the pair's markers (1 or 2) are stacked inward from the lower endpoint.
All other 3s become 8.

Scope: the number of tracks (4..15), the width (10..30), the gap positions
(0..2 per track) and the rung layout are randomized. Colours are fixed, as in
the task. Markers follow the task convention: the outer ends of all tracks
except the bottom one.
"""

import random

import common


def _segments(width, gaps):
  segs = []
  start = 0
  for g in sorted(gaps) + [width]:
    if g > start:
      segs.append((start, g - 1))
    start = g + 1
  return segs


def _seg_of(segs, c):
  for lo, hi in segs:
    if lo <= c <= hi:
      return lo, hi
  return c, c


def _walk(track, col, segs, rung_map):
  lo, hi = _seg_of(segs[track], col)
  d = 1 if col == lo else -1
  first = True
  seen = set()
  for _ in range(10000):
    state = (track, col, d, first)
    if state in seen:
      break
    seen.add(state)
    lo, hi = _seg_of(segs[track], col)
    cands = [(x, o) for x, o in rung_map[track]
             if lo <= x <= hi and ((x - col) * d > 0 or (first and x == col))]
    if not cands:
      col = hi if d > 0 else lo
      break
    x, o = min(cands, key=lambda it: abs(it[0] - col))
    col, track = x, o
    d = -d
    first = False
  return (track, col)


def _sample_gaps(width, tracks):
  gaps = []
  for _ in range(tracks):
    gs = []
    if random.random() < 0.3:
      n = 1 if width < 15 or random.random() < 0.7 else 2
      for _ in range(n):
        for _ in range(30):
          g = random.randint(3, width - 4)
          if all(abs(g - h) >= 4 for h in gs):
            gs.append(g)
            break
    gaps.append(sorted(gs))
  return gaps


def _sample_rungs(width, tracks, gaps):
  rungs = [[] for _ in range(tracks - 1)]
  for i in range(tracks - 1):
    k = random.choice([0, 1, 1, 2, 2, 2, 3, 3])
    forbid = gaps[i] + gaps[i + 1]
    for _ in range(k):
      for _ in range(40):
        m = random.randint(2, width - 3)
        if not all(abs(m - g) >= 3 for g in forbid):
          continue
        if not all(abs(m - x) >= 4 for x in rungs[i]):
          continue
        if i > 0 and not all(abs(m - x) >= 2 for x in rungs[i - 1]):
          continue
        rungs[i].append(m)
        break
    rungs[i].sort()
  return rungs


def generate(width=None, tracks=None, gaps=None, rungs=None, markers=None):
  """Build one ladder puzzle.

  Args:
    width: grid width (10..30).
    tracks: number of track rows; the height is 2 * tracks - 1 (4..15).
    gaps: per-track list of gap columns (0 cells inside the track row).
    rungs: per-gap-row list of rung middle columns. Entry i joins track i to
      track i + 1, and its bar occupies columns m-1..m+1 on row 2i+1.
    markers: optional list of (track, col) green marker positions. The default
      is the outer ends of every track except the last.
  """
  if width is None:
    width = random.randint(10, 30)
  if tracks is None:
    tracks = random.randint(4, 15)
  if not isinstance(width, int) or not 10 <= width <= 30:
    raise ValueError("width must be in 10..30")
  if not isinstance(tracks, int) or not 4 <= tracks <= 15:
    raise ValueError("tracks must be in 4..15")
  if gaps is not None:
    if len(gaps) != tracks or any(len(set(row)) != len(row) or any(not 0 < c < width - 1 for c in row) for row in gaps):
      raise ValueError("One valid gap list required per track")
  if rungs is not None and gaps is None:
    raise ValueError("Explicit rungs require explicit gaps")
  if rungs is None:
    for _ in range(200):
      g = gaps if gaps is not None else _sample_gaps(width, tracks)
      r = _sample_rungs(width, tracks, g)
      if sum(len(x) for x in r) >= max(2, tracks - 2):
        break
    else:
      raise ValueError("Could not place enough separated rungs")
    gaps, rungs = g, r
  if len(rungs) != tracks - 1:
    raise ValueError("One rung list required per gap row")
  for i, row in enumerate(rungs):
    if (any(not 1 <= m < width - 1 for m in row) or len(set(row)) != len(row) or
        any(abs(a - b) < 4 for j, a in enumerate(row) for b in row[j+1:]) or
        any(m in gaps[i] or m in gaps[i+1] for m in row) or
        (i > 0 and set(row) & set(rungs[i-1]))):
      raise ValueError("Rungs overlap, cross track gaps, or have ambiguous shared columns")
  if markers is None:
    markers = []
    for t in range(tracks - 1):
      markers.append((t, 0))
      markers.append((t, width - 1))
  markers = [tuple(m) for m in markers]
  endpoints = {(t, c) for t in range(tracks) for lo, hi in _segments(width, gaps[t]) for c in (lo, hi)}
  if len(set(markers)) != len(markers) or any(m not in endpoints for m in markers):
    raise ValueError("Markers must be distinct segment endpoints")
  markers = set(markers)

  height = 2 * tracks - 1
  grid = common.grid(width, height, 0)
  segs = [_segments(width, gaps[t]) for t in range(tracks)]
  for t in range(tracks):
    for lo, hi in segs[t]:
      for c in range(lo, hi + 1):
        grid[2 * t][c] = 8
  for t, c in markers:
    grid[2 * t][c] = 3
  for i, row in enumerate(rungs):
    for m in row:
      for c in range(m - 1, m + 2):
        grid[2 * i + 1][c] = 7

  out = [row[:] for row in grid]
  rung_map = [[] for _ in range(tracks)]
  for i, row in enumerate(rungs):
    r = 2 * i + 1
    for m in row:
      for c in range(m - 1, m + 2):
        out[r][c] = 8
      for rr in (r - 1, r, r + 1):
        out[rr][m] = 6
      rung_map[i].append((m, i + 1))
      rung_map[i + 1].append((m, i))
  for r in range(height):
    for c in range(width):
      if out[r][c] == 3:
        out[r][c] = 8

  endpoints = set()
  for t in range(tracks):
    for lo, hi in segs[t]:
      endpoints.add((t, lo))
      endpoints.add((t, hi))
  paths = set()
  for e in sorted(endpoints):
    dest = _walk(e[0], e[1], segs, rung_map)
    paths.add(tuple(sorted((e, dest))))
  for a, b in sorted(paths):
    count = int(a in markers) + int(b in markers)
    if not count:
      continue
    if a[0] == b[0]:
      for e in (a, b):
        if e in markers:
          out[2 * e[0]][e[1]] = 3
    else:
      t, c = b
      lo, hi = _seg_of(segs[t], c)
      d = 1 if c == lo else -1
      for k in range(count):
        x = c + d * k
        if 0 <= x < width:
          out[2 * t][x] = 3
  return {"input": grid, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=19, tracks=7,
               gaps=[[7], [], [], [], [15], [], [2, 8]],
               rungs=[[4, 10], [6, 13], [3, 8, 15], [5, 11], [8], [5, 13]]),
      generate(width=16, tracks=6,
               gaps=[[], [], [], [], [], []],
               rungs=[[4], [12], [6], [3, 11], [7]]),
  ]
  test = [
      generate(width=17, tracks=10,
               gaps=[[], [], [7], [], [], [10], [], [], [], [7]],
               rungs=[[10], [13], [], [7], [4], [], [10], [7], [3, 12]]),
  ]
  return {"train": train, "test": test}
