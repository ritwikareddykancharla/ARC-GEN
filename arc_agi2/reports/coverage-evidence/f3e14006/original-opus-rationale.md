# Woven rectangle from two crossing marked lines: worked explanation

## What the input is made of

Each input has a background of 0 and two full lines that cross:

- **A horizontal line.** It is mostly one *thread colour* and contains two cells of a different *marker colour*.
- **A vertical line.** It also has its own thread colour and two marker cells of its own marker colour.
- **The crossing cell.** It shows one of the two thread colours. That tells us which line lies on top.

The program finds the two lines as the row and the column with the most non-background cells. The thread colour of each line is its most common colour, ignoring the crossing cell. Its markers are the remaining non-background cells on that line.

| Pair | Horizontal line (row, thread, markers) | Vertical line (column, thread, markers) | Crossing cell |
|---|---|---|---|
| 1 | y=9, colour 3, markers 5 at x=6, 8 | x=2, colour 4, markers 2 at y=1, 6 | 3 (horizontal on top) |
| 2 | y=2, colour 8, markers 2 at x=2, 6 | x=7, colour 5, markers 9 at y=4, 8 | 8 (horizontal on top) |
| 3 | y=9, colour 3, markers 5 at x=6, 8 | x=2, colour 4, markers 2 at y=1, 3 | 4 (vertical on top) |
| 4 | y=4, colour 1, markers 3 at x=3, 8 | x=5, colour 7, markers 6 at y=7, 11 | 1 (horizontal on top) |

## How the output is built

Both lines are erased. A woven rectangle is drawn in their place.

**Extent of the rectangle**
- Columns run from the leftmost to the rightmost horizontal marker.
- Rows run from the topmost to the bottommost of these rows: the two vertical-marker rows and the horizontal line's row.

**Parity counted from the top of the rectangle**

Rows and columns are classed as even or odd by their offset from the rectangle's top-left corner (y0, x0). The parity is not counted from the marker positions.

- **Odd-offset rows (thread rows):**
  - Every cell gets the horizontal thread colour.
  - Exception: if the vertical line is on top at the crossing, the odd-offset columns get the vertical thread colour instead.
- **Even-offset rows (marker rows):**
  - Odd-offset columns get the vertical thread colour.
  - Even-offset columns get a marker colour. Which one depends on where the row lies:
    - **Vertical marker colour:** if the row lies inside the closed interval [top vertical marker, bottom vertical marker].
    - **Horizontal marker colour:** if the row lies outside that interval.

The interval test is applied to whichever even-offset rows fall inside it. The vertical marker rows themselves may sit at odd offsets. In that case they become plain thread rows.

**Special nearest-marker rule (kept from the reference, uncertain)**

- Take the vertical marker nearest the horizontal line.
- If its distance to the line is even, that marker's row uses the crossing-cell colour in its odd-offset columns instead of the vertical thread colour.
- Only pair 2 visibly depends on this. The rule is fitted to that single pair, so I cannot claim it generalises.

## Checking against the demonstrations

**Pair 1**
- Rectangle: x=6..8, y=1..9.
- Odd-offset rows 2, 4, 6, 8 are `3 3 3`, because horizontal is on top.
- Even-offset rows inside the interval [1, 6] are rows 1, 3, 5. They read `2 4 2`.
- Rows 7 and 9 lie outside the interval and read `5 4 5`.
- The nearest marker is y=6. Its distance to y=9 is 3, which is odd, so there is no special row. ✓

**Pair 2**
- Rectangle: x=2..6, y=2..8.
- Odd-offset rows 3, 5, 7 are all 8.
- Row 2 lies outside the interval [4, 8] and reads `2 5 2 5 2`.
- Rows 6 and 8 read `9 5 9 5 9`.
- The nearest marker is y=4. Its distance to y=2 is 2, which is even, so row 4 uses the crossing colour 8 and reads `9 8 9 8 9`. ✓

**Pair 3**
- Rectangle: x=6..8, y=1..9.
- The vertical line is on top, so odd-offset rows 2, 4, 6, 8 read `3 4 3`.
- Rows 1 and 3 lie inside the interval [1, 3] and read `2 4 2`.
- Rows 5, 7, 9 read `5 4 5`.
- The special rule fires on row 3, since the distance from y=3 to y=9 is 6. The crossing colour 4 equals the vertical thread colour, so nothing visibly changes. ✓

**Pair 4**
- Rectangle: x=3..8, y=4..11.
- Odd-offset rows 5, 7, 9, 11 are all 1.
- The vertical markers sit at y=7 and y=11, which are odd offsets. So those rows are thread rows, not marker rows.
- The even-offset rows inside the interval [7, 11] are rows 8 and 10. They read `6 7 6 7 6 7`.
- Rows 4 and 6 read `3 7 3 7 3 7`.
- This pair is the direct evidence for top-origin parity combined with the interval test. ✓

## Applying it to the queries

The results below come from running the supplied transform on the inputs.

**Query 1**
- Lines: horizontal at y=4 (colour 5, markers 2 at x=5, 10); vertical at x=2 (colour 6, markers 3 at y=17, 19). The crossing cell is 5, so horizontal is on top.
- Rectangle: x=5..10, y=4..19.
- Odd-offset rows 5, 7, …, 19 are six 5s each. This includes marker rows 17 and 19.
- Even-offset rows 4, 6, …, 16 lie outside the interval [17, 19] and read `2 6 2 6 2 6`.
- Row 18 is the only even-offset row inside the interval. It reads `3 6 3 6 3 6`.
- The nearest marker is y=17, at distance 13 from the line. That is odd, so there is no special row.

**Query 2**
- Lines: horizontal at y=4 (colour 7, markers 4 at x=1, 7); vertical at x=5 (colour 9, markers 8 at y=0, 3). The crossing cell is 7, so horizontal is on top.
- Rectangle: x=1..7, y=0..4.
- Rows 1 and 3 are seven 7s each.
- Rows 0 and 2 lie inside the interval [0, 3] and read `8 9 8 9 8 9 8`.
- Row 4 reads `4 9 4 9 4 9 4`.
- The nearest marker is y=3, at distance 1 from the line. That is odd, so there is no special row.

## Program (transformation unchanged; emits mark the stages)