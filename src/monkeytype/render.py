"""Live typing view built as rich renderables. Holds no state of its own."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from . import theme

INNER_MAX = 64
VISIBLE_LINES = 3
# header + panel (3 lines + 2 padding + 2 border) + blank + footer
CONTENT_HEIGHT = 1 + (VISIBLE_LINES + 4) + 1 + 1


def _typed_word(target, typed, is_current):
    """Color one word's characters and place the cursor when it is current."""
    text = Text()
    cursor = len(typed)
    for pos, ch in enumerate(target):
        if pos < len(typed):
            style = theme.CORRECT if typed[pos] == ch else theme.INCORRECT
        elif is_current and pos == cursor:
            style = theme.CURSOR
        else:
            style = theme.PENDING
        text.append(ch, style=style)
    for extra in typed[len(target):]:
        text.append(extra, style=theme.EXTRA)
    if is_current and cursor >= len(target):
        text.append(" ", style=theme.CURSOR)
    return text


def _wrap(lengths, width):
    """Group word indices into lines that fit within width characters."""
    lines = []
    line = []
    used = 0
    for i, length in enumerate(lengths):
        cost = length if not line else length + 1
        if line and used + cost > width:
            lines.append(line)
            line, used = [i], length
        else:
            line.append(i)
            used += cost
    if line:
        lines.append(line)
    return lines or [[]]


def _window(lines, current_line):
    """A 3-line slice keeping the active line centered when possible."""
    start = max(0, current_line - 1)
    return lines[start:start + VISIBLE_LINES]


def _words_body(engine, width):
    words = engine.words
    lines = _wrap([len(w) for w in words], width)
    current_line = next(
        (li for li, idxs in enumerate(lines) if engine.word_idx <= idxs[-1]),
        len(lines) - 1,
    )
    body = Text(justify="left")
    visible = _window(lines, current_line)
    for row, idxs in enumerate(visible):
        if row:
            body.append("\n")
        for col, i in enumerate(idxs):
            if col:
                body.append(" ")
            typed = engine.typed[i] if i < len(engine.typed) else ""
            body.append_text(_typed_word(words[i], typed, i == engine.word_idx))
    return body, len(visible)


def _zen_body(engine, width):
    words = engine.typed[0].split(" ")
    lines = _wrap([len(w) for w in words], width)
    visible = lines[-VISIBLE_LINES:]
    body = Text(justify="left")
    for row, idxs in enumerate(visible):
        if row:
            body.append("\n")
        for col, i in enumerate(idxs):
            if col:
                body.append(" ")
            body.append(words[i], style=theme.CORRECT)
    body.append(" ", style=theme.CURSOR)
    return body, len(visible)


def _header(engine, remaining):
    wpm = int(engine.live_wpm())
    acc = int(round(engine.live_accuracy()))
    if engine.mode == "time":
        tail = f"{int(remaining)}s"
    elif engine.mode == "zen":
        tail = "zen"
    else:
        tail = f"{engine.word_idx}/{len(engine.words)}"
    line = Text(justify="center")
    line.append(f"{wpm} wpm", style=theme.ACCENT)
    line.append("   ·   ", style=theme.SUBTLE)
    line.append(f"{acc}%", style=theme.SUBTLE)
    line.append("   ·   ", style=theme.SUBTLE)
    line.append(tail, style=theme.SUBTLE)
    return line


def _footer(engine):
    hint = "esc finish   ·   tab restart" if engine.is_zen else "tab restart   ·   esc quit"
    return Text(hint, style=theme.SUBTLE, justify="center")


def typing_view(engine, remaining, width, height):
    inner = min(max(20, width - 8), INNER_MAX)
    if engine.is_zen:
        body, used = _zen_body(engine, inner)
    else:
        body, used = _words_body(engine, inner)
    for _ in range(VISIBLE_LINES - used):
        body.append("\n")

    panel = Panel(body, width=inner + 6, border_style=theme.SUBTLE, padding=(1, 2))
    view = Group(
        Align.center(_header(engine, remaining)),
        Align.center(panel),
        Text(),
        Align.center(_footer(engine)),
    )

    top_pad = max(0, (height - CONTENT_HEIGHT) // 2)
    if top_pad:
        return Group(Text("\n" * top_pad), view)
    return view
