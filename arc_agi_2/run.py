"""Build submission.json for ARC-AGI-2, and score it locally when answers exist.

    python -m arc_agi_2.run --split evaluation      # score against public answers
    python -m arc_agi_2.run --split training
    python -m arc_agi_2.run --tasks <dir> --out submission.json --no-score

On Kaggle point --tasks at the attached competition directory and pass
--no-score; the hidden test outputs are not present there.

Scoring matches the competition: two attempts per test input, and the task
scores 1 if *either* attempt matches the ground truth exactly, else 0.
"""

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python run.py` as well as -m
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arc_agi_2 import solvers  # noqa: E402

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "ARC-AGI-2" / "data"


def load(task_dir: Path) -> dict:
    files = sorted(task_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"no task files in {task_dir}")
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in files}


def validate(submission: dict, tasks: dict) -> list:
    """Structural checks. A malformed file can void the whole submission."""
    problems = []
    for tid, task in tasks.items():
        entry = submission.get(tid)
        if entry is None:
            problems.append(f"{tid}: missing")
            continue
        if len(entry) != len(task["test"]):
            problems.append(
                f"{tid}: {len(entry)} attempts for {len(task['test'])} test inputs"
            )
            continue
        for i, att in enumerate(entry):
            for key in ("attempt_1", "attempt_2"):
                g = att.get(key)
                if not isinstance(g, list) or not g:
                    problems.append(f"{tid}[{i}].{key}: not a non-empty grid")
                    continue
                if not all(isinstance(r, list) and r for r in g):
                    problems.append(f"{tid}[{i}].{key}: rows must be non-empty lists")
                elif len({len(r) for r in g}) != 1:
                    problems.append(f"{tid}[{i}].{key}: ragged rows")
                elif not all(isinstance(v, int) and 0 <= v <= 9 for r in g for v in r):
                    problems.append(f"{tid}[{i}].{key}: values must be ints 0-9")
    return problems


def score(submission: dict, tasks: dict) -> tuple:
    """Competition scoring, on tasks that carry their answers."""
    scored = solved = 0
    hits = []
    for tid, task in tasks.items():
        if not all("output" in t for t in task["test"]):
            continue
        scored += 1
        entry = submission[tid]
        ok = all(
            t["output"] in (a["attempt_1"], a["attempt_2"])
            for t, a in zip(task["test"], entry)
        )
        if ok:
            solved += 1
            hits.append(tid)
    return scored, solved, hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, help="directory of task .json files")
    ap.add_argument("--split", default="evaluation", choices=["training", "evaluation"])
    ap.add_argument("--out", type=Path, default=Path("submission.json"))
    ap.add_argument("--no-score", action="store_true")
    a = ap.parse_args(argv)

    task_dir = a.tasks or (DEFAULT_DATA / a.split)
    if not task_dir.exists():
        raise SystemExit(f"{task_dir} not found — run fetch_data.py first")

    tasks = load(task_dir)
    submission = {tid: solvers.predict(task) for tid, task in tasks.items()}

    problems = validate(submission, tasks)
    if problems:
        print(f"INVALID — {len(problems)} problem(s):")
        for p in problems[:20]:
            print("  " + p)
        return 1

    a.out.write_text(json.dumps(submission), encoding="utf-8")
    kb = a.out.stat().st_size / 1024
    print(f"wrote {a.out} — {len(submission)} tasks, {kb:,.0f} KB, format OK")

    if not a.no_score:
        scored, solved, hits = score(submission, tasks)
        if scored:
            pct = 100.0 * solved / scored
            print(f"local score: {solved}/{scored} = {pct:.2f}%")
            if hits:
                print("solved: " + ", ".join(hits[:10]) + ("..." if len(hits) > 10 else ""))
        else:
            print("no ground truth in this split — nothing to score")
    return 0


if __name__ == "__main__":
    sys.exit(main())
