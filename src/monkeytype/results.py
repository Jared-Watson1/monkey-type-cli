"""End-of-test results screen and the persistent stats view."""

import plotext as plt
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import input as keys
from . import stats as history
from . import theme

console = Console()

# Chart sizing bounds. Below the floor a plot is illegible, so it is skipped;
# above the cap it stops reading as a trend and just stretches.
MIN_CHART_WIDTH = 32
MAX_CHART_WIDTH = 100
MIN_CHART_HEIGHT = 8
# Rows kept free above/below the chart for the panel, headings and prompts.
CHART_VERTICAL_RESERVE = 8


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
    """A terminal-sized line plot, or None when there is too little to show.

    plotext emits ANSI escapes (including a trailing reset on every line).
    Passing that raw string to Rich leaks a literal "[0m" onto screen and
    throws off width math, so the output is parsed with Text.from_ansi.
    """
    if len(values) < 2 or console.width < MIN_CHART_WIDTH:
        return None
    width = max(MIN_CHART_WIDTH, min(console.width, MAX_CHART_WIDTH))
    height = max(MIN_CHART_HEIGHT, min(height, console.height - CHART_VERTICAL_RESERVE))

    plt.clear_figure()
    plt.theme("clear")
    plt.plot(list(range(len(values))), values, marker="braille")
    plt.title(title)
    plt.plotsize(width, height)
    plt.xfrequency(0)
    return Align.center(Text.from_ansi(plt.build()))


def _trend(value, delta, has_history, unit=""):
    """A value followed by a colored up/down delta against the lifetime average."""
    text = Text()
    text.append(f"{value}{unit}", style=theme.CORRECT)
    if not has_history or abs(delta) < 0.05:
        return text
    if delta > 0:
        text.append(f"  ▲ +{delta:.1f}", style=theme.POSITIVE)
    else:
        text.append(f"  ▼ {abs(delta):.1f}", style=theme.NEGATIVE)
    return text


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


def _lifetime_block(stats):
    """A two-row grid comparing this run to the lifetime averages, or None.

    Stacking wpm and accuracy keeps each row short so it never wraps on a
    narrow terminal, and it mirrors the stat grid below it.
    """
    progress = history.progress(history.load())
    if not progress:
        return None
    grid = Table.grid(padding=(0, 2))
    grid.add_column(justify="right", style=theme.SUBTLE)
    grid.add_column()
    grid.add_row("vs avg", _trend(progress["avg_wpm"], stats.wpm - progress["avg_wpm"],
                                  progress["has_history"], unit=" wpm"))
    grid.add_row("", _trend(progress["avg_accuracy"], stats.accuracy - progress["avg_accuracy"],
                            progress["has_history"], unit="% acc"))
    return Align.center(grid)


def show_result(stats):
    headline = Text(justify="center")
    headline.append(f"{stats.wpm}", style=theme.HEADER)
    headline.append(" wpm    ", style=theme.ACCENT)
    headline.append(f"{stats.accuracy}%", style=theme.HEADER)
    headline.append(" acc", style=theme.ACCENT)

    body = [Align.center(headline), Text()]
    lifetime = _lifetime_block(stats)
    if lifetime:
        body.append(lifetime)
        body.append(Text())
    body.append(Align.center(_stat_table(stats)))

    console.print()
    console.print(Panel(Group(*body), border_style=theme.ACCENT, padding=(1, 3)))
    graph = _graph(stats.samples, "wpm over time")
    if graph:
        console.print(graph)
    console.print(Text("chars: correct / incorrect / extra / missed",
                       style=theme.SUBTLE, justify="center"))


def show_stats():
    entries = history.load()
    summary = history.summary(entries)
    if not summary:
        console.print(Text("No tests recorded yet. Run a test first.", style=theme.SUBTLE))
        return

    has_history = summary["tests"] > 1
    recent_wpm = _trend(summary["recent_avg_wpm"],
                        summary["recent_avg_wpm"] - summary["avg_wpm"], has_history)
    recent_acc = _trend(summary["recent_avg_accuracy"],
                        summary["recent_avg_accuracy"] - summary["avg_accuracy"],
                        has_history, unit="%")

    table = Table.grid(padding=(0, 3))
    table.add_column(justify="right", style=theme.SUBTLE)
    table.add_column(style=theme.CORRECT)
    table.add_row("tests", str(summary["tests"]))
    table.add_row("best wpm", f"{summary['best_wpm']}")
    table.add_row("best acc", f"{summary['best_accuracy']}%")
    table.add_row("avg wpm", f"{summary['avg_wpm']}")
    table.add_row("recent wpm", recent_wpm)
    table.add_row("avg acc", f"{summary['avg_accuracy']}%")
    table.add_row("recent acc", recent_acc)

    console.print(Panel(table, title="stats", border_style=theme.ACCENT, padding=(1, 3)))
    graph = _graph(history.wpm_series(entries), "wpm trend", height=15)
    if graph:
        console.print(graph)
