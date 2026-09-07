"""Prove the runner survives every input layout ARC Prize has shipped.

The competition directory is not visible from outside a Kaggle session, so the
2026 layout is a genuine unknown until submission day. This is the guard on the
failure that costs the most and shows the least: predicting for the wrong set of
task ids scores zero however good the rules are, and the notebook log is the only
place it would ever be visible.

Three layouts, built from the public evaluation split with answers withheld:

  A  per-task <task_id>.json files, as the public repo ships
  B  consolidated challenges + sample_submission + decoy training files
  C  consolidated challenges, no sample_submission

All three must produce the *same* submission, covering *exactly* the graded ids,
with nothing predicted for the decoy split.

    python kaggle/test_layouts.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ARC-AGI-2" / "data"
N_TEST = 40
N_DECOY = 15


def load_dir(d: Path) -> dict:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}


def run(inp: Path, out: Path) -> int:
    r = subprocess.run(
        [sys.executable, str(ROOT / "kaggle" / "kaggle_runner.py"),
         "--input", str(inp), "--out", str(out)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    print(r.stdout.rstrip())
    if r.returncode != 0 and r.stderr.strip():
        print("STDERR:", r.stderr.strip()[:800])
    return r.returncode


def main() -> int:
    if not (DATA / "evaluation").exists():
        print(f"{DATA/'evaluation'} not found — run fetch_data.py first")
        return 1

    ev, tr = load_dir(DATA / "evaluation"), load_dir(DATA / "training")
    test_ids, decoy_ids = sorted(ev)[:N_TEST], sorted(tr)[:N_DECOY]
    print(f"{len(ev)} evaluation tasks; {len(test_ids)} stand in for the hidden test set")

    # Answers stripped, the way a hidden test set actually arrives.
    hidden = {t: {"train": ev[t]["train"],
                  "test": [{"input": x["input"]} for x in ev[t]["test"]]}
              for t in test_ids}

    tmp = Path(tempfile.mkdtemp(prefix="arc_layouts_"))
    try:
        outs, codes = {}, {}

        a = tmp / "a" / "arc-prize-2026"
        a.mkdir(parents=True)
        for t in test_ids:
            (a / f"{t}.json").write_text(json.dumps(ev[t]), encoding="utf-8")

        b = tmp / "b" / "arc-prize-2026"
        b.mkdir(parents=True)
        (b / "arc-agi_test_challenges.json").write_text(json.dumps(hidden), encoding="utf-8")
        (b / "arc-agi_training_challenges.json").write_text(
            json.dumps({t: tr[t] for t in decoy_ids}), encoding="utf-8")
        (b / "arc-agi_training_solutions.json").write_text(
            json.dumps({t: [x["output"] for x in tr[t]["test"]] for t in decoy_ids}),
            encoding="utf-8")
        (b / "sample_submission.json").write_text(json.dumps(
            {t: [{"attempt_1": [[0]], "attempt_2": [[0]]} for _ in hidden[t]["test"]]
             for t in test_ids}), encoding="utf-8")

        c = tmp / "c" / "arc-prize-2026"
        c.mkdir(parents=True)
        (c / "arc-agi_test_challenges.json").write_text(json.dumps(hidden), encoding="utf-8")
        (c / "arc-agi_training_challenges.json").write_text(
            json.dumps({t: tr[t] for t in decoy_ids}), encoding="utf-8")

        for name, label in (("a", "per-task .json files"),
                            ("b", "consolidated + sample_submission + decoys"),
                            ("c", "consolidated test file, no sample_submission")):
            print("\n" + "=" * 70 + f"\nLAYOUT {name.upper()}: {label}\n" + "=" * 70)
            out = tmp / f"out_{name}.json"
            codes[name] = run(tmp / name, out)
            outs[name] = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None

        print("\n" + "=" * 70 + "\nCHECKS\n" + "=" * 70)
        ok = True
        for name in "abc":
            rc, s = codes[name], outs[name]
            ok &= rc == 0
            print(f"  layout {name}: exit {rc}", "OK" if rc == 0 else "FAIL")
            if s is None:
                print("    no submission written"); ok = False; continue
            exact = sorted(s) == test_ids
            print(f"    {len(s)} ids, exactly the graded set: {exact}")
            ok &= exact
            leaked = set(s) & set(decoy_ids)
            if leaked:
                print(f"    LEAK: predicted for {len(leaked)} decoy id(s)"); ok = False

        if all(outs[n] is not None for n in "abc"):
            identical = outs["a"] == outs["b"] == outs["c"]
            print(f"  all three layouts identical: {identical}")
            ok &= identical
            solved = sum(1 for t in test_ids
                         if all(x["output"] in (p["attempt_1"], p["attempt_2"])
                                for x, p in zip(ev[t]["test"], outs["b"][t])))
            # Zero is the expected number today and it is not what this test
            # checks. It is printed so a change in it is never silent.
            print(f"  score on the {len(test_ids)} withheld tasks: {solved}/{len(test_ids)}")

        print("\nRESULT:", "ALL LAYOUTS PASS" if ok else "FAILURES ABOVE")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
