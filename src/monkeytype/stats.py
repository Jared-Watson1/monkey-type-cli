"""Persistent test history stored as JSON Lines in the user's home directory."""

import json
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path.home() / ".monkeytype-cli"
HISTORY_FILE = HISTORY_DIR / "history.jsonl"

RECENT_WINDOW = 10


def record(mode, stats, params=None):
    """Append one completed test to the history file."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "params": params or {},
        "wpm": stats.wpm,
        "raw_wpm": stats.raw_wpm,
        "accuracy": stats.accuracy,
        "consistency": stats.consistency,
        "correct": stats.correct,
        "incorrect": stats.incorrect,
        "extra": stats.extra,
        "missed": stats.missed,
    }
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load():
    if not HISTORY_FILE.exists():
        return []
    entries = []
    for line in HISTORY_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def summary(entries):
    """Compute bests and averages, excluding zen runs from WPM-based figures."""
    scored = [e for e in entries if e["mode"] != "zen"]
    if not scored:
        return None
    recent = scored[-RECENT_WINDOW:]
    return {
        "tests": len(entries),
        "best_wpm": max(e["wpm"] for e in scored),
        "best_accuracy": max(e["accuracy"] for e in scored),
        "avg_wpm": round(sum(e["wpm"] for e in scored) / len(scored), 1),
        "recent_avg_wpm": round(sum(e["wpm"] for e in recent) / len(recent), 1),
        "avg_accuracy": round(sum(e["accuracy"] for e in scored) / len(scored), 1),
        "recent_avg_accuracy": round(sum(e["accuracy"] for e in recent) / len(recent), 1),
    }


def progress(entries):
    """Lifetime WPM/accuracy averages and how the most recent run compares.

    The delta is the latest scored run measured against the lifetime average,
    so a positive value means the run beat your usual pace.
    """
    scored = [e for e in entries if e["mode"] != "zen"]
    if not scored:
        return None
    avg_wpm = round(sum(e["wpm"] for e in scored) / len(scored), 1)
    avg_acc = round(sum(e["accuracy"] for e in scored) / len(scored), 1)
    last = scored[-1]
    return {
        "avg_wpm": avg_wpm,
        "avg_accuracy": avg_acc,
        "last_wpm": last["wpm"],
        "last_accuracy": last["accuracy"],
        "wpm_delta": round(last["wpm"] - avg_wpm, 1),
        "acc_delta": round(last["accuracy"] - avg_acc, 1),
        # No delta arrow makes sense until there is more than one run to compare.
        "has_history": len(scored) > 1,
    }


def wpm_series(entries):
    return [e["wpm"] for e in entries if e["mode"] != "zen"]
