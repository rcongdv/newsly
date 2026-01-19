"""Tests for the subtitle generation utilities."""

import pytest

from app.integrations.tts.base import WordTiming
from app.integrations.video.subtitle import (
    SubtitleEntry,
    split_text_into_segments,
    generate_srt_content,
    word_timings_to_subtitles,
    _format_srt_time,
)


class TestFormatSrtTime:
    """Tests for the _format_srt_time function."""

    def test_format_zero_seconds(self):
        """Test formatting zero seconds."""
        assert _format_srt_time(0.0) == "00:00:00,000"

    def test_format_milliseconds(self):
        """Test formatting with milliseconds."""
        assert _format_srt_time(0.5) == "00:00:00,500"
        assert _format_srt_time(0.123) == "00:00:00,123"

    def test_format_seconds(self):
        """Test formatting seconds."""
        assert _format_srt_time(5.0) == "00:00:05,000"
        assert _format_srt_time(59.999) == "00:00:59,999"

    def test_format_minutes(self):
        """Test formatting minutes."""
        assert _format_srt_time(60.0) == "00:01:00,000"
        assert _format_srt_time(125.5) == "00:02:05,500"

    def test_format_hours(self):
        """Test formatting hours."""
        assert _format_srt_time(3600.0) == "01:00:00,000"
        assert _format_srt_time(3661.123) == "01:01:01,123"


class TestSplitTextIntoSegments:
    """Tests for the split_text_into_segments function."""

    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns empty list."""
        result = split_text_into_segments("", 10.0)
        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        """Test that whitespace-only text returns empty list."""
        result = split_text_into_segments("   \n\t  ", 10.0)
        assert result == []

    def test_single_sentence(self):
        """Test splitting a single sentence."""
        result = split_text_into_segments("Hello world.", 5.0)
        assert len(result) == 1
        assert result[0].text == "Hello world."
        assert result[0].start_time == 0.0
        assert result[0].end_time == 5.0

    def test_multiple_sentences(self):
        """Test splitting multiple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        result = split_text_into_segments(text, 30.0)

        assert len(result) == 3
        assert result[0].text == "First sentence."
        assert result[1].text == "Second sentence."
        assert result[2].text == "Third sentence."

    def test_timing_is_proportional_to_length(self):
        """Test that timing is proportional to segment length."""
        text = "Short. This is a much longer sentence."
        result = split_text_into_segments(text, 20.0)

        assert len(result) == 2
        # Longer sentence should have more time
        short_duration = result[0].end_time - result[0].start_time
        long_duration = result[1].end_time - result[1].start_time
        assert long_duration > short_duration

    def test_segments_are_contiguous(self):
        """Test that segment timings are contiguous."""
        text = "First. Second. Third."
        result = split_text_into_segments(text, 15.0)

        for i in range(1, len(result)):
            assert result[i].start_time == result[i - 1].end_time

    def test_last_segment_ends_at_duration(self):
        """Test that the last segment ends at the audio duration."""
        text = "First. Second. Third."
        duration = 15.0
        result = split_text_into_segments(text, duration)

        assert result[-1].end_time == duration

    def test_question_and_exclamation_marks(self):
        """Test splitting on question and exclamation marks."""
        text = "Is this working? Yes it is! Great."
        result = split_text_into_segments(text, 15.0)

        assert len(result) == 3
        assert result[0].text == "Is this working?"
        assert result[1].text == "Yes it is!"
        assert result[2].text == "Great."

    def test_long_sentence_splits_at_commas(self):
        """Test that long sentences are split at punctuation."""
        text = "This is a very long sentence that goes on and on, with a comma here, and another part after."
        result = split_text_into_segments(text, 30.0, max_chars_per_line=40)

        # Should have multiple segments
        assert len(result) >= 2

    def test_minimum_duration_per_segment(self):
        """Test that segments have minimum duration for readability."""
        text = "A. B. C. D. E."
        result = split_text_into_segments(text, 100.0)

        for entry in result:
            duration = entry.end_time - entry.start_time
            assert duration >= 1.0  # Minimum 1 second


class TestGenerateSrtContent:
    """Tests for the generate_srt_content function."""

    def test_empty_entries_returns_empty_string(self):
        """Test that empty entries returns empty string."""
        result = generate_srt_content([])
        assert result == ""

    def test_single_entry(self):
        """Test generating SRT for a single entry."""
        entries = [SubtitleEntry(0.0, 5.0, "Hello world")]
        result = generate_srt_content(entries)

        lines = result.strip().split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:05,000"
        assert lines[2] == "Hello world"

    def test_multiple_entries(self):
        """Test generating SRT for multiple entries."""
        entries = [
            SubtitleEntry(0.0, 3.0, "First line"),
            SubtitleEntry(3.0, 6.0, "Second line"),
            SubtitleEntry(6.0, 10.0, "Third line"),
        ]
        result = generate_srt_content(entries)

        # Each entry should have: number, timestamp, text, blank line
        lines = result.split("\n")

        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:03,000"
        assert lines[2] == "First line"
        assert lines[3] == ""

        assert lines[4] == "2"
        assert lines[5] == "00:00:03,000 --> 00:00:06,000"
        assert lines[6] == "Second line"

    def test_srt_format_compliance(self):
        """Test that output follows SRT format specification."""
        entries = [SubtitleEntry(61.5, 125.999, "Test subtitle")]
        result = generate_srt_content(entries)

        lines = result.strip().split("\n")
        assert lines[0] == "1"
        assert "-->" in lines[1]
        assert "," in lines[1]  # Milliseconds use comma in SRT


class TestSubtitleEntry:
    """Tests for the SubtitleEntry dataclass."""

    def test_create_entry(self):
        """Test creating a subtitle entry."""
        entry = SubtitleEntry(start_time=1.5, end_time=5.0, text="Test")

        assert entry.start_time == 1.5
        assert entry.end_time == 5.0
        assert entry.text == "Test"

    def test_entry_equality(self):
        """Test subtitle entry equality."""
        entry1 = SubtitleEntry(1.0, 2.0, "Same")
        entry2 = SubtitleEntry(1.0, 2.0, "Same")

        assert entry1 == entry2


class TestWordTimingsToSubtitles:
    """Tests for the word_timings_to_subtitles function."""

    def test_empty_timings_returns_empty_list(self):
        """Test that empty word timings returns empty list."""
        result = word_timings_to_subtitles([])
        assert result == []

    def test_single_word(self):
        """Test converting a single word timing."""
        timings = [WordTiming(word="Hello", start_time=0.0, end_time=0.5)]
        result = word_timings_to_subtitles(timings)

        assert len(result) == 1
        assert result[0].text == "Hello"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 0.5

    def test_multiple_words_single_segment(self):
        """Test that multiple short words are grouped into one segment."""
        timings = [
            WordTiming(word="Hello", start_time=0.0, end_time=0.3),
            WordTiming(word="world", start_time=0.4, end_time=0.7),
        ]
        result = word_timings_to_subtitles(timings)

        assert len(result) == 1
        assert result[0].text == "Hello world"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 0.7

    def test_respects_max_chars_per_line(self):
        """Test that segments don't exceed max characters."""
        timings = [
            WordTiming(word="This", start_time=0.0, end_time=0.2),
            WordTiming(word="is", start_time=0.3, end_time=0.4),
            WordTiming(word="a", start_time=0.5, end_time=0.6),
            WordTiming(word="test", start_time=0.7, end_time=0.9),
            WordTiming(word="sentence", start_time=1.0, end_time=1.5),
        ]
        result = word_timings_to_subtitles(timings, max_chars_per_line=10)

        # Should split because "This is a test" > 10 chars
        assert len(result) >= 2

    def test_respects_max_words_per_segment(self):
        """Test that segments don't exceed max words."""
        timings = [
            WordTiming(word="One", start_time=0.0, end_time=0.1),
            WordTiming(word="two", start_time=0.2, end_time=0.3),
            WordTiming(word="three", start_time=0.4, end_time=0.5),
            WordTiming(word="four", start_time=0.6, end_time=0.7),
            WordTiming(word="five", start_time=0.8, end_time=0.9),
        ]
        result = word_timings_to_subtitles(timings, max_words_per_segment=3)

        assert len(result) == 2
        assert result[0].text == "One two three"
        assert result[1].text == "four five"

    def test_preserves_accurate_timing(self):
        """Test that timing comes from actual word timings, not estimation."""
        timings = [
            WordTiming(word="First", start_time=0.5, end_time=1.0),
            WordTiming(word="segment", start_time=1.2, end_time=1.8),
            WordTiming(word="here", start_time=2.0, end_time=2.5),
        ]
        result = word_timings_to_subtitles(timings, max_words_per_segment=2)

        assert len(result) == 2
        # First segment timing from actual words
        assert result[0].start_time == 0.5
        assert result[0].end_time == 1.8
        # Second segment timing
        assert result[1].start_time == 2.0
        assert result[1].end_time == 2.5

    def test_handles_single_long_word(self):
        """Test handling a single word that's very long."""
        timings = [
            WordTiming(word="Supercalifragilisticexpialidocious", start_time=0.0, end_time=2.0),
            WordTiming(word="is", start_time=2.1, end_time=2.3),
        ]
        result = word_timings_to_subtitles(timings, max_chars_per_line=20)

        # Long word should be its own segment
        assert len(result) == 2
        assert result[0].text == "Supercalifragilisticexpialidocious"
