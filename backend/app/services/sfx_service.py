"""
Sound Effects (SFX) Generation Service

Generates simple sound effects using scipy/numpy for manga video panels.
"""
import math
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.io import wavfile

from ..config import settings, STORAGE_DIRS


class SFXService:
    """Generates sound effects using synthesized waveforms."""

    AUDIO_DIR = STORAGE_DIRS["audio"] / "sfx"

    SFX_TYPES = ["whoosh", "impact", "sparkle", "wind", "rain", "thunder"]

    def generate(
        self,
        sfx_type: str = "whoosh",
        duration: float = 1.0,
        intensity: float = 0.5,
        output_filename: Optional[str] = None,
        sample_rate: int = 44100,
    ) -> Path:
        """
        Generate a sound effect.

        Args:
            sfx_type: Type of SFX (whoosh, impact, sparkle, wind, rain, thunder)
            duration: Duration in seconds
            intensity: Intensity 0.0-1.0
            output_filename: Optional output filename
            sample_rate: Audio sample rate

        Returns:
            Path to generated WAV file
        """
        import time
        if output_filename is None:
            output_filename = f"sfx_{sfx_type}_{int(time.time())}.wav"

        output_path = self.AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generators = {
            "whoosh": self._gen_whoosh,
            "impact": self._gen_impact,
            "sparkle": self._gen_sparkle,
            "wind": self._gen_wind,
            "rain": self._gen_rain,
            "thunder": self._gen_thunder,
        }

        generator = generators.get(sfx_type, self._gen_whoosh)
        audio = generator(duration, intensity, sample_rate)

        # Normalize
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.8

        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(str(output_path), sample_rate, audio_int16)

        return output_path

    def _gen_whoosh(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """Filtered noise sweep for whoosh effect."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        # White noise with bandpass sweep
        noise = np.random.randn(len(t)).astype(np.float32)
        freq_sweep = 200 + intensity * 2000 * (t / dur)
        carrier = np.sin(2 * math.pi * freq_sweep * t)
        envelope = np.exp(-3 * t / dur)
        return noise * 0.3 * envelope + carrier * 0.7 * envelope

    def _gen_impact(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """Low-frequency impact hit."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        base_freq = 40 + intensity * 60
        signal = np.sin(2 * math.pi * base_freq * t)
        # Add sub-bass
        signal += 0.5 * np.sin(2 * math.pi * base_freq * 0.5 * t)
        # Sharp attack envelope
        envelope = np.exp(-8 * t / max(dur, 0.01))
        return signal * envelope

    def _gen_sparkle(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """High-frequency sparkle/chime effect."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        freqs = [800, 1200, 1600, 2000, 2400]
        signal = np.zeros(len(t), dtype=np.float32)
        for i, freq in enumerate(freqs[:int(1 + intensity * 4)]):
            phase = i * 0.3
            signal += np.sin(2 * math.pi * freq * (t + phase)) * 0.2
        envelope = np.exp(-4 * t / max(dur, 0.01))
        return signal * envelope

    def _gen_wind(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """Wind-like filtered noise."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        noise = np.random.randn(len(t)).astype(np.float32)
        # Slowly varying amplitude
        mod = 0.5 + 0.5 * np.sin(2 * math.pi * 0.3 * t)
        envelope = np.exp(-0.5 * t / max(dur, 0.01))
        return noise * mod * intensity * 0.3 * envelope

    def _gen_rain(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """Rain-like white noise."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        noise = np.random.randn(len(t)).astype(np.float32)
        # High-pass character
        mod = 0.7 + 0.3 * np.sin(2 * math.pi * 2 * t)
        return noise * mod * intensity * 0.2

    def _gen_thunder(self, dur: float, intensity: float, sr: int) -> np.ndarray:
        """Low rumbling thunder."""
        t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
        noise = np.random.randn(len(t)).astype(np.float32)
        # Low frequency rumble
        signal = noise * 0.3 + np.sin(2 * math.pi * 30 * t) * 0.7
        # Slow roll
        envelope = np.exp(-2 * t / max(dur, 0.01))
        return signal * envelope * intensity


sfx_service = SFXService()
