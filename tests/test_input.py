"""Key parsing tests driven through a pseudo-terminal in raw mode.

Guards against the buffered-read regression where reading a lone ESC byte would
slurp the rest of an arrow-key sequence, causing arrows to be misread as ESC.
"""

import os
import pty
import sys
import tty

import pytest

from monkeytype import input as keys


@pytest.fixture
def fake_tty(monkeypatch):
    master, slave = os.openpty()
    tty.setraw(slave)

    class FakeStdin:
        def fileno(self):
            return slave

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    yield master
    os.close(master)
    os.close(slave)


@pytest.mark.parametrize(
    "sequence, expected",
    [
        (b"\x1b[A", keys.UP),
        (b"\x1b[B", keys.DOWN),
        (b"\x1bOA", keys.UP),
        (b"a", "a"),
        (b" ", keys.SPACE),
        (b"\x7f", keys.BACKSPACE),
        (b"\t", keys.TAB),
        (b"\x03", keys.CTRL_C),
        (b"\x1b", keys.ESC),
    ],
)
def test_read_key_parses_sequences(fake_tty, sequence, expected):
    os.write(fake_tty, sequence)
    assert keys.read_key(timeout=1) == expected


def test_read_key_returns_none_on_timeout(fake_tty):
    assert keys.read_key(timeout=0.01) is None
