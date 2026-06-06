"""Raw per-keystroke terminal input.

Keeps the live loop responsive: read_key returns None on timeout so the caller
can refresh the countdown and live WPM even when no key is pressed.
"""

import os
import select
import sys
import termios
import tty
from contextlib import contextmanager

# Normalized key names for non-printable input.
SPACE = "SPACE"
BACKSPACE = "BACKSPACE"
ENTER = "ENTER"
ESC = "ESC"
TAB = "TAB"
CTRL_C = "CTRL_C"
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"

_ARROWS = {"A": UP, "B": DOWN, "C": RIGHT, "D": LEFT}


@contextmanager
def raw_mode():
    """Put the terminal in cbreak mode so keys arrive unbuffered."""
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def read_key(timeout=0.1):
    """Return the next key, or None if nothing arrives within timeout seconds.

    Reads from the raw file descriptor with os.read rather than the buffered
    sys.stdin. Buffered reads would slurp a whole escape sequence at once, so a
    later select() on the fd would miss the trailing bytes and misread an arrow
    key as a bare ESC.
    """
    fd = sys.stdin.fileno()
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return None

    data = os.read(fd, 6)
    if not data:
        return None

    head = data[:1]
    if head == b"\x03":
        return CTRL_C
    if head == b"\x1b":
        # ESC [ A/B/C/D or ESC O A; a lone ESC arrives as a single byte.
        if len(data) >= 3 and data[1:2] in (b"[", b"O"):
            return _ARROWS.get(chr(data[2]), ESC)
        return ESC
    if head in (b"\x7f", b"\x08"):
        return BACKSPACE
    if head in (b"\r", b"\n"):
        return ENTER
    if head == b"\t":
        return TAB
    if head == b" ":
        return SPACE

    try:
        char = data.decode("utf-8")[0]
    except (UnicodeDecodeError, IndexError):
        return None
    return char if char.isprintable() else None
