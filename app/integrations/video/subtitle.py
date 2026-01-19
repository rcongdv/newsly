"""Subtitle generation utilities for video creation."""

import re
from dataclasses import dataclass

from app.integrations.tts.base import WordTiming


@dataclass
class SubtitleEntry:
    """A single subtitle entry with timing and text."""

    start_time: float  # seconds
    end_time: float  # seconds
    text: str


def word_timings_to_subtitles(
    word_timings: list[WordTiming],
    max_chars_per_line: int = 60,
    max_words_per_segment: int = 10,
) -> list[SubtitleEntry]:
    """
    Convert word timings to subtitle entries.

    Groups words into readable segments based on character/word limits
    while preserving accurate timing from the TTS engine.

    Args:
        word_timings: List of WordTiming from TTS service
        max_chars_per_line: Maximum characters per subtitle line
        max_words_per_segment: Maximum words per subtitle segment

    Returns:
        List of SubtitleEntry objects with accurate timing
    """
    if not word_timings:
        return []

    entries = []
    current_words: list[WordTiming] = []
    current_chars = 0

    for word_timing in word_timings:
        word_len = len(word_timing.word)

        # Check if adding this word would exceed limits
        would_exceed_chars = current_chars + word_len + (1 if current_words else 0) > max_chars_per_line
        would_exceed_words = len(current_words) >= max_words_per_segment

        if current_words and (would_exceed_chars or would_exceed_words):
            # Create subtitle entry from current words
            entries.append(
                SubtitleEntry(
                    start_time=current_words[0].start_time,
                    end_time=current_words[-1].end_time,
                    text=" ".join(w.word for w in current_words),
                )
            )
            current_words = []
            current_chars = 0

        # Add word to current segment
        current_words.append(word_timing)
        current_chars += word_len + (1 if len(current_words) > 1 else 0)

    # Don't forget the last segment
    if current_words:
        entries.append(
            SubtitleEntry(
                start_time=current_words[0].start_time,
                end_time=current_words[-1].end_time,
                text=" ".join(w.word for w in current_words),
            )
        )

    return entries


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_text_into_segments(
    text: str,
    audio_duration: float,
    max_chars_per_line: int = 60,
) -> list[SubtitleEntry]:
    """
    Split text into subtitle segments with proportional timing.

    Uses sentence-based chunking with character-proportional timing
    distribution across the audio duration.

    Args:
        text: The full text to split into subtitles
        audio_duration: Total audio duration in seconds
        max_chars_per_line: Maximum characters per subtitle line

    Returns:
        List of SubtitleEntry objects with timing information
    """
    if not text.strip():
        return []

    # Split into sentences using regex
    # Matches: . ! ? followed by space or end, handles abbreviations reasonably
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = re.split(sentence_pattern, text.strip())

    # Filter empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    # Further split long sentences at punctuation or natural breaks
    segments = []
    for sentence in sentences:
        if len(sentence) <= max_chars_per_line:
            segments.append(sentence)
        else:
            # Split at commas, semicolons, or colons if present
            sub_parts = re.split(r"(?<=[,;:])\s+", sentence)
            current_segment = ""
            for part in sub_parts:
                if not current_segment:
                    current_segment = part
                elif len(current_segment) + len(part) + 1 <= max_chars_per_line:
                    current_segment += " " + part
                else:
                    if current_segment:
                        segments.append(current_segment)
                    current_segment = part
            if current_segment:
                segments.append(current_segment)

    if not segments:
        return []

    # Calculate proportional timing based on character count
    total_chars = sum(len(s) for s in segments)
    if total_chars == 0:
        return []

    entries = []
    current_time = 0.0

    for segment in segments:
        # Proportional duration based on character count
        char_ratio = len(segment) / total_chars
        duration = audio_duration * char_ratio

        # Ensure minimum duration for readability (at least 1 second)
        duration = max(duration, 1.0)

        # Cap end time at audio duration
        end_time = min(current_time + duration, audio_duration)

        entries.append(
            SubtitleEntry(
                start_time=current_time,
                end_time=end_time,
                text=segment,
            )
        )

        current_time = end_time

    # Adjust last entry to match audio duration exactly
    if entries and entries[-1].end_time < audio_duration:
        entries[-1] = SubtitleEntry(
            start_time=entries[-1].start_time,
            end_time=audio_duration,
            text=entries[-1].text,
        )

    return entries


def generate_srt_content(entries: list[SubtitleEntry]) -> str:
    """
    Generate SRT format content from subtitle entries.

    Args:
        entries: List of SubtitleEntry objects

    Returns:
        SRT formatted string
    """
    if not entries:
        return ""

    lines = []
    for i, entry in enumerate(entries, start=1):
        lines.append(str(i))
        lines.append(
            f"{_format_srt_time(entry.start_time)} --> {_format_srt_time(entry.end_time)}"
        )
        lines.append(entry.text)
        lines.append("")  # Blank line between entries

    return "\n".join(lines)
