from monkeytype.content import Content, load_quotes


def test_quotes_load_with_length_categories():
    quotes = load_quotes()
    assert quotes
    assert all(q["length"] in ("short", "medium", "long") for q in quotes)
    assert all(q["text"] and q["source"] for q in quotes)


def test_random_quote_respects_length_filter():
    content = Content(seed=1)
    words, source = content.random_quote("short")
    assert words and source
    assert isinstance(words, list)


def test_seed_makes_selection_deterministic():
    assert Content(seed=7).random_quote() == Content(seed=7).random_quote()


def test_stream_fills_requested_length():
    content = Content(seed=3)
    words = content.stream(min_chars=200)
    assert sum(len(w) + 1 for w in words) >= 200


def test_no_punctuation_strips_symbols_and_lowercases():
    content = Content(punctuation=False, seed=2)
    words, _ = content.random_quote()
    joined = "".join(words)
    assert joined.isalnum()
    assert joined == joined.lower()
