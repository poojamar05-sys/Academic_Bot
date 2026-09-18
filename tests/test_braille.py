from braille import text_to_braille


def test_basic_ascii_braille():
    assert text_to_braille("A") == "⠁"
    assert text_to_braille("hello") == "⠓⠑⠇⠇⠕"


def test_text_with_space_and_punctuation():
    text = "Cloud computing"
    assert text_to_braille(text) == "⠉⠇⠕⠥⠙ ⠉⠕⠍⠏⠥⠞⠊⠝⠛"
