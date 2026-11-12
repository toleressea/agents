from fetch import lines, pick


def test_pick_never_takes_translated_auto_track():
    auto = {"en": [], "en-orig": [], "de": []}
    assert pick({"subtitles": {"en-GB": []}, "automatic_captions": auto}) == (
        "en-GB",
        False,
    )
    assert pick({"subtitles": {"live_chat": []}, "automatic_captions": auto}) == (
        "en-orig",
        True,
    )
    assert pick(
        {"subtitles": {"fr": []}, "automatic_captions": {"en": [], "es-orig": []}}
    ) == ("fr", False)
    assert pick({"automatic_captions": {"en": [], "es-orig": []}}) == ("es-orig", True)
    assert pick({"automatic_captions": {"en": []}}) is None


def test_lines_buckets_and_skips_empty_events():
    events = [
        {"tStartMs": 0, "segs": [{"utf8": "hello"}, {"utf8": " world"}]},
        {"tStartMs": 1000, "segs": [{"utf8": "\n"}]},
        {"tStartMs": 2000},
        {"tStartMs": 29_999, "segs": [{"utf8": "again"}]},
        {"tStartMs": 3_661_000, "segs": [{"utf8": "  late\nline "}]},
    ]
    assert lines(events) == ["[0:00:00] hello world again", "[1:01:00] late line"]
