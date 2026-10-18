"""Emit the Kaggle submission notebook from the repo's own source files.

The notebook is **generated, never hand-edited**. Copying code into a notebook by
hand creates two versions of the truth, and the one that gets graded is the one
nobody tested. Here the notebook cells are the verbatim text of

    arc_agi_2/solvers.py
    kaggle/kaggle_runner.py

so what Kaggle runs is byte-identical to what `measure.py` scored. That is not
tidiness: Reproducibility is one of the six ARC-AGI-2 Grand Prize criteria, and
a generated notebook is the cheapest honest way to earn it.

    python kaggle/build_notebook.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "kaggle" / "arc_agi_2_submission.ipynb"

HEADER = """# ARC Prize 2026 — ARC-AGI-2

Deterministic, CPU-only, **Python standard library only**. No model, no
pretraining, no internet, no accelerator.

## What this is

A library of explicit transformation rules. A rule is applied to a task **only if
it reproduces every training demonstration exactly**, and it returns nothing
rather than guess when the rule is underdetermined for a given input.

This entry exists to test one claim:

> For a non-learning solver on ARC-AGI-2 the binding constraint is **hypothesis
> coverage, not hypothesis selection**. Demonstration-consistency is a
> near-perfect selector, so accuracy is bought by adding rules at no precision
> cost.

It is falsified if precision falls as the rule library grows. On the public
training split, growing the library from 6 to 21 rules moved accuracy from 0.80%
to 2.00% with precision@1 flat at 100% and zero ambiguity between fitting rules.

**Expect a low score, and read the writeup for why that is the result rather
than an excuse.** No rule in this library fits any task in the public evaluation
split, which is itself evidence about ARC-AGI-2's design.

## Reproducibility

Source: {repo}

This notebook is generated from that repository by `kaggle/build_notebook.py`;
the code cells below are the verbatim contents of `arc_agi_2/solvers.py` and
`kaggle/kaggle_runner.py`. All code is open source, as prize eligibility
requires.
"""

REPO = "https://github.com/sufian07/arc-prize-2026"

RUN_CELL = '''# Build the submission. Kaggle's own paths, no arguments to get wrong.
rc = build(Path("/kaggle/input"), Path("/kaggle/working/submission.json"))
assert rc == 0, "submission was NOT written — read the log above before submitting"
'''


def cell_source(path: Path, drop_main: bool = False) -> str:
    src = path.read_text(encoding="utf-8")
    if drop_main:
        marker = '\nif __name__ == "__main__":'
        # The notebook has no argv worth parsing, and __name__ is "__main__"
        # inside a cell, so leaving this in would run main() with Kaggle's
        # kernel arguments. The explicit call in the last cell replaces it.
        src = src.split(marker)[0].rstrip() + "\n"
    return src


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(True)}


def main() -> int:
    solvers = ROOT / "arc_agi_2" / "solvers.py"
    runner = ROOT / "kaggle" / "kaggle_runner.py"
    for p in (solvers, runner):
        if not p.exists():
            print(f"missing {p}")
            return 1

    nb = {
        "cells": [
            md(HEADER.format(repo=REPO)),
            md("## `arc_agi_2/solvers.py`\n"),
            code(cell_source(solvers)),
            md("## `kaggle/kaggle_runner.py`\n"),
            code(cell_source(runner, drop_main=True)),
            md("## Run\n"),
            code(RUN_CELL),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} — {len(nb['cells'])} cells, {kb:,.0f} KB")
    if "fill in" in REPO:
        print("NOTE: REPO placeholder is still unset. Set it before submitting —")
        print("      open-sourcing is a prize-eligibility requirement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
