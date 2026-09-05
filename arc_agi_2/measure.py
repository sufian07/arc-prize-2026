"""Coverage or selection? The experiment the entry is built around.

A score of 2% and a score of 0% look equally bad, and neither tells you where to
spend the next month. Two rival explanations sit behind a low non-learning score:

  coverage   — the hypothesis library is too small. The rules that would explain
               these tasks are simply not in it. Fix by adding rules.
  selection  — the library is big enough, but picking the right rule from the
               ones that fit the demonstrations is the hard part. Fix by ranking,
               test-time training, or search.

The field spends on both without measuring which binds. This module measures it.

**Claim under test.** For a non-learning solver on ARC-AGI-2, the binding
constraint is coverage, not selection: demonstration-consistency is a
near-perfect selector, so accuracy is bought linearly by adding rules at no
precision cost.

**Falsifier.** Precision falls as the library grows. If more rules means more
co-fitting rules that disagree, and the tie-break is wrong more often, then
selection binds and the claim is dead.

The measurement is a replay. `solvers.TRANCHE` records which batch each rule
joined in, so the library can be rebuilt at each size and scored again. Three
numbers matter and only one of them is accuracy:

  coverage     answered / total          how often any rule explains the task
  precision@1  correct@1 / answered      is the first fitting rule the right one
  ambiguity    disagreed / answered      how often fitting rules disagree at all

Precision is the claim's load-bearing number. Ambiguity is its mechanism: the
claim can only fail through rules that both fit and disagree, so ambiguity
staying near zero is *why* precision holds, and ambiguity rising while precision
holds would mean the ordering is doing real work that needs explaining.

    python -m arc_agi_2.measure --split training
    python -m arc_agi_2.measure --split evaluation
"""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arc_agi_2 import solvers  # noqa: E402
from arc_agi_2.run import DEFAULT_DATA, load  # noqa: E402


def library(k):
    """The solver list as it stood at tranche k, in SOLVERS order."""
    return [(n, f) for n, f in solvers.SOLVERS if solvers.TRANCHE.get(n, 1) <= k]


def hypotheses(lib, task, grid):
    """Distinct grids proposed for `grid` by rules that explain every demonstration.

    Ordered by SOLVERS order, deduplicated. A rule that fits the demonstrations
    but abstains on this input contributes nothing — abstention is not a
    hypothesis, and counting it as one would turn a refusal into a wrong answer.
    """
    out = []
    names = []
    for name, fit in lib:
        fn = fit(task["train"])
        if fn is None:
            continue
        g = fn(grid)
        if g is None or g in out:
            continue
        out.append(g)
        names.append(name)
    return names, out


def evaluate(lib, tasks):
    """Replay one library size over tasks that carry ground-truth outputs."""
    stat = dict(total=0, fits=0, answered=0, abstained=0,
                correct1=0, correct2=0, ambiguous=0, ambiguous_wrong=0)
    wrong = []

    for tid, task in tasks.items():
        if not all("output" in t for t in task["test"]):
            continue
        stat["total"] += 1

        if not any(fit(task["train"]) is not None for _, fit in lib):
            continue
        stat["fits"] += 1

        per_test = [hypotheses(lib, task, t["input"]) for t in task["test"]]
        # One test input with no hypothesis means the task falls through to the
        # fallback, and a fallback that happens to be right is luck, not a rule.
        if any(not h for _, h in per_test):
            stat["abstained"] += 1
            continue
        stat["answered"] += 1

        truth = [t["output"] for t in task["test"]]
        hit1 = all(h[0] == y for (_, h), y in zip(per_test, truth))
        hit2 = all(y in h[:2] for (_, h), y in zip(per_test, truth))
        amb = any(len(h) > 1 for _, h in per_test)

        stat["correct1"] += hit1
        stat["correct2"] += hit2
        stat["ambiguous"] += amb
        if amb and not hit1:
            stat["ambiguous_wrong"] += 1
        if not hit2:
            wrong.append((tid, per_test[0][0]))

    return stat, wrong


def pct(n, d):
    return f"{100.0 * n / d:6.2f}%" if d else "     --"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="training", choices=["training", "evaluation"])
    ap.add_argument("--tasks", type=Path)
    a = ap.parse_args(argv)

    tasks = load(a.tasks or (DEFAULT_DATA / a.split))
    tranches = sorted(set(solvers.TRANCHE.values()))

    rows = []
    for k in tranches:
        lib = library(k)
        stat, wrong = evaluate(lib, tasks)
        rows.append((k, len(lib), stat, wrong))

    total = rows[-1][2]["total"]
    print(f"split: {a.split}  ({total} tasks with ground truth)\n")
    print(f"{'tranche':>7} {'rules':>6} {'answered':>9} {'coverage':>9} "
          f"{'prec@1':>8} {'prec@2':>8} {'ambig':>8} {'accuracy':>9}")
    for k, size, s, _ in rows:
        print(f"{k:>7} {size:>6} {s['answered']:>9} {pct(s['answered'], s['total']):>9} "
              f"{pct(s['correct1'], s['answered']):>8} {pct(s['correct2'], s['answered']):>8} "
              f"{pct(s['ambiguous'], s['answered']):>8} {pct(s['correct2'], s['total']):>9}")

    first, last = rows[0][2], rows[-1][2]
    print()
    if last["answered"] == 0:
        print("VERDICT: nothing answered at the largest library. No evidence either way;")
        print("the claim needs a split where at least one rule fits and is willing.")
        return 0

    def prec(s):
        return s["correct1"] / s["answered"] if s["answered"] else None

    p_first, p_last = prec(first), prec(last)
    grew = last["answered"] - first["answered"]

    if p_first is None:
        print(f"VERDICT: tranche 1 answered nothing here, so there is no baseline to")
        print(f"compare against. Largest library: precision@1 {pct(last['correct1'], last['answered']).strip()}"
              f" over {last['answered']} answers.")
    elif p_last >= p_first - 1e-9:
        print(f"VERDICT: claim SURVIVES this split. Answers grew by {grew} "
              f"({first['answered']} -> {last['answered']}) and precision@1 did not fall "
              f"({p_first * 100:.1f}% -> {p_last * 100:.1f}%).")
        print("Coverage is the binding constraint here: every rule added bought accuracy")
        print("without costing precision.")
    else:
        print(f"VERDICT: claim WOUNDED on this split. Answers grew by {grew} but "
              f"precision@1 fell {p_first * 100:.1f}% -> {p_last * 100:.1f}%.")
        print(f"{last['ambiguous_wrong']} of the wrong answers had two or more fitting rules")
        print("disagreeing, which is selection failing, not coverage.")

    _, _, s, wrong = rows[-1]
    if wrong:
        print(f"\nwrong at the largest library ({len(wrong)}), first 10:")
        for tid, names in wrong[:10]:
            print(f"  {tid}  fitted: {', '.join(names) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
