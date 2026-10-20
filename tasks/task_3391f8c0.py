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

"""ARC task 3391f8c0: swap a repeated shape with a single odd shape.

Rule: the input holds two foreground colours on a black background. One
colour forms several identical copies of a small shape (the repeated
shape). The other colour forms exactly one shape with the same bounding-box
size (the odd shape). In the output the two shapes trade places. Every
copy's box gets the odd shape in the odd colour. The odd shape's box gets
the repeated shape in the repeated colour.

Scope: both shapes fill an h x w box with 2 <= h, w <= 6. Each shape
touches all four edges of its box. A shape need not be connected. The
repeated shape has 2..10 copies. The grid is 7..30 cells per side and the
background is 0. Random scenes mix loose gaps and tightly packed non-overlapping boxes.
A template-uniqueness check keeps the repeated pattern identifiable. The fixtures, which have tighter spacing, are rebuilt from
explicit latent arguments.
"""

import random

import common


def _random_shape(h, w):
  """Random 0/1 mask of size h x w that touches all four edges."""
  for _ in range(200):
    m = [[1 if random.random() < 0.55 else 0 for _ in range(w)]
         for _ in range(h)]
    if not any(m[0]) or not any(m[-1]):
      continue
    if not any(r[0] for r in m) or not any(r[-1] for r in m):
      continue
    if sum(map(sum, m)) == h * w:
      continue
    return m
  raise RuntimeError("Could not sample a non-solid edge-spanning mask")


def _separated(a, b, h, w, gap):
  (r1, c1), (r2, c2) = a, b
  row_gap = max(r1, r2) - min(r1, r2) - h
  col_gap = max(c1, c2) - min(c1, c2) - w
  return row_gap >= gap or col_gap >= gap


def _identifiable(rep, odd, copies, odd_pos, height, width):
  """Check unique repeated-mask evidence without constructing the target."""
  h,w=len(rep),len(rep[0]);g=[[0]*width for _ in range(height)]
  for r,c in copies:
    for y in range(h):
      for x in range(w):
        if rep[y][x]:g[r+y][c+x]=1
  for y in range(h):
    for x in range(w):
      if odd[y][x]:g[odd_pos[0]+y][odd_pos[1]+x]=2
  counts={};positions={}
  for r in range(height-h+1):
    for c in range(width-w+1):
      m=[row[c:c+w] for row in g[r:r+h]]
      if any(2 in row for row in m):continue
      if not any(m[0]) or not any(m[-1]) or not any(row[0] for row in m) or not any(row[-1] for row in m):continue
      key=tuple(tuple(row) for row in m)
      counts[key]=counts.get(key,0)+1;positions.setdefault(key,[]).append((r,c))
  key=tuple(tuple(row) for row in rep)
  return (set(positions.get(key,[]))==set(copies) and all(n < len(copies) for k,n in counts.items() if k!=key))


def generate(width=None, height=None, rep=None, odd=None, rep_color=None,
             odd_color=None, copies=None, odd_pos=None,
             shape_height=None, shape_width=None, num_copies=None, packing=None):
  """Build one input/output pair.

  Args:
    width: grid width.
    height: grid height.
    rep: 0/1 rows giving the repeated shape's mask.
    odd: 0/1 rows giving the odd shape's mask, same size as rep.
    rep_color: colour of the repeated shape.
    odd_color: colour of the odd shape.
    copies: list of (row, col) top-left corners of the repeated copies.
    odd_pos: (row, col) top-left corner of the odd shape.
    shape_height, shape_width: random mask dimensions in 2..6.
    num_copies: exact number of repeated copies in 2..10.
    packing: "loose" or "tight" (random if omitted).
  """
  for d in (width,height):
    if d is not None and (not isinstance(d,int) or not 1 <= d <= 30):
      raise ValueError("Dimensions must be in 1..30")
  for colour in (rep_color,odd_color):
    if colour is not None and colour not in range(1,10):
      raise ValueError("Foreground colours must be in 1..9")
  if rep_color is not None and rep_color == odd_color:
    raise ValueError("Foreground colours must differ")
  if packing not in (None,"loose","tight"):
    raise ValueError("packing must be loose or tight")
  for d in (shape_height,shape_width):
    if d is not None and (not isinstance(d,int) or not 2 <= d <= 6):
      raise ValueError("Random mask dimensions must be in 2..6")
  if num_copies is not None and (not isinstance(num_copies,int) or not 2 <= num_copies <= 10):
    raise ValueError("num_copies must be in 2..10")
  if rep is None:
    if odd is not None or copies is not None or odd_pos is not None:
      raise ValueError("Explicit masks and positions must be supplied together")
    if any(d is not None and d < 7 for d in (width,height)):
      raise ValueError("Random dimensions must be at least 7")
    pack = packing if packing is not None else random.choice(("loose","tight"))
    for _ in range(500):
      h = shape_height if shape_height is not None else random.choice([2,2,3,3,4,5,6])
      w = shape_width if shape_width is not None else random.choice([2,2,3,3,4,5,6])
      rep_m,odd_m = _random_shape(h,w),_random_shape(h,w)
      if rep_m == odd_m:continue
      n = num_copies if num_copies is not None else random.randint(2,10)
      if n*sum(map(sum,rep_m)) <= sum(map(sum,odd_m)):continue
      W = width if width is not None else random.randint(max(7,w+4),30)
      H = height if height is not None else random.randint(max(7,h+4),30)
      # Black remains the background under the archived rule's modal estimate.
      if W*H-n*sum(map(sum,rep_m))-sum(map(sum,odd_m)) <= n*sum(map(sum,rep_m)):continue
      gap=max(1,max(h,w)-1) if pack=="loose" else 0
      boxes=[]
      for _ in range(400):
        if len(boxes)==n+1:break
        p=(random.randint(0,H-h),random.randint(0,W-w))
        if all(_separated(p,q,h,w,gap) for q in boxes):boxes.append(p)
      if len(boxes)!=n+1:continue
      if not _identifiable(rep_m,odd_m,boxes[1:],boxes[0],H,W):continue
      rep,odd,width,height=rep_m,odd_m,W,H
      odd_pos,copies=boxes[0],boxes[1:]
      break
    else:raise RuntimeError("Could not place identifiable shapes with requested controls")
  else:
    if any(x is not None for x in (shape_height,shape_width,num_copies,packing)):
      raise ValueError("Random sampling controls cannot accompany explicit masks")
  if rep_color is None:rep_color=random.choice([c for c in range(1,10) if c!=odd_color])
  if odd_color is None:odd_color=random.choice([c for c in range(1,10) if c!=rep_color])
  if any(x is None for x in (rep,odd,width,height,copies,odd_pos)):
    raise ValueError("Explicit masks and positions require complete geometry")
  for mask in (rep,odd):
    if not mask or not mask[0] or any(len(row)!=len(mask[0]) or any(v not in (0,1) for v in row) for row in mask):
      raise ValueError("Masks must be rectangular binary arrays")
    if not all((any(mask[0]),any(mask[-1]),any(row[0] for row in mask),any(row[-1] for row in mask))):
      raise ValueError("Masks must touch every box edge")
  if len(rep)!=len(odd) or len(rep[0])!=len(odd[0]) or rep==odd:
    raise ValueError("Masks must differ and have equal dimensions")
  h,w=len(rep),len(rep[0]);positions=list(copies)+[odd_pos]
  if len(copies)<2 or len(copies)*sum(map(sum,rep))<=sum(map(sum,odd)):
    raise ValueError("Repeated colour must have greater total area")
  for i,(r,c) in enumerate(positions):
    if not (0<=r<=height-h and 0<=c<=width-w):raise ValueError("Shape outside canvas")
    if any(not _separated((r,c),q,h,w,0) for q in positions[:i]):raise ValueError("Boxes must not overlap")
  h, w = len(rep), len(rep[0])
  inp = common.grid(width, height, 0)
  out = common.grid(width, height, 0)
  for (r, c) in copies:
    for i in range(h):
      for j in range(w):
        if rep[i][j]:
          inp[r + i][c + j] = rep_color
        if odd[i][j]:
          out[r + i][c + j] = odd_color
  r, c = odd_pos
  for i in range(h):
    for j in range(w):
      if odd[i][j]:
        inp[r + i][c + j] = odd_color
      if rep[i][j]:
        out[r + i][c + j] = rep_color
  return {"input": inp, "output": out}


def validate():
  """Rebuild the canonical pairs from explicit latent arguments."""
  train = [
      generate(width=10, height=9, rep=[[1, 0, 1], [0, 1, 0], [0, 1, 0]],
               odd=[[0, 1, 0], [1, 1, 1], [0, 1, 0]], rep_color=3,
               odd_color=8, copies=[(1, 1), (1, 5)], odd_pos=(5, 1)),
      generate(width=12, height=9, rep=[[1, 1], [1, 0]],
               odd=[[0, 1], [1, 1]], rep_color=2, odd_color=3,
               copies=[(1, 1), (1, 4), (1, 7), (4, 4)], odd_pos=(4, 7)),
      generate(width=10, height=11, rep=[[1, 0], [0, 1]],
               odd=[[0, 1], [1, 0]], rep_color=1, odd_color=7,
               copies=[(1, 1), (1, 4), (4, 1), (7, 1)], odd_pos=(1, 7)),
      generate(width=17, height=9, rep=[[0, 1, 0], [1, 1, 1]],
               odd=[[1, 1, 1], [0, 1, 0]], rep_color=8, odd_color=1,
               copies=[(1, 7), (3, 4), (3, 10), (5, 1), (5, 13)],
               odd_pos=(5, 7)),
  ]
  test = [
      generate(width=14, height=11, rep=[[1, 0, 1], [0, 1, 0], [1, 1, 1]],
               odd=[[1, 1, 1], [1, 0, 1], [0, 0, 1]], rep_color=5,
               odd_color=6, copies=[(1, 2), (1, 7), (5, 7)],
               odd_pos=(5, 2)),
  ]
  return {"train": train, "test": test}
