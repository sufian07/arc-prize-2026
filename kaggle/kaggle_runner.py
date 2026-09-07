"""The Kaggle side of an ARC-AGI-2 submission: find the tasks, answer, write the file.

Runs with **no internet**, so nothing here fetches, installs or clones. It is
stdlib only for the same reason the solvers are.

The hard part is not prediction, it is not guessing wrong about the input
layout. A submission that predicts for the wrong set of task ids scores zero no
matter how good the rules are, and the competition directory is not visible from
here — the 2026 layout is only observable from inside a Kaggle session. So this
discovers the layout rather than assuming it, and handles every shape ARC Prize
has shipped:

  per-task files       one <task_id>.json per task, as the public repo ships
  consolidated files   arc-agi_test_challenges.json, a dict of task_id -> task
  a sample submission  sample_submission.json, whose keys are authoritative

**`sample_submission.json` wins when present.** It states exactly which task ids
the grader expects and how many attempt slots each needs, which is better
evidence than any filename convention. Everything else is a fallback for when it
is absent.

Every discovery decision is printed. A submission that fails at 3am on the
deadline is diagnosed from the notebook log or not at all.

Local test against the public evaluation set:

    python kaggle/kaggle_runner.py --input data/ARC-AGI-2/data/evaluation --out /tmp/s.json
"""

import argparse
import json
import sys
from pathlib import Path

try:  # running from the repo: make the repo root importable, as run.py does
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
except NameError:  # pragma: no cover - no __file__ inside a notebook cell
    pass

try:  # locally this resolves; inside the notebook the cell above defined it
    from arc_agi_2.solvers import predict
except ImportError:  # pragma: no cover - notebook path
    predict = globals()["predict"]


# ---------------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------------

def _is_task(o) -> bool:
    return isinstance(o, dict) and "train" in o and "test" in o


def _is_sample_submission(o) -> bool:
    if not isinstance(o, dict) or not o:
        return False
    for v in o.values():
        if not isinstance(v, list) or not v:
            return False
        if not all(isinstance(a, dict) and "attempt_1" in a for a in v):
            return False
    return True


def discover(root: Path) -> tuple:
    """Return (ids, tasks, sample) for whatever layout `root` turns out to hold."""
    pool: dict = {}
    consolidated: dict = {}
    sample = None
    sample_path = None

    files = sorted(p for p in root.rglob("*.json"))
    print(f"scanning {root}: {len(files)} json file(s)")

    for p in files:
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {p.name}: unreadable ({type(e).__name__})")
            continue
        if _is_task(o):
            pool[p.stem] = o
        elif _is_sample_submission(o):
            sample, sample_path = o, p
            print(f"  {p.name}: sample submission, {len(o)} task ids")
        elif isinstance(o, dict) and o and all(_is_task(v) for v in o.values()):
            consolidated[p] = o
            print(f"  {p.name}: {len(o)} tasks")
        # anything else (solutions files, metadata) is deliberately ignored

    per_file = len(pool)
    if per_file:
        print(f"  {per_file} per-task file(s)")

    # Consolidated files merge into the pool. Sorted so a "test"-named file is
    # applied last and wins any id collision, which is the set being graded.
    for p in sorted(consolidated, key=lambda q: "test" in q.name.lower()):
        pool.update(consolidated[p])

    if sample is not None:
        ids = list(sample)
        print(f"required ids: {len(ids)}, from {sample_path.name}")
    else:
        test_files = [p for p in consolidated if "test" in p.name.lower()]
        if test_files:
            pick = sorted(test_files, key=lambda q: len(q.name))[0]
            ids = list(consolidated[pick])
            print(f"no sample submission; using {pick.name} ({len(ids)} ids)")
        else:
            ids = sorted(pool)
            print(f"no sample submission and no test file; using all {len(ids)} tasks")

    return ids, pool, sample


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def validate(submission: dict, ids: list, tasks: dict, sample) -> list:
    """Structural checks. A malformed file can void the whole submission."""
    problems = []
    for tid in ids:
        entry = submission.get(tid)
        if entry is None:
            problems.append(f"{tid}: missing")
            continue
        want = len(tasks[tid]["test"]) if tid in tasks else None
        if sample is not None and len(sample.get(tid, [])) != len(entry):
            problems.append(
                f"{tid}: {len(entry)} attempt block(s), sample wants {len(sample[tid])}"
            )
        elif want is not None and len(entry) != want:
            problems.append(f"{tid}: {len(entry)} attempt block(s) for {want} test input(s)")
        for i, att in enumerate(entry):
            for key in ("attempt_1", "attempt_2"):
                g = att.get(key)
                if not isinstance(g, list) or not g:
                    problems.append(f"{tid}[{i}].{key}: not a non-empty grid")
                elif not all(isinstance(r, list) and r for r in g):
                    problems.append(f"{tid}[{i}].{key}: rows must be non-empty lists")
                elif len({len(r) for r in g}) != 1:
                    problems.append(f"{tid}[{i}].{key}: ragged rows")
                elif not all(isinstance(v, int) and 0 <= v <= 9 for r in g for v in r):
                    problems.append(f"{tid}[{i}].{key}: values must be ints 0-9")
    extra = set(submission) - set(ids)
    if extra:
        problems.append(f"{len(extra)} unrequested id(s): {sorted(extra)[:5]}")
    return problems


# ---------------------------------------------------------------------------

def build(root: Path, out: Path) -> int:
    ids, tasks, sample = discover(root)

    missing = [t for t in ids if t not in tasks]
    if missing:
        print(f"\nFATAL: {len(missing)} required id(s) have no task data: {missing[:5]}")
        return 1
    if not ids:
        print("\nFATAL: no tasks discovered. Check the attached competition data.")
        return 1

    submission = {tid: predict(tasks[tid]) for tid in ids}

    problems = validate(submission, ids, tasks, sample)
    if problems:
        print(f"\nINVALID — {len(problems)} problem(s), nothing written:")
        for p in problems[:20]:
            print("  " + p)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(submission), encoding="utf-8")
    kb = out.stat().st_size / 1024

    # How many answers came from a rule rather than the fallback. It does not
    # change the file, but a run that answers nothing by rule should say so
    # rather than look identical to one that did.
    try:
        from arc_agi_2.solvers import fitted_names
    except ImportError:  # pragma: no cover - notebook path
        fitted_names = globals().get("fitted_names")
    if fitted_names:
        n = sum(1 for tid in ids if fitted_names(tasks[tid]))
        print(f"\nrules fit {n}/{len(ids)} task(s); the rest are the fallback")

    print(f"wrote {out} — {len(submission)} tasks, {kb:,.0f} KB, format OK")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/kaggle/input"))
    ap.add_argument("--out", type=Path, default=Path("/kaggle/working/submission.json"))
    a = ap.parse_args(argv)
    if not a.input.exists():
        print(f"FATAL: {a.input} does not exist")
        return 1
    return build(a.input, a.out)


if __name__ == "__main__":
    sys.exit(main())
