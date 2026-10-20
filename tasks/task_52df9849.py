# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator."""

import common


_MAX_ATTEMPTS = 100000

def _bounds(cells):
    return (min(r for r,c in cells),max(r for r,c in cells),min(c for r,c in cells),max(c for r,c in cells))


def _staircase(cells,box,vertical):
    r0,r1,c0,c1=box
    intervals=[]
    for a in range(r0,r1+1) if vertical else range(c0,c1+1):
        positions=sorted(c if vertical else r for r,c in cells if (r if vertical else c)==a)
        if not positions or positions!=list(range(positions[0],positions[-1]+1)):return False
        intervals.append((positions[0],positions[-1]))
    lower,upper=(c0,c1) if vertical else (r0,r1)
    for rows in (intervals,intervals[::-1]):
        if rows[0]!=(lower,upper):continue
        if all(nl-l in (0,1) and rr-nr in (0,1) for (l,rr),(nl,nr) in zip(rows,rows[1:])):
            return True
    return False


def _shape(cells,box):
    r0,r1,c0,c1=box
    if len(cells)==(r1-r0+1)*(c1-c0+1):return True
    if r1-r0==c1-c0 and len(cells)==r1-r0+1:
        if len({r-c for r,c in cells})==1 or len({r+c for r,c in cells})==1:return True
    return _staircase(cells,box,True) or _staircase(cells,box,False)


def _options(grid,colour,bg):
    visible=frozenset((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==colour)
    box=_bounds(visible);r0,r1,c0,c1=box
    options=set()
    if _shape(visible,box): options.add((False,visible))
    candidates=set()
    corners=[(r0,c0),(r0,c1),(r1,c0),(r1,c1)]
    if sum(p in visible for p in corners)>=3:
        candidates.add(frozenset((r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)))
    for vertical in (True,False):
        mask=set();valid=True
        for a in range(r0,r1+1) if vertical else range(c0,c1+1):
            positions=[c if vertical else r for r,c in visible if (r if vertical else c)==a]
            if not positions:valid=False;break
            for b in range(min(positions),max(positions)+1):mask.add((a,b) if vertical else (b,a))
        if valid and _staircase(mask,box,vertical):candidates.add(frozenset(mask))
    if r1-r0==c1-c0:
        if len({r-c for r,c in visible})==1:
            candidates.add(frozenset((r0+i,c0+i) for i in range(r1-r0+1)))
        if len({r+c for r,c in visible})==1:
            candidates.add(frozenset((r0+i,c1-i) for i in range(r1-r0+1)))
    for cells in candidates:
        if cells>visible and all(grid[r][c]!=bg for r,c in cells):
            options.add((True,cells))
    return box,visible,sorted(options,key=lambda x:(x[0],sorted(x[1])))


def _separate(a,b):
    return not any((r+dr,c+dc) in b for r,c in a for dr in (-1,0,1) for dc in (-1,0,1))


def _visible_outputs(grid,bg):
    colours=sorted({v for row in grid for v in row}-{bg})
    info={c:_options(grid,c,bg) for c in colours}
    order=sorted(colours,key=lambda c:len(info[c][2]))
    chosen={};answers=set();nodes=0
    def rec(index):
        nonlocal nodes
        nodes+=1
        if nodes>200000:raise RuntimeError('Layer search budget exhausted')
        if len(answers)>1:return
        if index==len(order):
            covered=set()
            for colour,(bottom,cells) in chosen.items():
                if not bottom:continue
                for r,c in cells:
                    other=grid[r][c]
                    if other!=colour and chosen[other][0]:return
                covered.update(cells)
            for colour,(bottom,cells) in chosen.items():
                if not bottom and (not cells&covered or not cells-covered):return
            out=[list(row) for row in grid]
            for colour,(bottom,cells) in chosen.items():
                if bottom:
                    for r,c in cells:out[r][c]=colour
            answers.add(tuple(map(tuple,out)))
            return
        colour=order[index];box,visible,options=info[colour]
        for bottom,cells in options:
            if any(bottom==ob and not _separate(cells,other_cells) for oc,(ob,other_cells) in chosen.items()):continue
            if bottom and any(grid[r][c] in chosen and grid[r][c]!=colour and chosen[grid[r][c]][0] for r,c in cells):continue
            chosen[colour]=(bottom,cells);rec(index+1);del chosen[colour]
            if len(answers)>1:return
    rec(0)
    return answers


def generate(wides=None, talls=None, rows=None, cols=None, colors=None,
             orders=None, shapes=None):
  """Returns input and output grids according to the given parameters.

  Args:
    wides: widths of the boxes.
    talls: talls of the boxes.
    rows: rows of the boxes.
    cols: columns of the boxes.
    colors: colors of the boxes.
    orders: order of the boxes.
    shapes: shapes of the boxes.
  """

  def draw():
    grid, output = common.grids(16, 16, 7)
    # Draw the shapes without checking anything.
    for order in [0, 1]:
      for t, w, r, c, l, o, s in zip(talls, wides, rows, cols, colors, orders, shapes):
        layer = grid if o == order else output
        if s == 0: common.rect(layer, w, t, r, c, l)
        if s == 1: common.backslash(layer, w, r, c, l)
        if s == 2: common.slash(layer, w, r, c, l)
    # Check #1: every color must be visible in both grids.
    flattened_grid = common.flatten(grid)
    flattened_output = common.flatten(output)
    for color in colors:
      if color not in flattened_grid or color not in flattened_output:
        return None, None
    # Check #2: every color must be partially obscured by another color.
    obscured = set()
    for t, w, r, c, l, o, s in zip(talls, wides, rows, cols, colors, orders, shapes):
      layer = output if o else grid
      if s == 0 and common.rect_obscured(layer, w, t, r, c, l): obscured.add(l)
      if s == 1 and common.backslash_obscured(layer, w, r, c, l): obscured.add(l)
      if s == 2 and common.slash_obscured(layer, w, r, c, l): obscured.add(l)
    if len(obscured) != len(set(colors)): return None, None
    # Check #3: for every object, over half of all corners must be visible.
    for t, w, r, c, l, o, s in zip(talls, wides, rows, cols, colors, orders, shapes):
      if o: continue  # We're only worried about objects hidden in *input* background.
      layer = output if o else grid
      if s == 0 and not common.rect_visible(layer, w, t, r, c, l): return None, None
      if s == 1 and not common.backslash_visible(layer, w, r, c, l): return None, None
      if s == 2 and not common.slash_visible(layer, w, r, c, l): return None, None
    return grid, output

  if wides is None:
    num_boxes = [common.randint(1, 3), common.randint(1, 3)]
    for _ in range(_MAX_ATTEMPTS):
      # These are the "pre-shaved" lists.
      pwides, ptalls, prows, pcols, pcolors, porders, pshapes = [], [], [], [], [], [], []
      good = True
      for o in [0, 1]:
        ws,ts,rs,cs = [],[],[],[]
        for _object in range(num_boxes[o]):
          placed = False
          for _size_try in range(12):
            w,t = common.randint(1,16),common.randint(1,16)
            positions = [(r,c) for r in range(17-t) for c in range(17-w)
                         if not common.overlaps(rs+[r],cs+[c],ws+[w],ts+[t],1)]
            if not positions: continue
            r,c = common.sample(positions,1)[0]
            ws.append(w);ts.append(t);rs.append(r);cs.append(c)
            placed = True
            break
          if not placed: break
        if len(ws)!=num_boxes[o]:
          good = False
          break
        available = [c for c in [0, 1, 2, 3, 4, 5, 6, 8, 9] if c not in pcolors]
        ls = common.sample(available, num_boxes[o])
        os = [o] * len(ws)
        ss = [0 if w != t else common.randint(1, 2) for w, t in zip(ws, ts)]
        pwides.extend(ws)
        ptalls.extend(ts)
        prows.extend(rs)
        pcols.extend(cs)
        pcolors.extend(ls)
        porders.extend(os)
        pshapes.extend(ss)
      if not good: continue
      # Now, shave down some of the rectangles.
      wides, talls, rows, cols, colors, orders, shapes = [], [], [], [], [], [], []
      for w, t, r, c, l, o, s in zip(pwides, ptalls, prows, pcols, pcolors, porders, pshapes):
        if s != 0 or common.randint(0, 4) > 0:
          wides.append(w)
          talls.append(t)
          rows.append(r)
          cols.append(c)
          colors.append(l)
          orders.append(o)
          shapes.append(s)
          continue
        swides, stalls, srows, scols = common.shave(w, t, r, c)
        wides.extend(swides)
        talls.extend(stalls)
        rows.extend(srows)
        cols.extend(scols)
        colors.extend([l] * len(swides))
        orders.extend([o] * len(swides))
        shapes.extend([s] * len(swides))
      grid, output = draw()
      if grid:
        try:
          answers = _visible_outputs(grid,7)
        except RuntimeError:
          continue
        if answers == {tuple(map(tuple,output))}: break
    else:
      raise RuntimeError("52df9849: no identifiable scene within attempt budget")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(wides=[4, 5], talls=[6, 7], rows=[4, 6], cols=[7, 4],
               colors=[4, 1], orders=[0, 1], shapes=[0, 0]),
      generate(wides=[1, 10], talls=[11, 1], rows=[2, 7], cols=[5, 2],
               colors=[5, 9], orders=[1, 0], shapes=[0, 0]),
  ]
  test = [
      generate(wides=[2, 2, 4, 14, 16], talls=[12, 12, 12, 2, 3],
               rows=[2, 2, 2, 4, 9], cols=[2, 6, 10, 1, 0],
               colors=[5, 8, 6, 9, 1], orders=[1, 1, 1, 0, 0],
               shapes=[0, 0, 0, 0, 0]),
      generate(wides=[15, 11, 10, 8, 7, 5, 4, 2, 1, 3],
               talls=[15, 1, 1, 1, 1, 1, 1, 1, 1, 5],
               rows=[1, 10, 9, 8, 7, 6, 5, 4, 3, 4],
               cols=[0, 4, 5, 6, 7, 8, 9, 10, 11, 13],
               colors=[3, 8, 8, 8, 8, 8, 8, 8, 8, 2],
               orders=[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
               shapes=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
  ]
  return {"train": train, "test": test}
