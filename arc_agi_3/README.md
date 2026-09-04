# ARC-AGI-3 — not started

Secondary track. Scheduled for **Oct 9–26** per `../../contests/CONTESTS.md`; week 1 only needs a
trivial valid submission here, not an agent worth anything.

Different problem from ARC-AGI-2 entirely. Not static grids — interactive game environments,
scoring exploration, world-modeling, goal-setting and planning/execution. A batch predictor does
not transfer; this needs an agent loop.

## Interface

Agent logic goes in a single file, `agent/my_agent.py`, implementing:

```python
class MyAgent:
    def is_done(self, frames, latest_frame) -> bool:
        """When to stop playing."""

    def choose_action(self, frames, latest_frame) -> GameAction:
        """Next action, given what has been seen so far."""
```

Output file is **`submission.parquet`** (not JSON, unlike ARC-AGI-2). Submissions are Kaggle
notebooks; the official starter kit generates the notebook from the agent code and pushes it with
`make submit`.

## Before writing anything here

1. Pull the official starter kit and get its unmodified example agent submitting. A working
   round-trip first, an agent second — same order that worked for ARC-AGI-2.
2. Confirm how `submission.parquet` is produced. Nothing in this repo writes parquet today, and
   the stdlib cannot. Either the starter kit handles it, or this track needs a dependency that
   ARC-AGI-2 deliberately avoids.
3. Check the RTX 6000 quota cost before using it.

## Deadlines

Submissions **2026-11-02**, same as every track. Milestone #2 on 2026-09-30 is ignored on
purpose — top-3 only, and chasing it costs three weeks of the real run.
