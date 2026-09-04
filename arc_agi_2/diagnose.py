"""Is it plumbing, or is it coverage?

Two failure modes look identical from a score of zero:

  plumbing  — the solver's own transformation family is implemented wrong, so it
              cannot even reproduce demonstrations it was designed for
  coverage  — the plumbing is exact, but nothing in SOLVERS describes what the
              tasks actually do

They need opposite responses, so never guess between them. The separating
signal is the **false-positive rate**: tasks where a solver reproduced every
training pair, then got the held-out test wrong. A fit that survives all
demonstrations and still fails the test means the rule was underdetermined or
the implementation is subtly wrong. Zero false positives means the transforms
are exact and the problem is that there are too few of them.

    python -m arc_agi_2.diagnose --split training
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arc_agi_2 import solvers  # noqa: E402
from arc_agi_2.run import DEFAULT_DATA, load  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="training", choices=["training", "evaluation"])
    ap.add_argument("--tasks", type=Path)
    a = ap.parse_args(argv)

    task_dir = a.tasks or (DEFAULT_DATA / a.split)
    tasks = load(task_dir)

    fits = Counter()
    n_fit = n_said = n_hit = n_miss = n_abstain = n_lucky = 0
    misses = []

    for tid, task in tasks.items():
        names = solvers.fitted_names(task)
        for n in names:
            fits[n] += 1
        if not all("output" in t for t in task["test"]):
            continue
        pred = solvers.predict(task)
        ok = all(
            t["output"] in (p["attempt_1"], p["attempt_2"])
            for t, p in zip(task["test"], pred)
        )
        if not names:
            # No rule explained the demonstrations, so anything right here came
            # from the fallback landing on it by chance. Counting these as solves
            # would flatter the score with luck.
            n_lucky += ok
            continue
        n_fit += 1
        # Fitting the demonstrations is not the same as being willing to answer:
        # a solver may abstain on this particular input. Only a solver that
        # actually produced a grid can be judged right or wrong.
        spoke = any(
            fn(t["input"]) is not None
            for name, fit in solvers.SOLVERS
            if name in names and (fn := fit(task["train"])) is not None
            for t in task["test"][:1]
        )
        if not spoke:
            n_abstain += 1
            continue
        n_said += 1
        if ok:
            n_hit += 1
        else:
            n_miss += 1
            misses.append((tid, names))

    print(f"split: {a.split}  ({len(tasks)} tasks)\n")
    print("solvers that reproduced every training pair:")
    for name, _ in solvers.SOLVERS:
        print(f"  {name:<12} {fits.get(name, 0):>4}")
    print(f"  {'(no fit)':<12} {len(tasks) - n_fit:>4}\n")

    print(f"tasks with a fitting solver  : {n_fit}")
    print(f"  abstained on the test input: {n_abstain}")
    print(f"  answered                   : {n_said}")
    print(f"    correct                  : {n_hit}")
    print(f"    wrong (FALSE POSITIVE)   : {n_miss}")
    print(f"solved by fallback luck only : {n_lucky}")

    if n_fit == 0:
        print("\nno solver fits anything here — says nothing about plumbing.")
    elif n_said == 0:
        print("\nevery fitting solver abstained — no evidence either way.")
    elif n_miss == 0:
        print("\nVERDICT: plumbing is exact. Every rule that explained the")
        print("demonstrations and was willing to answer got the held-out test")
        print("right. The problem is COVERAGE — too few transformation families,")
        print("not broken ones.")
        if n_lucky:
            print(f"\nNote: {n_lucky} further task(s) scored by fallback luck, not by")
            print("any rule. Real solve count is {}, not {}.".format(n_hit, n_hit + n_lucky))
    else:
        rate = 100.0 * n_miss / n_said
        print(f"\nVERDICT: {rate:.0f}% of answers were wrong. A rule explained every")
        print("demonstration, was willing to answer, and still failed — underdetermined")
        print("rules or a subtle implementation bug. Inspect before adding any solver:")
        for tid, names in misses[:10]:
            print(f"  {tid}  fitted: {', '.join(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
