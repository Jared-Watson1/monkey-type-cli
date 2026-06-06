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
    }


def wpm_series(entries):
    return [e["wpm"] for e in entries if e["mode"] != "zen"]
