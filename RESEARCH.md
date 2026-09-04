# Research brief

Questions I cannot answer well myself, ranked by leverage. Answers land back here.

Two blind spots drive this list: Kaggle pages render as JavaScript shells to automated fetching,
and my training data stops at **May 2026** — so anything about the current state of ARC solving is
guesswork on my side.

Ordered by what changes the work most. **1 and 2 are worth more than 3–5 combined.**

---

## 1. What past ARC papers actually won on

The Paper Track is the realistic prize here, and its rubric is public but its *standard* is not —
scores are never shared. Past winners are the only calibration available.

**Feed it:** ARC Prize 2025 solution writeups on Kaggle · ARC Prize 2024 winning solutions on
arcprize.org · the ARC Prize technical reports for 2024 and 2025.

**Ask:**

- What did paper-prize winners do *differently* from leaderboard winners? Did high-scoring papers
  come from high-scoring code, or did modest scores win on theory and novelty?
- Concretely, what does a paper that scores well on **Theory** contain? The rubric says "why the
  Submission works, as opposed to merely describing how it works" — what does that look like in a
  paper that won?
- How did winners handle **Universality** — what claims did they make about generalising beyond
  ARC, and how did they support them?
- How long were the winning writeups, and how did they use the media gallery? Ours is capped at
  **1,500 words**, so structure matters more than volume.
- Any writeup that scored well despite a low leaderboard score — and what carried it?

## 2. ARC-AGI-2 state of the art, as of September 2026

My baseline scores **0/120** on the public evaluation set, and no hand-written transform fits a
single eval task. I need to know what the gap actually is before choosing an approach.

**Feed it:** the ARC-AGI-2 paper/design doc · the current ARC-AGI-2 leaderboard · recent papers or
posts on ARC-AGI-2 methods · the ARC Prize blog.

**Ask:**

- What is the **current top score on ARC-AGI-2**, by whom, and by what method? Both the Kaggle
  (no-internet, limited-compute) leaderboard and any unconstrained/frontier-model figure — they
  differ a lot and I want both numbers.
- What **approach families** are on the leaderboard now: test-time training, program synthesis over
  a DSL, LLM-guided search, evolutionary methods, ensembles? Rough ranking by score.
- **Why did ARC-AGI-2 break the ARC-AGI-1 playbook?** What specifically did it change — task
  design, compositionality, grid size, number of rules per task — that made prior solvers collapse?
- What is the **best open-source ARC-AGI-2 solver** available to read right now?
- Is there a published account of what an *honest floor* looks like — what naive baselines score,
  so I know whether 0% is normal or whether I have a bug?

## 3. Test-time training and program synthesis, specifically

The two families I'd bet on. I know them up to early 2026 and need the current picture.

**Ask:**

- Does **test-time training** still work on ARC-AGI-2, or was it an ARC-AGI-1 artifact? What
  scores does it reach now, and at what compute cost?
- What is the state of **DSL-based program synthesis** for ARC — is Hodel's DSL still the reference
  point, and has anything superseded it for ARC-AGI-2?
- Any approach that works *within Kaggle's constraints* (no internet, T4 ×2 or P100, fixed runtime)
  rather than requiring frontier-model API calls? This is the binding constraint and most published
  results ignore it.

## 4. The two open rule questions

These are **copy-paste, not research** — the pages just need to be read by a human, since they
render as empty shells to me. Both are logged in `../contests/CONTESTS.md`.

- The **ARC-AGI-2 competition rules page** — does its Grand Prize ($275K, judged on writeup
  quality) use the *same six criteria* as the Paper Track? The "one document, two prize entries"
  plan rests entirely on this.
- **May two writeups be submitted**, one for ARC-AGI-2 and one for ARC-AGI-3? The Paper Track page
  says one writeup documents one submission, but is silent on entering a second.
- While there: the **actual compute and runtime limits** on the ARC-AGI-2 competition page.

Pasting those pages here as raw text works fine — that is how the Paper Track details got verified.

## 5. ARC-AGI-3 — later, not now

Scheduled Oct 9–26. No point researching it before ARC-AGI-2 is real work.

**When we get there:** what the official starter kit provides, whether it writes
`submission.parquet` itself (the stdlib cannot), what a competent baseline agent scores, and what
the RTX 6000 quota actually costs.

---

## Answers

Paste findings below as they come in, with the source. Anything that changes the plan gets carried
into `../contests/CONTESTS.md`; anything that changes the code gets carried into the code.

### Q1 — what past paper winners won on · answered 2026-09-04

Sources: [ARC Prize 2025 technical report](https://arxiv.org/html/2601.10904v1) ·
[ARC Prize 2024 technical report](https://arxiv.org/html/2412.04604v2)

**The Paper Track is not a disguised leaderboard contest.** In 2025 the top scorers were NVARC
(24.03%), the ARChitects (16.53%) and MindsAI (12.64%); the Paper Awards went to **TRM, SOAR and
CompressARC** — three different systems. 2024 repeated the pattern: high score was the ARChitects
at 53.5%, while the papers went to induction/transduction, test-time training, and latent-program
search. Leaderboard strength buys credibility. It is neither necessary nor sufficient.

| Paper | ARC performance | Why it mattered |
| --- | --- | --- |
| **TRM** — 1st | 45% AGI-1 · **8% AGI-2** | Recursive refinement in a **7M-parameter** network produces competitive reasoning |
| **SOAR** — 2nd | up to +52% on an open AGI-1 solver | Search traces improve the generator — no hand-built DSL, no solution corpus |
| **CompressARC** — 3rd | 20–34% AGI-1 · **4% AGI-2** | Per-puzzle description-length minimisation generalises with no pretraining and no search |

**CompressARC settles the "can a modest score win" question: yes.** 4% on ARC-AGI-2 against a 24%
winner, and it still placed third — because it isolated a clean phenomenon (a tiny randomly
initialised model, optimised for one puzzle, still finds useful abstractions). What carried it was
not a better pipeline. It was a falsifiable explanation, tested.

**Calibration for our 0%:** the whole field is in single-to-low-double digits on ARC-AGI-2. Paper
winners scored 8% and 4%. Our 0/120 is a weak baseline, not a broken one.

**What scores on Theory** — one sharp explanatory claim, plus belief earned:

1. **Mechanism** — name the proposed *cause*, not the components.
2. **Minimal intervention** — strip confounds (huge pretrained models, hidden data, ensembles) so
   the mechanism is visible. TRM's 7M params and CompressARC's no-pretraining are the exemplars.
3. **Ablations that could have falsified it** — remove the recursion, the MDL objective, the
   verifier feedback; show which removal breaks which capability.
4. **Boundary conditions** — where it fails, how cost scales, whether it survives AGI-1 → AGI-2.
   CompressARC's collapse from 20–34% to 4% was *reported*, not hidden; it defines the limit.
5. **Connection to a broader principle** — 2025's unifying theme was the **refinement loop**:
   repeatedly improve a candidate using feedback, whether it lives in weights, Python, or language.

*How* is a recipe. *Why* is a causal claim plus an experiment that could have proven it wrong.

The 2025 report also notes the performance frontier was driven by refinement loops while the
**efficiency gap still needs new scientific ideas** — that gap is where a small entry can say
something real.

### Q2 — ARC-AGI-2 state of the art · answered 2026-09-04

Sources: [ARC Prize 2025 technical report](https://arxiv.org/html/2601.10904v1) ·
[official leaderboard](https://arcprize.org/leaderboard)

**Two regimes, and they are not comparable.**

| Regime | Best | Cost |
| --- | --- | --- |
| Constrained Kaggle (our regime) | **NVARC 24.03%** · ARChitects 16.53% · MindsAI 12.64% | ~$0.20/task |
| Unconstrained | Gemini 3 Pro alone **31%**; Poetiq refinement harness **54%** | ~$31/task |

Treat third-party "90%+" claims as unverified without tracing the evaluation protocol — the
official leaderboard separates base models, reasoning systems, refinement harnesses and
constrained Kaggle systems, and flags some results as provisional.

**Every winning family is a per-task refinement loop:** generate a candidate, test it against the
demonstrations, use the mismatch as feedback, revise.

- *Test-time training in weight space* — NVARC (2024 ARChitects idea + synthetic data), ARChitects
  (spatially oriented masked-diffusion with recursive self-refinement), MindsAI (test-time
  fine-tuning + augmentation ensembles)
- *Program synthesis and search* — generate candidate programs, verify against **all**
  demonstrations, mutate or refine
- *LLM + verifier harness* — strong but far more expensive
- *Small recursive / per-puzzle models* — TRM 8%, CompressARC 4%

**Why ARC-AGI-2 broke the ARC-AGI-1 playbook.** Same grid format, but difficulty is *normalised* —
the easy wins that carried brittle solvers are gone. The AGI-1 playbook leant on a fixed library of
transformations, a static DSL, or one-pass pattern matching. AGI-2 more often demands
**composition**: identify objects and relations, propose a rule, apply it, and reject it if even
one demonstration cell disagrees. The report's central conclusion is that leading systems need
**iterative refinement rather than a static solver**.

> This is a direct hit on the current design. `solvers.py` is exactly the static library the
> playbook says fails — a fixed list, one pass, no refinement, no object representation.

**Is 0/120 normal?** No canonical naive-baseline table is published, deliberately — public
baselines invite overfitting, and official SOTA is measured only on non-public subsets. But 0/120
is plausible for a narrow one-shot baseline and is *not* evidence of a bug on its own, given paper
winners scored 4% and 8%.

### Q2 follow-up — plumbing verified locally, 2026-09-04

Ran the suggested check (`arc_agi_2/diagnose.py`), which separates *fitted the demonstrations*,
*was willing to answer*, and *was right*:

```
tasks with a fitting solver  : 9
  abstained on the test input: 1
  answered                   : 8
    correct                  : 8
    wrong (FALSE POSITIVE)   : 0
solved by fallback luck only : 1
```

**Verdict: plumbing is exact, coverage is the problem.** Every rule that explained the
demonstrations and was willing to answer got the held-out test right. Zero false positives.

Two things the check surfaced that the raw score hid:

1. **`aabf363d` was a confidently wrong answer.** `colour_map` fit all demonstrations, then met
   colour 8 at test time — absent from every training input — and passed it through unchanged,
   getting 16 of 49 cells wrong. Fixed: the solver now **abstains** when an input contains a colour
   with no learned image. Same discipline as rejecting a rule that misses one demonstration cell.
2. **`e872b94a` was luck, not a solve.** No rule fit; the constant-fill fallback happened to match.

So the honest training number is **8 real solves out of 1000**, not 9. Evaluation stays 0/120.

**Correction to the brief:** ARC-AGI-2 has **1,000 public training tasks** (combining ARC-AGI-1
tasks with new ones) and 120 public evaluation — not 400. Straight from the repo readme. Average
human performance on the public evaluation set was **66%**.

The readme also carries a methodological warning worth honouring in the paper: do not repeatedly
modify an algorithm using the evaluation score as feedback. That is evaluation-set leakage, and
with only 120 public eval tasks it is easy to do by accident.

### Q4 — the rule questions · answered 2026-09-04

Source: [ARC-AGI-2 competition page](https://arcprize.org/competitions/2026/arc-agi-2) ·
[2025 archive](https://arcprize.org/competitions/2025/archive)

**The two rubrics are NOT the same. The "one document, two prize entries" assumption was wrong.**

| ARC-AGI-2 Grand Prize ($275K) | Paper Track ($450K) |
| --- | --- |
| **Novelty** | **Novelty** |
| **Theory** | **Theory** |
| Effectiveness | Accuracy |
| Efficiency | Universality |
| Reproducibility | Progress |
| Clarity | Completeness |

Two of six overlap. Both average six 0–5 criteria. One technical report can still feed both, but
it needs different framing per submission — and critically, the **AGI-2 Grand Prize requires an
actual eligible Kaggle system with measured results**. A theory-first document with no working
submission cannot win it. The Paper Track is more forgiving there; the Grand Prize is not.

**Efficiency is its own criterion on the AGI-2 Grand Prize.** That is a strategic opening, not a
footnote — see the note in `../contests/CONTESTS.md`.

**Compute.** 2025 (archived) ran **4× NVIDIA L4, ~$50 of compute per submission**, with the Grand
Prize threshold at roughly **$2.50/task** at 85%+ private accuracy. Internet/API systems (GPT, o3,
Claude) are excluded during private evaluation. **2026 limits are announced at launch and are not
yet published** — do not assume the 2025 L4×4 allocation carries over, and do not treat the Kaggle
notebook default (T4 ×2) as the official 2026 competition limit. Treat T4 as *our* deployment
target, not a published constraint.

Scoring confirmed: exactly two output grids per test input, task scores 1 if either matches
exactly, final score is the mean across task test outputs. Target is **85% on the private set**.

### Unsolicited — "Why all ARC solvers fail today" · read 2026-09-04

Source: [mvakde.github.io](https://mvakde.github.io/blog/why-all-ARC-solvers-fail-today/) —
**a personal blog, self-reported numbers, not peer-reviewed or leaderboard-verified.** Weigh
accordingly; the argument is worth more than the scores.

**Claim:** *"Every solver today fails because it leaves some data uncompressed."* All current
approaches violate Minimum Description Length by failing to jointly compress three sources:

1. **Example input grids.** Solvers find `P` with `P(input) = output`, which compresses only the
   outputs and leaves inputs listed verbatim. Proposed instead: find `F` with `F(k) = (I_k, O_k)`,
   compressing both — because *"inputs and outputs share common structures: same kinds of red
   squares, same object layouts, same background patterns."*
2. **Private/test puzzles.** Almost all concepts in the eval puzzles already appear in the training
   puzzles, so MDL demands compressing all puzzles together — which makes test-time training
   *"100% necessary"* on the author's reading.
3. **Test input grids.** These carry distribution shifts (e.g. 90° rotations), so a solver must
   train on data sampling both distributions.

Notes CompressARC as *"the only approach today that compresses the test inputs"*. Appendix
taxonomies 15+ approaches by which source each leaves uncompressed, and treats hand-built
augmentations, DSLs and bespoke architectures as **human intervention** to be designed out.

Self-reported: **27.5% at "an unbelievable cost of $2"**, with a prediction of 50% within two
weeks. Unverified — that would beat NVARC's 24.03%, and the two-week prediction is the kind of
claim to hold loosely until it appears on a leaderboard.

**What this means for us — two things, pulling opposite ways.**

*Against the plan:* if test-time training really is necessary, a CPU-only pure-Python entry has a
hard ceiling. That is a direct challenge and should not be waved off.

*For the plan:* the author's own justification for joint compression is that **inputs and outputs
share object structure** — "same kinds of red squares, same object layouts". That is the
object-centric claim wearing compression clothes. It also stakes the compression framing publicly,
which lowers the novelty available there while leaving the *representation vs search budget*
question — ours — untouched and cheaper to test.

Also worth noting: the post treats hand-built DSLs as the thing to eliminate. Our claim does not
defend a DSL; it asks what the loop should propose *over*. Compatible, and testable without a GPU.

### Architecture detail · 2026-09-04

**Score collapse is the benchmark, not the field getting worse.** Private-leaderboard scores fell
from **40–55% (2024, ARC-AGI-1)** to **6–24% (2025, ARC-AGI-2)**.

**How ARC-AGI-2 was built to break the old playbook** — three deliberate changes:

1. **Systematically removed tasks susceptible to brute-force program search.**
2. Hand-tested human calibration of every task.
3. Added compositional generalization — *symbolic interpretation* and *context-conditioned rules*.

> Point 1 is aimed squarely at the cheapest approach available to us. Search over a transform
> space is not merely weak on ARC-AGI-2; the benchmark was *designed* to exclude what it can reach.
> This is the single most important finding for our plan. See the reassessment in
> `../contests/CONTESTS.md`.

**2024 winners (ARC-AGI-1)**

| | Score | How |
| --- | --- | --- |
| ARChitects | 53.5% | NeMo-Minitron-8B + rule-based augmentation; selection by **stability of a solution under augmentation** |
| Barbadillo (Omni-ARC) | 40.0% | Qwen2.5-**0.5B** multi-task fine-tune, then single-task TTT at runtime |
| MindsAI | 55.5% raw | Highest score but **declined to open-source → ineligible** |

2024's other lesson: **induction** (LLM writes Python programs) and **transduction** (LLM predicts
output pixels directly) solve *complementary* task subsets, so ensembling the two paid.

**2025 winners (ARC-AGI-2)**

| | Score | How |
| --- | --- | --- |
| NVARC | 24.03% | Built on ARChitects' TTT. Moved heavy reasoning **offline**: 103k synthetic puzzles + 3.2M augmented, training a compact **4B Qwen**; runtime TTT at **$0.20/task** |
| ARChitects | 16.53% | Threw out autoregression entirely. 2D-aware **masked diffusion** (LLaDA-8B), "Golden Gate RoPE" 2D positional encoding, latent soft-masking loop: guess → soft-mask → refine |
| MindsAI | 12.64% | TTT + tokenizer dropout + augmentation ensembles |

**Paper winners — scale is not the point**

- **TRM** (1st, 8% AGI-2 / 45% AGI-1) — **7M parameters**. A single 2-layer network recursing over
  its own state, refining answer and latent reasoning across *temporal* passes rather than physical
  layers.
- **CompressARC** (3rd, 20% AGI-1 / 4% AGI-2) — **76,000 parameters, zero pretraining,
  inference-only.** Minimises Minimum Description Length per task by overfitting a tiny equivariant
  network to the observed grids. **Converts combinatorial program search into differentiable
  gradient descent.**

> **CompressARC is the existence proof nearest our constraints.** 76k parameters and no pretraining
> is plausibly CPU-feasible. It needs autodiff, so not stdlib — but it is a non-zero ARC-AGI-2
> result that requires neither a frontier model nor a large-model TTT pipeline.

**Unverified claim to treat with suspicion:** third-party sites (BenchLM.ai) report **"GPT-6 Astra
leads at 95%"** on ARC-AGI-2 as of September 2026. This is exactly the ">90% third-party claim"
the earlier research warned not to accept without tracing the evaluation protocol — different
regime, possibly semi-private rather than private, possibly unconstrained cost. Not usable as a
reference point without the protocol.

Other lines worth reading later: code-evolution (Imbue), REPL agents (Symbolica), agentic coding
harnesses (pivotools). All LLM-driven, so all outside our compute regime.

### Q3 — can a CPU-only loop clear zero? · answered 2026-09-04

**Yes, but nothing verified.** No leaderboard-confirmed ARC-AGI-2 submission is both strictly
CPU-only and above 0% — every Kaggle top score and most open-source solvers use a GPU at inference
for TTT, neural synthesis, or LLM sampling.

| Result | AGI-2 | Regime | Verified? |
| --- | --- | --- | --- |
| Heuristic-only pattern matchers (SOAR-based repo README) | **~2.1%** | **pure CPU, no neural model** | self-reported, public subset |
| CompressARC | 4% | single RTX 4070, **~20 min/puzzle**, no pretraining | published report, not Kaggle-private |
| TRM | 8% | 7M params, GPU at test time | research report, not Kaggle-private |
| NVARC | 24.03% | 4B model + synthetic data + runtime TTT, $0.20/task | **Kaggle private-set verified** |

**The ~2.1% heuristic figure is the reference point that matters here.** It is unverified and on a
public subset, but it establishes that zero is beatable on CPU with no learning at all. Our 0/120
is therefore a **coverage gap, not a ceiling**.

**"Test-time training is 100% necessary" is refuted as an absolute.** Heuristics with no learning
can clear zero. The defensible version: *some* per-task refinement appears necessary for
double digits, but fine-tuning a large pretrained model is not required — tiny from-scratch
per-puzzle optimisers also clear zero.

**CompressARC-on-CPU is not viable as a submission.** ~20 min/puzzle on an RTX 4070 implies hours
per puzzle on CPU; across 120 evaluation tasks that exceeds any Kaggle notebook runtime. Attractive
as a *question*, dead as a strategy.

**Guidance received:** a CPU-only system can plausibly reach low single digits with a strong
heuristic library plus a small search verifying candidates against all demonstrations, but is
unlikely to approach 10–20% without per-task optimisation.

### Q5 — open

ARC-AGI-3 starter kit, deferred to October.

Still needed: whether test-time training survives on AGI-2 and at what compute, the state of
DSL-based synthesis, and the ARC-AGI-3 starter kit questions in section 5.

Guidance received on method selection: both test-time training and DSL synthesis fit the
constraints, since both run in-notebook, validate against demonstrations, and need no external
API. The deciding test is not which looks cleverer but **whether either can solve a known public
task deterministically inside the notebook's time and memory budget** before it ever sees an
evaluation task.
