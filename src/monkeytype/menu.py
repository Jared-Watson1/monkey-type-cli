"""Interactive launch menu shown when monkeytype runs with no arguments."""

from rich.console import Console
from rich.text import Text

from . import input as keys
from . import theme

console = Console()

# Each option resolves to a test config consumed by cli, or a string action.
OPTIONS = [
    ("quote  short", {"mode": "words", "length": "short"}),
    ("quote  medium", {"mode": "words", "length": "medium"}),
    ("quote  long", {"mode": "words", "length": "long"}),
    ("time   15s", {"mode": "time", "duration": 15}),
    ("time   30s", {"mode": "time", "duration": 30}),
    ("time   60s", {"mode": "time", "duration": 60}),
    ("zen", {"mode": "zen"}),
    ("view stats", "stats"),
]


def _render(selected):
    console.clear()
    console.print(Text("monkeytype", style=theme.HEADER))
    console.print(Text("use arrows or j/k, enter to start, q to quit", style=theme.SUBTLE))
    console.print()
    for i, (label, _) in enumerate(OPTIONS):
        if i == selected:
            console.print(Text(f"  > {label}", style=theme.CURSOR))
        else:
            console.print(Text(f"    {label}", style=theme.PENDING))


def run():
    """Return the chosen config dict, an action string, or None if quitting."""
    selected = 0
    with keys.raw_mode():
        while True:
            _render(selected)
            key = keys.read_key(timeout=None)
            if key in (keys.CTRL_C, keys.ESC, "q"):
                return None
            if key in (keys.ENTER, keys.SPACE):
                return OPTIONS[selected][1]
            if key in (keys.DOWN, "j"):
                selected = (selected + 1) % len(OPTIONS)
            elif key in (keys.UP, "k"):
                selected = (selected - 1) % len(OPTIONS)
