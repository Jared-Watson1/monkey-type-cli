"""End-of-test results screen and the persistent stats view."""

import plotext as plt
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import input as keys
from . import stats as history
from . import theme

console = Console()


def wait_for_key(message="press any key to return"):
    console.print()
    console.print(Text(message, style=theme.SUBTLE, justify="center"))
    with keys.raw_mode():
        keys.read_key(timeout=None)


def post_test_prompt():
    """Show replay options and return the chosen action."""
    hint = Text(justify="center")
    hint.append("↵ play again", style=theme.ACCENT)
    hint.append("   ·   m menu   ·   q quit", style=theme.SUBTLE)
    console.print()
    console.print(hint)
    with keys.raw_mode():
        while True:
            key = keys.read_key(timeout=None)
            if key in (keys.ENTER, keys.SPACE):
                return "again"
            if key == "m":
                return "menu"
            if key in ("q", keys.ESC, keys.CTRL_C):
                return "quit"


def _graph(values, title, height=12):
    if len(values) < 2:
        return None
    plt.clear_figure()
    plt.theme("clear")
    plt.plot(list(range(len(values))), values, marker="braille")
    plt.title(title)
    plt.plotsize(min(console.width, 80), height)
    plt.xfrequency(0)
    return plt.build()


def _stat_table(stats):
    table = Table.grid(padding=(0, 3))
    table.add_column(justify="right", style=theme.SUBTLE)
    table.add_column(style=theme.CORRECT)
    table.add_row("raw", f"{stats.raw_wpm} wpm")
    table.add_row("consistency", f"{stats.consistency}%")
    table.add_row(
        "chars",
        f"{stats.correct}/{stats.incorrect}/{stats.extra}/{stats.missed}",
    )
    return table


def show_result(stats):
    headline = Text()
    headline.append(f"{stats.wpm}", style=theme.HEADER)
    headline.append(" wpm    ", style=theme.ACCENT)
    headline.append(f"{stats.accuracy}%", style=theme.HEADER)
    headline.append(" acc", style=theme.ACCENT)

    console.print()
    console.print(Panel(Group(headline, Text(), _stat_table(stats)),
                        border_style=theme.ACCENT, padding=(1, 3)))
    graph = _graph(stats.samples, "wpm over time")
    if graph:
        console.print(graph)
    console.print(Text("chars: correct / incorrect / extra / missed", style=theme.SUBTLE))


def show_stats():
    entries = history.load()
    summary = history.summary(entries)
    if not summary:
        console.print(Text("No tests recorded yet. Run a test first.", style=theme.SUBTLE))
        return

    table = Table.grid(padding=(0, 3))
    table.add_column(justify="right", style=theme.SUBTLE)
    table.add_column(style=theme.CORRECT)
    table.add_row("tests", str(summary["tests"]))
    table.add_row("best wpm", f"{summary['best_wpm']}")
    table.add_row("best acc", f"{summary['best_accuracy']}%")
    table.add_row("avg wpm", f"{summary['avg_wpm']}")
    table.add_row("recent avg", f"{summary['recent_avg_wpm']}")
    table.add_row("avg acc", f"{summary['avg_accuracy']}%")

    console.print(Panel(table, title="stats", border_style=theme.ACCENT, padding=(1, 3)))
    graph = _graph(history.wpm_series(entries), "wpm trend", height=15)
    if graph:
        console.print(graph)
