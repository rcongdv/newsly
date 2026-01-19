"""ElevenLabs TTS service implementation."""

import base64
import logging

from elevenlabs.client import ElevenLabs

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import WordTiming

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """ElevenLabs text-to-speech service with word-level timing support."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str,
        output_path: str,
    ):
        self._elevenlabs = ElevenLabs(api_key=api_key)
        self._voice_id = voice_id
        self._model_id = model_id
        self._output_path = output_path
        self._word_timings: list[WordTiming] = []

    @property
    def output_path(self) -> str:
        """Return the output path where audio will be saved."""
        return self._output_path

    @property
    def word_timings(self) -> list[WordTiming]:
        """Return word timing data from last TTS generation."""
        return self._word_timings

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with ElevenLabs and extract word timings."""
        logger.info("Generating TTS audio with ElevenLabs (with timestamps)")
        try:
            response = self._elevenlabs.text_to_speech.convert_with_timestamps(
                text=text,
                voice_id=self._voice_id,
                model_id=self._model_id,
            )

            # Extract audio and save to file
            audio_bytes = base64.b64decode(response.audio_base_64)
            with open(self._output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"TTS audio saved to {self._output_path}")

            # Extract word timings from alignment data
            self._word_timings = self._extract_word_timings(response.alignment)
            logger.info(f"Extracted {len(self._word_timings)} word timings")

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with ElevenLabs",
                detail=str(e),
            ) from e

    def _extract_word_timings(self, alignment) -> list[WordTiming]:
        """Extract word timings from ElevenLabs alignment data.

        ElevenLabs returns character-level timing. We aggregate these
        into word-level timings by detecting word boundaries.
        """
        if not alignment:
            logger.warning(
                "No alignment data received from ElevenLabs - "
                "subtitles will use estimated timing"
            )
            return []

        # Safely access alignment attributes with defensive checks
        characters = getattr(alignment, "characters", None)
        start_times = getattr(alignment, "character_start_times_seconds", None)
        end_times = getattr(alignment, "character_end_times_seconds", None)

        if not characters or not start_times or not end_times:
            logger.warning(
                "Incomplete alignment data from ElevenLabs - "
                "missing characters or timing arrays"
            )
            return []

        # Validate array lengths match
        if len(characters) != len(start_times) or len(characters) != len(end_times):
            logger.warning(
                f"Alignment data length mismatch: chars={len(characters)}, "
                f"starts={len(start_times)}, ends={len(end_times)}"
            )
            return []

        word_timings = []
        current_word = ""
        word_start = None

        for i, char in enumerate(characters):
            if char.isspace():
                # End of word
                if current_word and word_start is not None:
                    word_timings.append(
                        WordTiming(
                            word=current_word,
                            start_time=word_start,
                            end_time=end_times[i - 1] if i > 0 else start_times[i],
                        )
                    )
                current_word = ""
                word_start = None
            else:
                # Part of a word
                if word_start is None:
                    word_start = start_times[i]
                current_word += char

        # Don't forget the last word
        if current_word and word_start is not None:
            word_timings.append(
                WordTiming(
                    word=current_word,
                    start_time=word_start,
                    end_time=end_times[-1] if end_times else word_start,
                )
            )

        return word_timings


def create_elevenlabs_service(settings: Settings) -> ElevenLabsService:
    """Factory function to create ElevenLabsService from settings."""
    return ElevenLabsService(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        model_id=settings.elevenlabs_model_id,
        output_path=settings.tts_output_path,
    )
