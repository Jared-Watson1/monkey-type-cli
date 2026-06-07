"""Command-line entry point and the live typing loop."""

import argparse
import time

from rich.live import Live

from . import content as content_mod
from . import engine as engine_mod
from . import input as keys
from . import menu
from . import render
from . import results
from . import stats
from .results import console

# Time mode needs more text than a fast typist can exhaust before the clock ends.
TIME_CHARS_PER_SECOND = 15


def _build_target(cfg, content):
    mode = cfg["mode"]
    if mode == "zen":
        return []
    if mode == "time":
        return content.stream(cfg["duration"] * TIME_CHARS_PER_SECOND)
    words, _ = content.random_quote(cfg.get("length"))
    return words


def _run_loop(engine):
    """Drive the live view until the test ends. Returns (outcome, final_time).

    Outcome is "done" (completed/finished), "restart" (tab), or "abort" (quit).
    """
    with keys.raw_mode(), Live(console=console, screen=True, auto_refresh=False) as live:
        while not engine.done:
            now = time.monotonic()
            remaining = 0.0
            if engine.mode == "time":
                if engine.start_time is None:
                    remaining = engine.duration
                else:
                    remaining = engine.duration - engine.elapsed(now)
                    if remaining <= 0:
                        break

            width, height = console.size
            live.update(render.typing_view(engine, remaining, width, height), refresh=True)

            key = keys.read_key(timeout=0.1)
            if key is None:
                continue
            if key == keys.CTRL_C:
                return "abort", now
            if key == keys.TAB:
                return "restart", now
            if key == keys.ESC:
                if engine.mode == "zen":
                    break
                return "abort", now
            engine.press(key, time.monotonic())

    final = time.monotonic()
    if engine.mode == "time" and engine.start_time is not None:
        final = engine.start_time + engine.duration
    return "done", final


def _play(cfg, content):
    """Run tests for one config until the user leaves. Returns the next action."""
    while True:
        target = _build_target(cfg, content)
        engine = engine_mod.Engine(target, mode=cfg["mode"], duration=cfg.get("duration"))
        outcome, final = _run_loop(engine)

        if outcome == "restart":
            continue
        if outcome == "abort" or engine.start_time is None:
            return "quit"

        result = engine.stats(now=final)
        params = {k: cfg[k] for k in ("length", "duration") if cfg.get(k)}
        stats.record(cfg["mode"], result, params)
        results.show_result(result)
        return results.post_test_prompt()


def _config_from_args(args):
    if args.zen:
        return {"mode": "zen"}
    if args.time:
        return {"mode": "time", "duration": args.time}
    if args.quote:
        length = None if args.quote == "any" else args.quote
        return {"mode": "words", "length": length}
    return None


def main():
    parser = argparse.ArgumentParser(prog="monkeytype", description="A terminal typing test.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stats", help="Show your typing history.")
    parser.add_argument(
        "--quote",
        nargs="?",
        const="any",
        choices=["short", "medium", "long", "any"],
        help="Type a quote, optionally of the given length.",
    )
    parser.add_argument("--time", type=int, choices=[15, 30, 60, 120], help="Timed test for N seconds.")
    parser.add_argument("--zen", action="store_true", help="Free typing until ESC.")
    parser.add_argument("--no-punctuation", action="store_true", help="Strip punctuation and capitals.")
    parser.add_argument("--seed", type=int, help="Seed text selection for repeatable tests.")
    args = parser.parse_args()

    if args.command == "stats":
        results.show_stats()
        return

    def _normalize(cfg):
        cfg.setdefault("length", None)
        cfg["punctuation"] = not args.no_punctuation
        cfg["seed"] = args.seed
        return cfg

    choice = _config_from_args(args) or menu.run()
    while choice:
        if choice == "stats":
            results.show_stats()
            results.wait_for_key("press any key to return to the menu")
            choice = menu.run()
            continue

        cfg = _normalize(choice)
        content = content_mod.Content(punctuation=cfg["punctuation"], seed=cfg["seed"])
        action = _play(cfg, content)
        if action == "menu":
            choice = menu.run()
        elif action == "again":
            choice = cfg
        else:
            choice = None
