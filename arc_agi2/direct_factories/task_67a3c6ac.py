def build_program(d4, palette):
    k = int(d4) % 4
    if k % 2 == 0:
        body = (
            "def solve(demonstrations, grid):\n"
            "    # Mirror across the vertical centre line: each row is read backwards.\n"
            "    rows = [list(r) for r in grid]\n"
            "    return [[int(v) for v in r[::-1]] for r in rows]\n"
        )
    else:
        body = (
            "def solve(demonstrations, grid):\n"
            "    # Mirror across the horizontal centre line: each column is read backwards,\n"
            "    # so the row order is reversed and each row's contents stay the same.\n"
            "    rows = [list(r) for r in grid]\n"
            "    return [[int(v) for v in r] for r in rows[::-1]]\n"
        )
    return body
