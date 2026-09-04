"""Fetch the public ARC-AGI-2 tasks into data/.

The Kaggle runtime has no internet, so this only ever runs locally. On Kaggle the
same JSON arrives as an attached competition dataset instead.
"""

import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/arcprize/ARC-AGI-2.git"
DEST = Path(__file__).parent / "data" / "ARC-AGI-2"


def main() -> int:
    if DEST.exists():
        print(f"already present: {DEST}")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"cloning {REPO} -> {DEST}")
    r = subprocess.run(["git", "clone", "--depth", "1", REPO, str(DEST)])
    if r.returncode:
        return r.returncode
    train = len(list((DEST / "data" / "training").glob("*.json")))
    evl = len(list((DEST / "data" / "evaluation").glob("*.json")))
    print(f"training tasks: {train}\nevaluation tasks: {evl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
