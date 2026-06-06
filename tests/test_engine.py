from monkeytype import input as keys
from monkeytype.engine import Engine


def _type(engine, sequence, start=0.0):
    """Feed keys one per second so timing is deterministic."""
    for i, key in enumerate(sequence):
        engine.press(key, start + i)


def test_perfect_run_completes_with_full_accuracy():
    engine = Engine(["the", "cat"])
    _type(engine, ["t", "h", "e", keys.SPACE, "c", "a", "t"])

    assert engine.done
    stats = engine.stats()
    assert stats.accuracy == 100.0
    assert stats.correct == 6
    assert stats.incorrect == 0
    # 7 correct chars (6 letters + 1 space) over 6 seconds.
    assert stats.wpm == 14.0
    assert stats.raw_wpm == 14.0
    assert stats.consistency == 100.0


def test_incorrect_letter_is_classified_and_penalizes_accuracy():
    engine = Engine(["hi"])
    _type(engine, ["h", "x"])

    stats = engine.stats()
    assert stats.correct == 1
    assert stats.incorrect == 1
    assert stats.accuracy == 50.0


def test_extra_characters_count_as_extra():
    engine = Engine(["hi", "yo"])
    _type(engine, ["h", "i", "x"])

    stats = engine.stats()
    assert stats.correct == 2
    assert stats.extra == 1
    assert not engine.done


def test_committing_short_word_counts_missed_chars():
    engine = Engine(["hello", "world"])
    _type(engine, ["h", "e", "l", keys.SPACE])

    stats = engine.stats()
    assert stats.correct == 3
    assert stats.missed == 2
    assert engine.word_idx == 1


def test_backspace_steps_into_prior_word_only_when_imperfect():
    engine = Engine(["ab", "cd"])
    _type(engine, ["a", "x", keys.SPACE])
    assert engine.word_idx == 1

    # Prior word "ax" is imperfect, so backspace at the boundary steps back.
    engine.press(keys.BACKSPACE, 10)
    assert engine.word_idx == 0
    assert engine.typed[0] == "ax"


def test_backspace_does_not_step_into_perfect_prior_word():
    engine = Engine(["ab", "cd"])
    _type(engine, ["a", "b", keys.SPACE])
    assert engine.word_idx == 1

    engine.press(keys.BACKSPACE, 10)
    assert engine.word_idx == 1


def test_live_accuracy_tracks_keystrokes():
    engine = Engine(["hi", "yo"])
    assert engine.live_accuracy() == 100.0
    _type(engine, ["h", "x"])
    assert engine.live_accuracy() == 50.0


def test_zen_mode_treats_all_input_as_correct():
    engine = Engine([], mode="zen")
    _type(engine, ["a", keys.SPACE, "b"])

    stats = engine.stats()
    assert engine.mode == "zen"
    assert stats.accuracy == 100.0
    assert not engine.done
