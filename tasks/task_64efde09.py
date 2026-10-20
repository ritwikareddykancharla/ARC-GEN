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

"""ARC-GEN style generator for task 64efde09.

Rule: the grid (background 8) contains several identical "devices" and a few
single-cell markers. A device is a bar two cells thick, made of two parallel
lines of length L. The far line reads a,a,b,...,b,e, so it has one doubled
end. The near line reads p,q,...,q,r and has no doubled end. Positions along
a device are indexed from its doubled end. Each marker lies on the grid
border, on the near side of exactly one device, and is aligned with index i
of that device. That gives a mapping index -> marker colour. In the output,
every device shoots a ray for every mapped index. The ray has the mapped
colour, leaves the near line at that index, runs perpendicular to the bar
away from the far line, and continues to the grid border.

Scope: random grid sizes (14..30 per side, a synthetic extension of the
21..29 fixture sizes), device length (5..10, fixtures use 7 and 9), device
template colours, device count, all four outward directions, both chiralities
(doubled end at either end), positions, marker count, marker indices, marker
hosts and marker colours. Several markers may share a host device. Rays never
cross other rays, devices or foreign markers. Markers are never 8-adjacent to
devices or to each other. Every marker lies in the near-side beam region of
exactly one device. Explicit arguments reconstruct the fixtures.
Not supported: crossing or blocked rays, markers away from the border,
marker colours that reuse device colours, and backgrounds other than 8.
"""

import random

import common

BG = 8
DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
POOL = [c for c in range(10) if c != BG]


def _geometry(device, length):
  """Returns (box, near_cells, far_cells), indexed from the doubled end."""
  r, c, d, flip = device
  if d in ("up", "down"):
    box = (r, c, r + 1, c + length - 1)
    near_row, far_row = (r + 1, r) if d == "down" else (r, r + 1)
    cols = [c + i for i in range(length)]
    if flip:
      cols = cols[::-1]
    near = [(near_row, x) for x in cols]
    far = [(far_row, x) for x in cols]
  else:
    box = (r, c, r + length - 1, c + 1)
    near_col, far_col = (c + 1, c) if d == "right" else (c, c + 1)
    rows = [r + i for i in range(length)]
    if flip:
      rows = rows[::-1]
    near = [(y, near_col) for y in rows]
    far = [(y, far_col) for y in rows]
  return box, near, far


def _ray(start, d, width, height):
  cells = []
  y, x = start[0] + d[0], start[1] + d[1]
  while 0 <= y < height and 0 <= x < width:
    cells.append((y, x))
    y, x = y + d[0], x + d[1]
  return cells


def _box_close(a, b):
  return (a[0] - 1 <= b[2] and b[0] <= a[2] + 1 and
          a[1] - 1 <= b[3] and b[1] <= a[3] + 1)


def _doubled_start(line):
  return line[0] == line[1] and line[1] != line[2]


def _doubled_end(line):
  return line[-1] == line[-2] and line[-2] != line[-3]


def _check_templates(far, near):
  if far is None or near is None:
    raise ValueError("far and near templates are required")
  if len(far) != len(near) or len(far) < 4:
    raise ValueError("far and near must share a length of at least 4")
  for c in list(far) + list(near):
    if type(c) is not int or c == BG or not 0 <= c <= 9:
      raise ValueError("template colours must be non-background colours")
  if not _doubled_start(far) or _doubled_end(far):
    raise ValueError("far template must have exactly one doubled end, first")
  if _doubled_start(near) or _doubled_end(near):
    raise ValueError("near template must not have a doubled end")


def _render(width, height, far, near, devices, markers):
  """Draws the latent scene and its answer, rejecting colliding rays."""
  _check_templates(far, near)
  if not (type(width) is int and type(height) is int and
          1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid sides must be within 1..30")
  length = len(far)
  grid = common.grid(width, height, BG)
  geoms = []
  boxes = []
  if not devices or not markers:
    raise ValueError("at least one device and marker are required")
  for dev in devices:
    if (len(dev)!=4 or dev[2] not in DIRS or type(dev[0]) is not int
        or type(dev[1]) is not int or type(dev[3]) is not bool):
      raise ValueError("unknown direction")
    box, nc, fc = _geometry(dev, length)
    if any(_box_close(box,b) for b in boxes):
      raise ValueError("devices must be separated")
    boxes.append(box)
    for i in range(length):
      for (y, x), colour in ((nc[i], near[i]), (fc[i], far[i])):
        if not (0 <= y < height and 0 <= x < width) or grid[y][x] != BG:
          raise ValueError("devices must lie inside the grid without overlap")
        grid[y][x] = colour
    geoms.append((nc, DIRS[dev[2]]))
  mapping = {}
  marker_cells = {}
  for di, idx, colour in markers:
    if (type(di) is not int or type(idx) is not int or
        not 0 <= di < len(geoms) or not 0 <= idx < length):
      raise ValueError("marker refers to a missing device or index")
    if (idx in mapping or type(colour) is not int or colour == BG or
        not 0 <= colour <= 9 or colour in set(far)|set(near)):
      raise ValueError("marker indices must be distinct, colours non-bg")
    nc, d = geoms[di]
    ray = _ray(nc[idx], d, width, height)
    if not ray:
      raise ValueError("marker host has no room on its near side")
    y, x = ray[-1]
    if _owner_count((y,x),geoms)!=1:
      raise ValueError("marker must identify exactly one near-side device")
    if any(0<=y+dy<height and 0<=x+dx<width and grid[y+dy][x+dx]!=BG
           for dy in (-1,0,1) for dx in (-1,0,1)):
      raise ValueError("markers must be isolated from devices and markers")
    if grid[y][x] != BG:
      raise ValueError("marker cell is occupied")
    grid[y][x] = colour
    mapping[idx] = colour
    marker_cells[(y, x)] = colour
  flat = [v for row in grid for v in row]
  if any(flat.count(c)>=flat.count(BG) for c in set(flat)-{BG}):
    raise ValueError("background must be the unique most common colour")
  output = [row[:] for row in grid]
  painted = {}
  for nc, d in geoms:
    for idx, colour in mapping.items():
      for (y, x) in _ray(nc[idx], d, width, height):
        if grid[y][x] != BG and marker_cells.get((y, x)) != colour:
          raise ValueError("ray blocked by a foreign cell")
        if painted.setdefault((y, x), colour) != colour:
          raise ValueError("rays of different colours cross")
        output[y][x] = colour
  return {"input": grid, "output": output}


def _place_devices(width, height, length, n_dev, indices):
  devices, boxes = [], []
  occupied, ray_cells_all = set(), set()
  for _ in range(n_dev):
    placed = False
    for _ in range(300):
      d = random.choice(list(DIRS))
      flip = random.random() < 0.5
      if d in ("up", "down"):
        if height < 2 or width < length:
          return None, None
        r = random.randint(0, height - 2)
        c = random.randint(0, width - length)
      else:
        if width < 2 or height < length:
          return None, None
        r = random.randint(0, height - length)
        c = random.randint(0, width - 2)
      dev = (r, c, d, flip)
      box, nc, fc = _geometry(dev, length)
      rays = [_ray(nc[i], DIRS[d], width, height) for i in indices]
      if not rays[0]:
        continue
      if any(_box_close(box, b) for b in boxes):
        continue
      cells = set(nc) | set(fc)
      if cells & ray_cells_all:
        continue
      new_rays = set()
      for ray in rays:
        new_rays.update(ray)
      if new_rays & occupied or new_rays & ray_cells_all:
        continue
      devices.append(dev)
      boxes.append(box)
      occupied |= cells
      ray_cells_all |= new_rays
      placed = True
      break
    if not placed:
      return None, None
  return devices, occupied


def _owner_count(cell, geoms):
  """Counts devices whose near-side beam region contains the cell."""
  count = 0
  for nc, d in geoms:
    for (py, px) in nc:
      if d[0] != 0 and px == cell[1] and (cell[0] - py) * d[0] > 0:
        count += 1
        break
      if d[1] != 0 and py == cell[0] and (cell[1] - px) * d[1] > 0:
        count += 1
        break
  return count


def _place_markers(width, height, length, devices, occupied, indices, colours):
  geoms = []
  for dev in devices:
    _, nc, _ = _geometry(dev, length)
    geoms.append((nc, DIRS[dev[2]]))
  hosts = [j for j, (nc, d) in enumerate(geoms)
           if len(_ray(nc[0], d, width, height)) >= 2]
  if not hosts:
    return None
  for _ in range(40):
    markers, cells = [], []
    for idx, colour in zip(indices, colours):
      j = random.choice(hosts)
      nc, d = geoms[j]
      markers.append((j, idx, colour))
      cells.append(_ray(nc[idx], d, width, height)[-1])
    good = True
    for cell in cells:
      if _owner_count(cell, geoms) != 1:
        good = False
        break
      y, x = cell
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          if dy == 0 and dx == 0:
            continue
          n = (y + dy, x + dx)
          if n in occupied or (n in cells and n != cell):
            good = False
      if not good:
        break
    if good:
      return markers
  return None


def _sample_templates(length, far, near):
  """Fills in whichever of far/near is missing, reusing supplied colours."""
  base = []
  for c in list(far or []) + list(near or []):
    if c not in base:
      base.append(c)
  extra = [c for c in POOL if c not in base]
  want = max(random.randint(2, 4) - len(base), 2 - len(base), 0)
  palette = base + random.sample(extra, min(want, len(extra)))
  if far is None:
    a, b = random.sample(palette, 2)
    # At length four a repeated b would create a second doubled end.
    end = a if length==4 else random.choice(palette)
    far = [a, a] + [b] * (length - 3) + [end]
  if near is None:
    p, q, r = (random.choice(palette) for _ in range(3))
    near = [p] + [q] * (length - 2) + [r]
  return list(far), list(near)


def generate(width=None, height=None, far=None, near=None, devices=None,
             markers=None, num_devices=None, num_markers=None):
  """Generates one input/output pair.

  Args:
    width: grid width (random 14..30 when omitted).
    height: grid height (random 14..30 when omitted).
    far: far-line colour template (list of length L), indexed from the
      doubled end, of the form a,a,b,...,b,e. Sampled when omitted.
    near: near-line colour template (list of length L), indexed from the
      doubled end, with no doubled end. Sampled when omitted.
    devices: explicit list of (row, col, direction, flip). (row, col) is the
      bounding-box top-left. direction is the outward ray direction. flip
      puts index 0 at the high-coordinate end. Requires width, height, far,
      near and markers.
    markers: explicit list of (device_index, index, colour). Each marker is
      placed on the grid border at the end of that device's ray for that
      index. Only valid together with devices.
    num_devices: number of devices for random scenes (1..6).
    num_markers: number of markers, which equals the number of distinct ray
      indices, for random scenes.
  """
  if devices is not None or markers is not None:
    if (devices is None or markers is None or width is None or
        height is None or far is None or near is None):
      raise ValueError("explicit scenes need width, height, far, near, "
                       "devices and markers")
    if num_devices is not None and num_devices != len(devices):
      raise ValueError("num_devices disagrees with devices")
    if num_markers is not None and num_markers != len(markers):
      raise ValueError("num_markers disagrees with markers")
    return _render(width, height, list(far), list(near), devices, markers)

  if far is not None and near is not None and len(far) != len(near):
    raise ValueError("far and near must have equal length")
  if far is not None:
    length = len(far)
  elif near is not None:
    length = len(near)
  else:
    length = random.randint(5, 10)
  if not 4 <= length <= 28:
    raise ValueError("device length must be within 4..28")
  for side in (width, height):
    if side is not None and (type(side) is not int or not 3 <= side <= 30):
      raise ValueError("grid sides must be within 3..30")
  far_t, near_t = _sample_templates(length, far, near)
  _check_templates(far_t, near_t)
  dev_cols = set(far_t) | set(near_t)
  rest = [c for c in POOL if c not in dev_cols]
  max_k = min(length - 2, len(rest))
  if max_k < 1:
    raise ValueError("no colours left for markers")
  if num_markers is not None and (type(num_markers) is not int or
                                 not 1 <= num_markers <= max_k):
    raise ValueError("num_markers must be within 1..%d" % max_k)
  if num_devices is not None and (type(num_devices) is not int or
                                 not 1 <= num_devices <= 6):
    raise ValueError("num_devices must be within 1..6")
  lo = min(30, max(14, length + 5))
  for attempt in range(400):
    w = width if width is not None else random.randint(lo, 30)
    h = height if height is not None else random.randint(lo, 30)
    if num_markers is not None:
      k = num_markers
    else:
      k = random.randint(min(2, max_k), min(4, max_k))
    if num_devices is not None:
      n_dev = num_devices
    elif attempt < 250:
      n_dev = random.choice([2, 3, 3, 4, 4])
    else:
      n_dev = 2
    indices = random.sample(range(1, length - 1), k)
    mcols = random.sample(rest, k)
    devs, occupied = _place_devices(w, h, length, n_dev, indices)
    if devs is None:
      continue
    marks = _place_markers(w, h, length, devs, occupied, indices, mcols)
    if marks is None:
      continue
    return _render(w, h, far_t, near_t, devs, marks)
  raise RuntimeError("failed to construct a valid scene for these settings")


def validate():
  """Reconstructs the canonical pairs through explicit generate calls."""
  train = [
      generate(width=29, height=26, far=[4, 4, 3, 3, 3, 3, 4],
               near=[4, 2, 2, 2, 2, 2, 2],
               devices=[(0, 18, "left", False), (7, 1, "down", True),
                        (15, 12, "down", True), (18, 22, "right", False)],
               markers=[(1, 4, 5), (2, 5, 1), (3, 1, 6)]),
      generate(width=27, height=21, far=[4, 4, 2, 2, 2, 2, 2, 2, 4],
               near=[1] * 9,
               devices=[(0, 5, "left", False), (2, 14, "up", True),
                        (9, 16, "right", False)],
               markers=[(0, 1, 3), (0, 5, 9), (1, 3, 6)]),
  ]
  test = [
      generate(width=29, height=29, far=[1, 1, 2, 2, 2, 2, 3],
               near=[1, 4, 4, 4, 4, 4, 3],
               devices=[(0, 4, "left", False), (2, 18, "down", True),
                        (10, 24, "right", True), (22, 9, "left", False)],
               markers=[(0, 1, 9), (1, 3, 6), (2, 5, 7)]),
  ]
  return {"train": train, "test": test}
