"""Deterministic baseline solvers for ARC-AGI-2.

Stdlib only, on purpose. A grid is a list of rows, each row a list of ints 0-9.

The point of this module is not to score well. It is to make the *shape* of a
solver explicit: a solver looks at a task's training pairs, decides whether it
can explain them, and if so predicts an output for a new input. Everything
smarter plugs into the same two functions, so the submission pipeline never
changes again.

Selection rule: a solver is only used on a task if it reproduces **every**
training output exactly. That is the one honest signal available before the
hidden test grid is scored, and it costs nothing to check.
"""

from collections import Counter

Grid = list  # list[list[int]]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def dims(g: Grid) -> tuple:
    return len(g), len(g[0]) if g else 0


def same(a: Grid, b: Grid) -> bool:
    return a == b


def rot90(g: Grid) -> Grid:
    """Clockwise."""
    return [list(r) for r in zip(*g[::-1])]


def rot180(g: Grid) -> Grid:
    return [row[::-1] for row in g[::-1]]


def rot270(g: Grid) -> Grid:
    return [list(r) for r in zip(*g)][::-1]


def anti_transpose(g: Grid) -> Grid:
    return rot180([list(r) for r in zip(*g)])


def tile(g: Grid, a: int, b: int) -> Grid:
    wide = [row * b for row in g]
    return [r[:] for _ in range(a) for r in wide]


def scale(g: Grid, a: int, b: int) -> Grid:
    out = []
    for row in g:
        wide = [v for v in row for _ in range(b)]
        out.extend(wide[:] for _ in range(a))
    return out


def background(g: Grid) -> int:
    """The most common colour. Ties break to the lower colour, deterministically."""
    counts = Counter(v for row in g for v in row)
    return min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]


# ---------------------------------------------------------------------------
# solvers
#
# Each is a callable: fit(train_pairs) -> predict(input_grid) -> Grid | None.
# fit returns None when the solver cannot explain the training pairs at all,
# which is cheaper than predicting and checking afterwards.
# ---------------------------------------------------------------------------

def fit_identity(pairs):
    """Output is the input, untouched."""
    if all(same(p["input"], p["output"]) for p in pairs):
        return lambda g: [row[:] for row in g]
    return None


def fit_constant(pairs):
    """Every training pair produces the same output, whatever the input."""
    outs = [p["output"] for p in pairs]
    first = outs[0]
    if all(same(o, first) for o in outs):
        return lambda g, out=first: [row[:] for row in out]
    return None


def fit_colour_map(pairs):
    """Same shape in and out, with one consistent colour substitution.

    Rejects any mapping that is ambiguous — a colour sending to two different
    colours across the training set means this is not what the task is doing,
    and guessing which one wins would be inventing a rule.
    """
    mapping: dict = {}
    for p in pairs:
        gi, go = p["input"], p["output"]
        if dims(gi) != dims(go):
            return None
        for ri, ro in zip(gi, go):
            for a, b in zip(ri, ro):
                if mapping.setdefault(a, b) != b:
                    return None

    def predict(g, m=mapping):
        # Refuse rather than guess. A colour absent from every training input has
        # no learned image, and passing it through unchanged is a guess dressed
        # as a rule. Training task aabf363d is the case: colour 8 appears only at
        # test time, the identity fallthrough got 16 of 49 cells wrong, and the
        # task counted as solved-then-failed instead of honestly abstained.
        # Same discipline as rejecting a rule that misses one demonstration cell.
        if any(v not in m for row in g for v in row):
            return None
        return [[m[v] for v in row] for row in g]

    return predict


def fit_transpose(pairs):
    for p in pairs:
        gi, go = p["input"], p["output"]
        if [list(r) for r in zip(*gi)] != go:
            return None
    return lambda g: [list(r) for r in zip(*g)]


def fit_flip_h(pairs):
    for p in pairs:
        if [row[::-1] for row in p["input"]] != p["output"]:
            return None
    return lambda g: [row[::-1] for row in g]


def fit_flip_v(pairs):
    for p in pairs:
        if p["input"][::-1] != p["output"]:
            return None
    return lambda g: g[::-1]


def fit_most_common_colour(pairs):
    """Degenerate fallback: a 1x1 grid of the input's most common colour.

    Never fits a real task. It exists so `attempt_2` is always populated with
    something well-formed rather than a duplicate of attempt_1.
    """
    return None


# ---------------------------------------------------------------------------
# tranche 2 - added 2026-09-05
#
# These exist to move one number: the size of the hypothesis library. The claim
# under test (see README.md) is that demonstration-consistency
# stays a near-perfect selector as the library grows. That is only measurable
# if the library actually grows, in tranches, with precision recorded at each
# step. See `measure.py`.
#
# Every one obeys the same two rules as tranche 1: reject unless the rule
# reproduces *every* demonstration exactly, and return None rather than guess
# when the rule is underdetermined for this particular input.
# ---------------------------------------------------------------------------

def _whole_grid(op):
    """Build a fit function for a parameterless whole-grid geometric op."""

    def fit(pairs, op=op):
        for p in pairs:
            if op(p["input"]) != p["output"]:
                return None
        return lambda g, op=op: op(g)

    return fit


fit_rot90 = _whole_grid(rot90)
fit_rot180 = _whole_grid(rot180)
fit_rot270 = _whole_grid(rot270)
fit_anti_transpose = _whole_grid(anti_transpose)
fit_mirror_h = _whole_grid(lambda g: [row + row[::-1] for row in g])
fit_mirror_v = _whole_grid(lambda g: [r[:] for r in g] + [r[:] for r in g[::-1]])


def fit_tile(pairs):
    """Output is the input repeated a x b times. One factor pair for the task."""
    factors = set()
    for p in pairs:
        gi, go = p["input"], p["output"]
        h, w = dims(gi)
        H, W = dims(go)
        if not h or not w or H % h or W % w:
            return None
        a, b = H // h, W // w
        if (a, b) == (1, 1):
            return None  # identity wearing a tiling costume
        if tile(gi, a, b) != go:
            return None
        factors.add((a, b))
    if len(factors) != 1:
        return None
    (a, b), = factors
    return lambda g, a=a, b=b: tile(g, a, b)


def fit_scale(pairs):
    """Each cell becomes an a x b block. One factor pair for the task."""
    factors = set()
    for p in pairs:
        gi, go = p["input"], p["output"]
        h, w = dims(gi)
        H, W = dims(go)
        if not h or not w or H % h or W % w:
            return None
        a, b = H // h, W // w
        if (a, b) == (1, 1):
            return None
        if scale(gi, a, b) != go:
            return None
        factors.add((a, b))
    if len(factors) != 1:
        return None
    (a, b), = factors
    return lambda g, a=a, b=b: scale(g, a, b)


def _unscale(g: Grid, a: int, b: int):
    """Inverse of scale, or None when a block is not one colour."""
    h, w = dims(g)
    if not h or not w or h % a or w % b:
        return None
    out = []
    for i in range(0, h, a):
        row = []
        for j in range(0, w, b):
            block = {g[i + di][j + dj] for di in range(a) for dj in range(b)}
            if len(block) != 1:
                return None
            row.append(block.pop())
        out.append(row)
    return out


def fit_downscale(pairs):
    """Block-reduce by a x b, where every block is a single colour."""
    factors = set()
    for p in pairs:
        gi, go = p["input"], p["output"]
        h, w = dims(gi)
        H, W = dims(go)
        if not H or not W or h % H or w % W:
            return None
        a, b = h // H, w // W
        if (a, b) == (1, 1):
            return None
        if _unscale(gi, a, b) != go:
            return None
        factors.add((a, b))
    if len(factors) != 1:
        return None
    (a, b), = factors
    # A non-uniform block at test time means the rule does not apply here, so
    # _unscale returns None. That is an abstention, not a guess.
    return lambda g, a=a, b=b: _unscale(g, a, b)


def _bbox(g: Grid, bg: int):
    rows = [i for i, row in enumerate(g) if any(v != bg for v in row)]
    if not rows:
        return None
    cols = [j for j in range(len(g[0])) if any(row[j] != bg for row in g)]
    if not cols:
        return None
    return [row[min(cols):max(cols) + 1] for row in g[min(rows):max(rows) + 1]]


def fit_crop_bbox(pairs):
    """Crop to the bounding box of everything that is not the background."""
    for p in pairs:
        gi = p["input"]
        if _bbox(gi, background(gi)) != p["output"]:
            return None
    return lambda g: _bbox(g, background(g))


def fit_strip_border(pairs):
    """Drop one cell from every edge."""
    for p in pairs:
        gi = p["input"]
        h, w = dims(gi)
        if h < 3 or w < 3:
            return None
        if [row[1:-1] for row in gi[1:-1]] != p["output"]:
            return None
    return lambda g: ([row[1:-1] for row in g[1:-1]]
                      if len(g) >= 3 and len(g[0]) >= 3 else None)


def fit_add_border(pairs):
    """Surround the input with a one-cell frame of a single fixed colour."""
    colours = set()
    for p in pairs:
        gi, go = p["input"], p["output"]
        h, w = dims(gi)
        if dims(go) != (h + 2, w + 2):
            return None
        frame = set(go[0]) | set(go[-1]) | {r[0] for r in go} | {r[-1] for r in go}
        if len(frame) != 1:
            return None
        if [row[1:-1] for row in go[1:-1]] != gi:
            return None
        colours.add(frame.pop())
    if len(colours) != 1:
        return None
    c, = colours
    return lambda g, c=c: ([[c] * (len(g[0]) + 2)]
                           + [[c] + row[:] + [c] for row in g]
                           + [[c] * (len(g[0]) + 2)])


def _pick(sel):
    """1x1 output holding a colour chosen from the input by `sel`."""

    def fit(pairs, sel=sel):
        for p in pairs:
            c = sel(p["input"])
            if c is None or p["output"] != [[c]]:
                return None
        return lambda g, sel=sel: (None if sel(g) is None else [[sel(g)]])

    return fit


def _most_common(g):
    counts = Counter(v for row in g for v in row)
    return min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0] if counts else None


def _least_common(g):
    counts = Counter(v for row in g for v in row)
    return min(counts.items(), key=lambda kv: (kv[1], kv[0]))[0] if counts else None


def _most_common_non_bg(g):
    counts = Counter(v for row in g for v in row)
    if len(counts) < 2:
        return None
    del counts[background(g)]
    return min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]


fit_pick_most_common = _pick(_most_common)
fit_pick_least_common = _pick(_least_common)
fit_pick_most_common_non_bg = _pick(_most_common_non_bg)


# Order matters: the first fitting solver becomes attempt_1.
SOLVERS = [
    ("constant", fit_constant),
    ("identity", fit_identity),
    ("colour_map", fit_colour_map),
    ("transpose", fit_transpose),
    ("flip_h", fit_flip_h),
    ("flip_v", fit_flip_v),
    ("rot90", fit_rot90),
    ("rot180", fit_rot180),
    ("rot270", fit_rot270),
    ("anti_transpose", fit_anti_transpose),
    ("mirror_h", fit_mirror_h),
    ("mirror_v", fit_mirror_v),
    ("tile", fit_tile),
    ("scale", fit_scale),
    ("downscale", fit_downscale),
    ("crop_bbox", fit_crop_bbox),
    ("strip_border", fit_strip_border),
    ("add_border", fit_add_border),
    ("pick_most_common", fit_pick_most_common),
    ("pick_least_common", fit_pick_least_common),
    ("pick_most_common_non_bg", fit_pick_most_common_non_bg),
]

# Which tranche each solver joined in. The coverage-vs-selection claim is tested
# by replaying the library one tranche at a time and recording precision at each
# step, so this is data the experiment reads, not commit history. See measure.py.
TRANCHE = {name: (1 if i < 6 else 2) for i, (name, _) in enumerate(SOLVERS)}


# ---------------------------------------------------------------------------
# prediction
# ---------------------------------------------------------------------------

def fallback(pairs, grid: Grid) -> Grid:
    """Something well-formed when nothing fits.

    Copies the input. Wrong almost always, but it is a valid grid, and a valid
    wrong answer keeps the submission parseable — a malformed one can invalidate
    the whole file.
    """
    return [row[:] for row in grid]


def second_guess(pairs, grid: Grid) -> Grid:
    """A different-but-plausible answer for attempt_2.

    Uses the most common training output shape filled with that output's most
    common colour. Distinct from the identity fallback, so the two attempts are
    never the same grid.
    """
    out = pairs[0]["output"]
    h, w = dims(out)
    counts = Counter(v for row in out for v in row)
    fill = counts.most_common(1)[0][0] if counts else 0
    return [[fill] * w for _ in range(h)]


def predict(task) -> list:
    """Two attempts for every test input in a task.

    Returns a list of {"attempt_1": grid, "attempt_2": grid}, one per test
    input, which is exactly the per-task value the submission file wants.
    """
    pairs = task["train"]
    fitted = []
    for name, fit in SOLVERS:
        fn = fit(pairs)
        if fn is not None:
            fitted.append((name, fn))

    out = []
    for test in task["test"]:
        g = test["input"]
        # A fitted solver may still abstain on this particular input, so collect
        # what actually produced a grid rather than trusting the fit alone.
        got = [p for _, fn in fitted if (p := fn(g)) is not None]
        a1 = got[0] if got else fallback(pairs, g)
        a2 = got[1] if len(got) > 1 else second_guess(pairs, g)
        if a1 == a2:
            a2 = second_guess(pairs, g)
        out.append({"attempt_1": a1, "attempt_2": a2})
    return out


def fitted_names(task) -> list:
    """Which solvers explain this task's training pairs. For reporting."""
    return [n for n, fit in SOLVERS if fit(task["train"]) is not None]
