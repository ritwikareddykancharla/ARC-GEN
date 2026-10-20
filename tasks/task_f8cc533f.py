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

"""Complete damaged copies of a shared D4-symmetric pattern.

Random scenes retain the original latent pattern construction and labels.
A scene is exported only when its input has a unique minimum-addition shared
completion matching that latent answer. This excludes hidden placement and
missing-colour ambiguity. Explicit fixture reconstruction remains unchanged.
"""

import common


def _unique_shared_completion(grid, max_size=7, budget=100000):
    """Find the unique minimum-addition shared D4-symmetric completion.

    Enumerate square placements up to the native seven-cell pattern limit.
    The shared mask is exactly the union of the surviving cells in those
    placements: no unsupported orbit is invented. Every copy must be damaged,
    windows have a one-cell gap, and the mask has a full square bounding box.
    Minimise template population, then side length; never use scan order to
    break a tie between distinct output grids. Search exhaustion is a failure,
    not evidence of uniqueness. This also handles outer-empty latent patterns
    by searching their intrinsic bounding-box size.
    """
    from collections import Counter
    counts = Counter(v for row in grid for v in row)
    bg = max(counts, key=counts.get)
    if sum(n == counts[bg] for n in counts.values()) != 1:
        raise ValueError('ambiguous background')
    h, w = len(grid), len(grid[0])
    colours = sorted(set(counts) - {bg})
    cells = {c: [(r,x) for r,row in enumerate(grid) for x,v in enumerate(row) if v==c] for c in colours}
    boxes = {c: (min(r for r,x in cells[c]), min(x for r,x in cells[c]), max(r for r,x in cells[c]), max(x for r,x in cells[c])) for c in colours}
    lo = max(max(b[2]-b[0]+1,b[3]-b[1]+1) for b in boxes.values())
    answer = None
    best_score = None
    ambiguous = False
    work = 0
    for size in range(lo, min(max_size,h,w)+1):
        orbits=[]
        for y in range(size):
            for x in range(size):
                orbit=0
                for a,b in ((y,x),(x,y)):
                    for r,c in ((a,b),(size-1-a,b),(a,size-1-b),(size-1-a,size-1-b)):
                        orbit |= 1 << (r*size+c)
                orbits.append(orbit)
        closure_cache={0:0}
        def closure(mask):
            original = mask
            if mask not in closure_cache:
                old=mask; result=0
                while mask:
                    bit=mask & -mask; result |= orbits[bit.bit_length()-1]; mask ^= bit
                closure_cache[old]=result
            return closure_cache[original]
        opts=[]
        for colour in colours:
            y0,x0,y1,x1=boxes[colour]; choices=[]
            for y in range(max(0,y1-size+1),min(y0,h-size)+1):
                for x in range(max(0,x1-size+1),min(x0,w-size)+1):
                    if any(grid[r][c] not in (bg,colour) for r in range(y,y+size) for c in range(x,x+size)):continue
                    mask=sum(1 << ((r-y)*size+c-x) for r,c in cells[colour]);choices.append((y,x,mask))
            opts.append(choices)
        if any(not o for o in opts):continue
        possible=[0]*(len(opts)+1)
        for i in range(len(opts)-1,-1,-1):
            possible[i]=possible[i+1]
            for y,x,mask in opts[i]:possible[i]|=mask
        def search(i,mask,chosen):
            nonlocal work,answer,best_score,ambiguous
            work+=1
            if work>budget:raise ValueError('completion search budget exceeded')
            if best_score is not None and (mask.bit_count(),size)>best_score:return
            if closure(mask) & ~(mask|possible[i]):return
            if i==len(opts):
                if mask!=closure(mask) or not mask & ((1<<size)-1):return
                n=mask.bit_count()
                if any(len(cells[c])>=n for c in colours):return
                output=[row[:] for row in grid]
                for col,(y,x,_) in zip(colours,chosen):
                    bits=mask
                    while bits:
                        bit=bits&-bits;k=bit.bit_length()-1;output[y+k//size][x+k%size]=col;bits^=bit
                key=tuple(map(tuple,output))
                score=(n,size)
                if best_score is None or score<best_score:
                    best_score=score; answer=key; ambiguous=False
                elif score==best_score and answer!=key:ambiguous=True
                return
            for y,x,raw in opts[i]:
                if any(not (y+size<yy or yy+size<y or x+size<xx or xx+size<x) for yy,xx,_ in chosen):continue
                search(i+1,mask|raw,chosen+[(y,x,raw)])
        search(0,0,[])
    if answer is None:raise ValueError('no supported shared pattern')
    if ambiguous:raise ValueError('ambiguous shared pattern')
    return [list(row) for row in answer]


def generate(width=None, height=None, length=None, brows=None, bcols=None,
             bcolors=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: The width of the grid.
    height: The height of the grid.
    length: The length of the pattern.
    brows: The rows of the boxes.
    bcols: The columns of the boxes.
    bcolors: The colors of the boxes.
    colors: The colors of the input grid.
  """

  def draw():
    grid, output = common.grids(width, height)
    for i, color in enumerate(colors):
      output[i // width][i % width] = grid[i // width][i % width] = color
    pattern = common.grid(length, length)
    for brow, bcol, bcolor in zip(brows, bcols, bcolors):
      for row in range(length):
        for col in range(length):
          if grid[brow + row][bcol + col] == bcolor:
            pattern[row][col] = 1
    for brow, bcol, bcolor in zip(brows, bcols, bcolors):
      some_missing = False
      for row in range(length):
        for col in range(length):
          if not pattern[row][col]: continue
          if output[brow + row][bcol + col] != bcolor: some_missing = True
          output[brow + row][bcol + col] = bcolor
      if not some_missing: return None, None
    return grid, output

  if width is None:
    length = common.randint(5, 7)
    bgcolor = common.random_color()
    num_boxes = common.randint(2, 4)
    bcolors = common.random_colors(num_boxes, exclude=[bgcolor])
    while True:
      width, height = common.randint(10, 22), common.randint(10, 22)
      if width * height < 11 * 19: continue
      # Choose the locations of the boxes.
      brows = [common.randint(0, height - length) for _ in range(num_boxes)]
      bcols = [common.randint(0, width - length) for _ in range(num_boxes)]
      lengths = [length] * num_boxes
      if common.overlaps(brows, bcols, lengths, lengths, 1): continue
      # Create a fully symmetric pattern.
      pattern = common.grid(length, length)
      for row in range(length):
        for col in range(length):
          if common.randint(0, 9): continue
          for r, c in [(row, col), (col, row)]:
            pattern[r][c] = 1
            pattern[r][length - 1 - c] = 1
            pattern[length - 1 - r][c] = 1
            pattern[length - 1 - r][length - 1 - c] = 1
      if len(set(common.flatten(pattern))) != 2: continue
      # Create the input.
      grid, expected = common.grids(width, height, bgcolor)
      for brow, bcol, bcolor in zip(brows, bcols, bcolors):
        for row in range(length):
          for col in range(length):
            if not pattern[row][col]: continue
            expected[brow + row][bcol + col] = bcolor
            if common.randint(0, 9): grid[brow + row][bcol + col] = bcolor
      colors = common.flatten(grid)
      # Finally, check that we can faithfully construct the pattern.
      grid, output = draw()
      if grid and expected == output:
        try:
          inferred = _unique_shared_completion(grid)
        except ValueError:
          continue
        if inferred == output:
          break

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=19, height=19, length=5, brows=[2, 2, 10, 11],
               bcols=[3, 11, 1, 11], bcolors=[8, 4, 2, 1],
               colors=[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 8, 8, 3, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3,
                       3, 3, 3, 3, 8, 3, 8, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 8, 3, 3, 3, 8, 3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3,
                       3, 3, 3, 8, 8, 3, 8, 8, 3, 3, 3, 4, 4, 3, 4, 4, 3, 3, 3,
                       3, 3, 3, 3, 8, 3, 8, 3, 3, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 1, 3, 3, 3, 3,
                       3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 1, 1, 3, 1, 1, 3, 3, 3,
                       3, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3,
                       3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 1, 1, 3, 1, 1, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                       3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
      generate(width=19, height=11, length=6, brows=[1, 5], bcols=[9, 1],
               bcolors=[4, 1],
               colors=[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                       2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 4, 2, 2, 2, 2, 2,
                       2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 2, 2, 2, 2,
                       2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 4, 2, 2, 2, 2, 2,
                       2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2,
                       2, 2, 1, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2,
                       2, 1, 1, 1, 1, 2, 1, 2, 2, 2, 4, 2, 2, 4, 2, 2, 2, 2, 2,
                       2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                       2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                       2, 2, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                       2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]),
      generate(width=19, height=11, length=5, brows=[1, 1, 4], bcols=[2, 14, 8],
               bcolors=[3, 8, 2],
               colors=[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 4, 8, 4,
                       4, 4, 3, 3, 4, 3, 3, 4, 4, 4, 4, 4, 4, 4, 8, 8, 4, 8, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 3, 3, 4, 3, 3, 4, 4, 2, 4, 2, 4, 4, 8, 8, 4, 4, 4,
                       4, 4, 4, 3, 4, 3, 4, 4, 2, 2, 4, 2, 4, 4, 4, 8, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 4, 4, 2, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]),
  ]
  test = [
      generate(width=18, height=20, length=5, brows=[2, 7, 11],
               bcols=[3, 10, 1], bcolors=[2, 3, 1],
               colors=[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 2, 4, 2, 4, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 4, 3, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 3, 4, 3, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 3, 4, 4, 4,
                       4, 1, 4, 4, 1, 1, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4,
                       4, 1, 4, 1, 4, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 1, 4, 1, 4, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                       4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]),
      generate(width=22, height=22, length=7, brows=[1, 2, 10, 13],
               bcols=[1, 11, 3, 13], bcolors=[1, 6, 4, 3],
               colors=[8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 1, 1, 1, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 1, 8, 8, 1, 8, 8, 8, 8, 8, 8, 6, 6, 6, 8, 8, 8, 8, 8, 8,
                       8, 1, 1, 1, 8, 1, 1, 1, 8, 8, 8, 8, 6, 6, 8, 8, 6, 8, 8, 8, 8, 8,
                       8, 1, 8, 8, 1, 8, 8, 1, 8, 8, 8, 6, 6, 6, 8, 6, 6, 6, 8, 8, 8, 8,
                       8, 1, 1, 1, 8, 1, 1, 1, 8, 8, 8, 6, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8,
                       8, 8, 1, 1, 8, 1, 1, 8, 8, 8, 8, 8, 8, 6, 8, 6, 6, 6, 8, 8, 8, 8,
                       8, 8, 8, 8, 1, 1, 8, 8, 8, 8, 8, 8, 6, 6, 8, 6, 6, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 4, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 4, 4, 8, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 4, 4, 4, 8, 4, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 4, 8, 8, 4, 8, 8, 8, 8, 8, 3, 3, 3, 8, 8, 8, 8,
                       8, 8, 8, 4, 4, 4, 8, 4, 4, 4, 8, 8, 8, 8, 3, 3, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 4, 4, 8, 4, 8, 8, 8, 8, 8, 3, 3, 3, 8, 8, 3, 3, 8, 8,
                       8, 8, 8, 8, 8, 4, 4, 4, 8, 8, 8, 8, 8, 3, 8, 8, 3, 8, 8, 3, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 3, 3, 8, 3, 3, 3, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 8, 8, 3, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3, 3, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]),
  ]
  return {"train": train, "test": test}
