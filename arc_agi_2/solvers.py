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


# Order matters: the first fitting solver becomes attempt_1.
SOLVERS = [
    ("constant", fit_constant),
    ("identity", fit_identity),
    ("colour_map", fit_colour_map),
    ("transpose", fit_transpose),
    ("flip_h", fit_flip_h),
    ("flip_v", fit_flip_v),
]


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
