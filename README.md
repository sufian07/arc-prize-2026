# arc-prize-2026

Entry code for [ARC Prize 2026](https://arcprize.org/competitions/2026) — ARC-AGI-2 (primary),
ARC-AGI-3 (secondary), and the Paper Track.

Status, plan, deadlines and prize structure live in `../contests/CONTESTS.md`. This repo is
only the code.

> **This repo will be public.** Open-sourcing is mandatory for prize eligibility, and required
> *before* private evaluation scores are released. Write every commit as though it is already
> being read, because it will be.

## Where things stand

Week 1 of the plan is a *valid* submission on both code tracks — not a good one. ARC-AGI-2 is
there; ARC-AGI-3 is not started.

| | ARC-AGI-2 | ARC-AGI-3 |
| --- | --- | --- |
| Pipeline runs end to end | yes | no |
| Submission format validated | yes | no |
| Local score | **2.10% training · 0.00% evaluation** | — |

The evaluation zero is the honest baseline and it is the right thing to have on day one. The
pipeline is what week 1 buys: a file the grader will accept, with a number attached that can
only go up.

## The claim this entry is built to test

Decided 2026-09-05. The entry optimises for **one falsifiable claim**, not for score — see
`../contests/CONTESTS.md` for why, and `RESEARCH.md` Q1 for the evidence that the Paper Track
rewards this shape (CompressARC took third in 2025 with 4%, against a 24% winner).

> For a non-learning solver on ARC-AGI-2, the binding constraint is **hypothesis coverage, not
> hypothesis selection**. Demonstration-consistency is a near-perfect selector: a rule that
> explains every demonstration and is willing to answer is almost always right on the held-out
> test. Accuracy is therefore bought linearly by adding rules, at no precision cost.

**It is falsified if precision falls as the library grows** — if more rules means more co-fitting
rules that disagree and the tie-break is wrong more often, selection binds and the claim is dead.
Either outcome is a result, which is the point of stating it this way.

The experiment is a replay: `solvers.TRANCHE` records which batch each rule joined in, so the
library is rebuilt at every size and rescored.

```bash
python -m arc_agi_2.measure --split training
```

**First data point — 2026-09-05, training split (1000 tasks):**

| Tranche | Rules | Answered | Coverage | precision@1 | Ambiguity | Accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | 8 | 0.80% | **100.00%** | 0.00% | 0.80% |
| 2 | 21 | 20 | 2.00% | **100.00%** | 0.00% | 2.00% |

The library grew 3.5x, answers grew 2.5x, and precision did not move off 100%. Not one pair of
fitting rules disagreed on any task. **The claim survives its first test**, and 2.00% lands on the
~2.1% CPU-only heuristic reference point in `RESEARCH.md` Q3 — reached here with no learning at
all, which is a cleaner version of that result than the one it matches.

Two honest caveats, both load-bearing:

- **n = 20.** One hundred percent of twenty is a weak interval. The claim needs a much larger
  answered set before the precision number means anything, and growing it is the work.
- **Evaluation is still 0/120** — no rule fits a single evaluation task, so the split that
  actually pays offers no evidence either way yet. That is itself consistent with ARC-AGI-2 having
  systematically removed search-susceptible tasks, and it is the reason the claim is about
  *whether coverage is purchasable*, not about this library reaching a good score.

## ARC-AGI-2

Stdlib only — no numpy, no dependencies. A grid is a `list[list[int]]` with values 0–9.

```bash
python fetch_data.py                          # clones the public tasks into data/
python -m arc_agi_2.run --split evaluation    # build submission.json + score locally
python -m arc_agi_2.run --split training
python -m arc_agi_2.measure --split training  # the coverage-vs-selection experiment
python -m arc_agi_2.diagnose --split training # plumbing check: any false positives?
```

**Submission format** — `submission.json`, one entry per task, one object per test input:

```json
{"007bbfb7": [{"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]}]}
```

Two attempts per test input; the task scores 1 if **either** matches the ground truth exactly.
`run.py` scores exactly this way, so the local number means what the leaderboard means.

**Structure is checked before anything is written** — missing tasks, wrong attempt counts, ragged
rows, out-of-range values. A malformed file can void an entire submission, and that is a stupid
way to lose two months.

### The solvers

`arc_agi_2/solvers.py` holds **21 deterministic rules in two tranches**. A rule is used on a task
**only if it reproduces every training pair exactly** — the one honest signal available before
scoring, and free to check. A rule that fits but cannot determine an answer for a particular input
returns `None`: abstention is not a hypothesis, and dressing a guess as a rule is what the
precision measurement exists to catch.

- **Tranche 1** — constant, identity, colour_map, transpose, flip_h, flip_v.
- **Tranche 2** (2026-09-05) — rot90/180/270, anti_transpose, mirror_h/v, tile, scale, downscale,
  crop_bbox, strip_border, add_border, pick_most_common, pick_least_common,
  pick_most_common_non_bg.

Fit rates say plainly how far this is from real:

| Rule | Training (1000) | Evaluation (120) |
| --- | --- | --- |
| colour_map | 5 | 0 |
| scale | 3 | 0 |
| transpose · rot180 · mirror_h · mirror_v | 2 each | 0 |
| flip_h · flip_v · rot270 · tile · crop_bbox | 1 each | 0 |
| constant · identity · rot90 · anti_transpose · downscale · strip_border · add_border · pick_×3 | 0 | 0 |
| **nothing fits** | **979** | **120** |

Seven of the fifteen new rules fit nothing at all. That is worth stating rather than quietly
dropping them: a rule that fits nothing costs no precision, which is exactly what a coverage-bound
regime predicts, and deleting them would erase the evidence.

Nothing fits any evaluation task. That gap is the actual problem to work on, and it is not a
tuning problem — it needs a different class of approach.

The module exists to fix the *shape* of a solver: fit against training pairs, predict for a new
input. Anything smarter plugs into `SOLVERS` and the submission pipeline never changes again.

### On Kaggle

No internet during evaluation, so nothing fetches, installs or clones. The submission notebook is
**generated from this repository**, never hand-edited:

```bash
python kaggle/build_notebook.py   # -> kaggle/arc_agi_2_submission.ipynb
python kaggle/test_layouts.py     # prove the runner survives every input layout
```

Its code cells are the verbatim text of `arc_agi_2/solvers.py` and `kaggle/kaggle_runner.py`, so
what Kaggle grades is byte-identical to what `measure.py` scored. Copying code into a notebook by
hand makes two versions of the truth and grades the untested one.

**The layout is the risk, not the score.** A submission covering the wrong set of task ids scores
zero however good the rules are, and the only place that is visible is the notebook log. The 2026
competition directory cannot be inspected from outside a Kaggle session, so `kaggle_runner.py`
discovers the layout rather than assuming it, and prints every decision:

| Layout | Handling |
| --- | --- |
| per-task `<task_id>.json` files | keyed by filename stem |
| consolidated `arc-agi_test_challenges.json` | merged; a `test`-named file wins id collisions |
| `sample_submission.json` present | **its keys are authoritative** — better evidence than any filename convention |
| solutions files, metadata | ignored |

`kaggle/test_layouts.py` builds all three shapes from the public evaluation split with answers
withheld, plus decoy training files, and asserts the three submissions are identical, cover exactly
the graded ids, and predict for no decoy. The notebook is separately checked to run with this repo
off `sys.path` — self-contained, as no-internet requires.

For an ad-hoc run against an attached directory, `run.py` still works:

```bash
python -m arc_agi_2.run --tasks /kaggle/input/<competition-dir> --out submission.json --no-score
```

**Before submitting:** set `REPO` in `kaggle/build_notebook.py` to the public URL and regenerate.
Open-sourcing is required for prize eligibility, and required *before* private scores are released.

## ARC-AGI-3

Not started. Interface notes in `arc_agi_3/README.md`.

## Accelerators

**2026 limits are not published yet** — they are announced at competition launch. Do not plan
against the Kaggle notebook defaults (CPU · T4 ×2 · P100 · RTX 6000 for ARC-AGI-3); those are the
notebook menu, not the competition's stated limit.

For reference, the archived **2025** ARC-AGI-2 contest ran **4× NVIDIA L4 at ~$50 of compute per
submission**, with the Grand Prize threshold near **$2.50/task**. Internet and external-API systems
are excluded during private evaluation either way.

We target CPU-only pure Python. That is a deliberate choice, not only a limitation — **Efficiency
and Reproducibility are two of the six ARC-AGI-2 Grand Prize criteria.**
