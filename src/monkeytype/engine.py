"""Pure typing-test state machine.

No terminal I/O and no clock access: every transition receives a monotonic
timestamp from the caller, so the whole engine is unit-testable without a TTY.
Behavior mirrors MonkeyType's default: wrong letters stay visible in red, space
commits the current word, and backspace can step back into a prior word only if
that word was left imperfect.
"""

from dataclasses import dataclass, field

from . import input as keys

# Per-character render states.
PENDING = "pending"
CORRECT = "correct"
INCORRECT = "incorrect"
EXTRA = "extra"


@dataclass
class Stats:
    wpm: float
    raw_wpm: float
    accuracy: float
    consistency: float
    correct: int
    incorrect: int
    extra: int
    missed: int
    samples: list = field(default_factory=list)


class Engine:
    def __init__(self, words, mode="words", duration=None):
        self.mode = mode
        self.duration = duration
        self.words = list(words)
        self.typed = [""]
        self.word_idx = 0
        self.done = False

        self.start_time = None
        self.last_time = None
        self.total_keystrokes = 0
        self.correct_keystrokes = 0
        # Timestamps of produced characters (letters + committed spaces), used
        # for per second WPM samples and the consistency metric.
        self.char_times = []

    @property
    def is_zen(self):
        return self.mode == "zen"

    @property
    def current_word(self):
        return self.words[self.word_idx] if self.word_idx < len(self.words) else ""

    def press(self, key, t):
        if self.done:
            return
        if self.start_time is None and key not in (keys.BACKSPACE,):
            self.start_time = t
        self.last_time = t

        if key == keys.BACKSPACE:
            self._backspace()
        elif key == keys.SPACE:
            self._commit_word(t)
        elif len(key) == 1 and key.isprintable():
            self._type_char(key, t)

    def _type_char(self, char, t):
        buf = self.typed[self.word_idx]
        position = len(buf)
        self.typed[self.word_idx] = buf + char

        self.total_keystrokes += 1
        target = self.current_word
        correct = position < len(target) and char == target[position]
        if correct or self.is_zen:
            self.correct_keystrokes += 1
        self.char_times.append(t)

        if not self.is_zen and self._last_word_complete():
            self.done = True

    def _commit_word(self, t):
        buf = self.typed[self.word_idx]
        if buf == "":
            return
        if self.is_zen:
            self.typed[self.word_idx] = buf + " "
            self.total_keystrokes += 1
            self.correct_keystrokes += 1
            self.char_times.append(t)
            return

        self.total_keystrokes += 1
        self.correct_keystrokes += 1
        self.char_times.append(t)
        self.word_idx += 1
        if self.word_idx >= len(self.words):
            self.done = True
            return
        if self.word_idx >= len(self.typed):
            self.typed.append("")

    def _backspace(self):
        buf = self.typed[self.word_idx]
        if buf:
            self.typed[self.word_idx] = buf[:-1]
            return
        if self.is_zen or self.word_idx == 0:
            return
        prev = self.typed[self.word_idx - 1]
        # MonkeyType only lets you reach back into a word you left imperfect.
        if prev != self.words[self.word_idx - 1]:
            self.word_idx -= 1

    def _last_word_complete(self):
        last = len(self.words) - 1
        return self.word_idx == last and self.typed[last] == self.words[last]

    def elapsed(self, now=None):
        if self.start_time is None:
            return 0.0
        end = now if now is not None else self.last_time
        return max(0.0, end - self.start_time)

    def live_wpm(self, now=None):
        minutes = self.elapsed(now) / 60
        if minutes <= 0:
            return 0.0
        return (self._correct_chars() / 5) / minutes

    def live_accuracy(self):
        if not self.total_keystrokes:
            return 100.0
        return 100 * self.correct_keystrokes / self.total_keystrokes

    def _correct_chars(self):
        total = 0
        for i, typed in enumerate(self.typed):
            if self.is_zen:
                total += len(typed)
                continue
            target = self.words[i] if i < len(self.words) else ""
            for pos, ch in enumerate(typed):
                if pos < len(target) and ch == target[pos]:
                    total += 1
        # Each committed word contributes one correct space separator.
        total += self.word_idx
        return total

    def _classify(self):
        correct = incorrect = extra = missed = 0
        committed = self.word_idx
        for i, typed in enumerate(self.typed):
            target = self.words[i] if i < len(self.words) else ""
            for pos, ch in enumerate(typed):
                if pos < len(target):
                    if ch == target[pos]:
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    extra += 1
            if i < committed and len(typed) < len(target):
                missed += len(target) - len(typed)
        return correct, incorrect, extra, missed

    def _samples(self):
        """Per-second WPM values derived from character timestamps."""
        if not self.char_times or self.start_time is None:
            return []
        buckets = {}
        for t in self.char_times:
            second = int(t - self.start_time)
            buckets[second] = buckets.get(second, 0) + 1
        span = max(buckets) + 1
        # chars/5 per second scaled to per-minute equals chars * 12.
        return [buckets.get(s, 0) * 12 for s in range(span)]

    def stats(self, now=None):
        minutes = self.elapsed(now) / 60
        if minutes <= 0:
            minutes = 1 / 60

        correct_chars = self._correct_chars()
        all_chars = sum(len(t) for t in self.typed) + (
            0 if self.is_zen else self.word_idx
        )
        wpm = (correct_chars / 5) / minutes
        raw_wpm = (all_chars / 5) / minutes
        accuracy = 100.0
        if self.total_keystrokes:
            accuracy = 100 * self.correct_keystrokes / self.total_keystrokes

        samples = self._samples()
        consistency = _consistency(samples)
        correct, incorrect, extra, missed = self._classify()
        return Stats(
            wpm=round(wpm, 1),
            raw_wpm=round(raw_wpm, 1),
            accuracy=round(accuracy, 1),
            consistency=round(consistency, 1),
            correct=correct,
            incorrect=incorrect,
            extra=extra,
            missed=missed,
            samples=samples,
        )


def _consistency(samples):
    """1 - coefficient of variation, as a clamped percentage."""
    if len(samples) < 2:
        return 100.0
    mean = sum(samples) / len(samples)
    if mean == 0:
        return 0.0
    variance = sum((s - mean) ** 2 for s in samples) / len(samples)
    cv = (variance**0.5) / mean
    return max(0.0, min(100.0, (1 - cv) * 100))
