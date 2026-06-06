"""Quote corpus loading and text generation.

The typing target always comes from real quotes rather than random words, so
punctuation and capitalization arrive naturally. Length categories are derived
from word count at load time so the data file stays simple.
"""

import json
import random
from importlib import resources

SHORT_MAX_WORDS = 15
MEDIUM_MAX_WORDS = 40

LENGTHS = ("short", "medium", "long")


def _category(text):
    count = len(text.split())
    if count < SHORT_MAX_WORDS:
        return "short"
    if count < MEDIUM_MAX_WORDS:
        return "medium"
    return "long"


def load_quotes():
    """Return the bundled quote corpus as a list of {text, source, length}."""
    raw = resources.files("monkeytype.data").joinpath("quotes.json").read_text("utf-8")
    quotes = json.loads(raw)
    for quote in quotes:
        quote["length"] = _category(quote["text"])
    return quotes


def _strip_punctuation(text):
    kept = [c for c in text if c.isalnum() or c.isspace()]
    return "".join(kept).lower()


class Content:
    """Serves typing targets from the quote corpus.

    A dedicated Random instance keeps tests deterministic when a seed is passed
    and avoids touching global RNG state otherwise.
    """

    def __init__(self, punctuation=True, seed=None):
        self.punctuation = punctuation
        self.quotes = load_quotes()
        self.rng = random.Random(seed)

    def _prepare(self, text):
        return text if self.punctuation else _strip_punctuation(text)

    def random_quote(self, length=None):
        """Return one quote's words, optionally filtered by length category."""
        pool = self.quotes
        if length:
            pool = [q for q in self.quotes if q["length"] == length] or self.quotes
        quote = self.rng.choice(pool)
        return self._prepare(quote["text"]).split(), quote["source"]

    def stream(self, min_chars):
        """Concatenate random quotes until reaching at least min_chars.

        Used by time mode, which needs continuous text the typist cannot exhaust
        before the clock runs out.
        """
        words = []
        chars = 0
        while chars < min_chars:
            text = self._prepare(self.rng.choice(self.quotes)["text"])
            for word in text.split():
                words.append(word)
                chars += len(word) + 1
        return words
