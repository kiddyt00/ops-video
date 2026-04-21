"""
Background Music (BGM) Generation Service

Generates simple background music/audio tracks using scipy/numpy.
Produces ambient loops suitable for manga video background.
"""
import math
import struct
import wave
from pathlib import Path
from typing import Optional
from uuid import UUID

import numpy as np
from scipy.io import wavfile

from ..config import settings, STORAGE_DIRS


class BGMService:
    """
    Generates simple background music using synthesized waveforms.

    Produces ambient/lo-fi tracks suitable for manga video backgrounds.
    """

    AUDIO_DIR = STORAGE_DIRS["audio"] / "bgm"

    def generate(
        self,
        duration: float = 30.0,
        bpm: int = 80,
        key: str = "C",
        mood: str = "ambient",
        output_filename: Optional[str] = None,
        sample_rate: int = 44100,
    ) -> Path:
        """
        Generate a background music track.

        Args:
            duration: Track duration in seconds
            bpm: Beats per minute
            key: Musical key (C, D, E, F, G, A, B)
            mood: Music mood (ambient, dramatic, cheerful, sad)
            output_filename: Optional output filename
            sample_rate: Audio sample rate

        Returns:
            Path to the generated WAV file
        """
        import time
        if output_filename is None:
            output_filename = f"bgm_{mood}_{int(time.time())}.wav"

        output_path = self.AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Note frequencies for the given key
        key_freqs = {
            "C": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],
            "D": [293.66, 329.63, 369.99, 392.00, 440.00, 493.88, 554.37],
            "E": [329.63, 369.99, 415.30, 440.00, 493.88, 554.37, 622.25],
            "F": [349.23, 392.00, 440.00, 466.16, 523.25, 587.33, 659.25],
            "G": [392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 739.99],
        }

        freqs = key_freqs.get(key, key_freqs["C"])
        mood_settings = self._get_mood_settings(mood)

        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        audio = np.zeros(len(t), dtype=np.float32)

        # Generate chord progression
        beat_duration = 60.0 / bpm
        num_beats = int(duration / beat_duration)
        chord_length = 4  # beats per chord

        for beat_idx in range(num_beats):
            beat_start = int(beat_idx * beat_duration * sample_rate)
            beat_end = int((beat_idx + 1) * beat_duration * sample_rate)
            if beat_start >= len(t):
                break

            # Select chord tones
            chord_idx = (beat_idx // chord_length) % len(freqs)
            root_freq = freqs[chord_idx]
            third_freq = freqs[(chord_idx + 2) % len(freqs)]
            fifth_freq = freqs[(chord_idx + 4) % len(freqs)]

            # Build this beat's audio
            beat_t = t[beat_start:beat_end]
            beat_len = len(beat_t)
            if beat_len == 0:
                continue

            # Envelope: attack-decay
            envelope = np.ones(beat_len)
            attack_samples = int(0.05 * sample_rate)
            decay_samples = int(0.3 * sample_rate)
            if attack_samples > 0:
                envelope[:attack_samples] = np.linspace(0, 1, min(attack_samples, beat_len))
            if decay_samples > 0 and beat_len > attack_samples:
                end = min(beat_len, attack_samples + decay_samples)
                envelope[attack_samples:end] = np.linspace(1, mood_settings["sustain"], end - attack_samples)
            envelope[end:] = mood_settings["sustain"]
            envelope *= mood_settings["volume"]

            # Mix harmonics
            signal = np.zeros(beat_len, dtype=np.float32)
            for freq, amp in [
                (root_freq, 0.4),
                (third_freq, 0.25),
                (fifth_freq, 0.2),
                (root_freq * 2, 0.1),  # octave
            ]:
                if mood_settings["wave"] == "sine":
                    signal += amp * np.sin(2 * math.pi * freq * beat_t)
                elif mood_settings["wave"] == "triangle":
                    signal += amp * (2 / math.pi) * np.arcsin(np.sin(2 * math.pi * freq * beat_t))
                else:
                    signal += amp * np.sin(2 * math.pi * freq * beat_t)

            audio[beat_start:beat_end] += signal * envelope

        # Normalize
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.8

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(str(output_path), sample_rate, audio_int16)

        return output_path

    def generate_panel_bgm(
        self,
        panels: list[dict],
        duration_per_panel: float = 3.0,
        mood: str = "ambient",
    ) -> list[Path]:
        """Generate short BGM clips for each storyboard panel."""
        paths = []
        for i, panel in enumerate(panels):
            panel_mood = panel.get("mood", mood)
            panel_dur = panel.get("duration", duration_per_panel)
            filename = f"bgm_panel_{i:03d}.wav"
            path = self.generate(
                duration=panel_dur,
                mood=panel_mood,
                output_filename=filename,
            )
            paths.append(path)
        return paths

    def _get_mood_settings(self, mood: str) -> dict:
        """Get waveform and volume settings for a given mood."""
        settings_map = {
            "ambient": {"wave": "sine", "volume": 0.3, "sustain": 0.6},
            "dramatic": {"wave": "triangle", "volume": 0.5, "sustain": 0.7},
            "cheerful": {"wave": "sine", "volume": 0.6, "sustain": 0.8},
            "sad": {"wave": "sine", "volume": 0.25, "sustain": 0.5},
        }
        return settings_map.get(mood, settings_map["ambient"])


bgm_service = BGMService()
