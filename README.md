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
| Local score | **0.90% training · 0.00% evaluation** | — |

The zero is the honest baseline, and it is the right thing to have on day one. The pipeline is
what week 1 buys: a file the grader will accept, with a number attached that can only go up.

## ARC-AGI-2

Stdlib only — no numpy, no dependencies. A grid is a `list[list[int]]` with values 0–9.

```bash
python fetch_data.py                          # clones the public tasks into data/
python -m arc_agi_2.run --split evaluation    # build submission.json + score locally
python -m arc_agi_2.run --split training
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

`arc_agi_2/solvers.py` holds six deterministic baselines: constant output, identity, colour
substitution, transpose, horizontal flip, vertical flip. A solver is used on a task **only if it
reproduces every training pair exactly** — the one honest signal available before scoring, and
free to check.

Fit rates say plainly how far this is from real:

| Solver | Training (1000) | Evaluation (120) |
| --- | --- | --- |
| colour_map | 5 | 0 |
| transpose | 2 | 0 |
| flip_h / flip_v | 1 each | 0 |
| nothing fits | 991 | **120** |

Nothing fits any evaluation task. That gap is the actual problem to work on, and it is not a
tuning problem — it needs a different class of approach.

The module exists to fix the *shape* of a solver: fit against training pairs, predict for a new
input. Anything smarter plugs into `SOLVERS` and the submission pipeline never changes again.

### On Kaggle

No internet during evaluation. Point `--tasks` at the attached competition directory and pass
`--no-score`, since hidden test outputs are not present:

```bash
python -m arc_agi_2.run --tasks /kaggle/input/<competition-dir> --out submission.json --no-score
```

## ARC-AGI-3

Not started. Interface notes in `arc_agi_3/README.md`.

## Accelerators

CPU · T4 ×2 (default) · P100 · RTX 6000 (ARC-AGI-3 only, higher quota use). Exact compute limits
are set at competition launch — one of the open rule checks in `../contests/CONTESTS.md`.
