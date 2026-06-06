# monkey-type-cli

A lightweight, terminal-native typing test inspired by [MonkeyType](https://monkeytype.com).
Type through real quotes letter by letter, correct mistakes as you go, and track your
words-per-minute and accuracy over time, all from the command line.

## Install

```sh
pip install -e .
```

This adds a `monkeytype` command.

## Usage

Run with no arguments for an interactive menu:

```sh
monkeytype
```

Or start a test directly:

```sh
monkeytype --quote            # a random quote
monkeytype --quote short      # short / medium / long
monkeytype --time 30          # timed test (15, 30, 60, 120 seconds)
monkeytype --zen              # free typing until ESC
monkeytype --no-punctuation   # strip punctuation and capitals
monkeytype --seed 42          # repeatable text selection
```

View your history:

```sh
monkeytype stats
```

### Typing rules

Mirrors MonkeyType's default behavior: wrong letters turn red but you keep typing,
space commits the current word and advances, and backspace fixes errors, stepping back
into a previous word only if you left it imperfect. Press `ESC` to end (zen mode) or
abort, `Ctrl-C` to quit.

## Stats

Every completed test is appended to `~/.monkeytype-cli/history.jsonl`. The `stats`
command shows your best and average WPM/accuracy alongside a WPM trend graph.

## Development

```sh
pip install -e ".[dev]"
pytest
```

The engine (`engine.py`) is a pure state machine with no terminal I/O, so the typing
logic, WPM/accuracy math, and character classification are fully unit-tested without a
TTY.
