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

*(nothing yet)*
