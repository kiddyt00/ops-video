"""
Video Synthesis Service

Combines images, audio (TTS + BGM + SFX), and storyboard timing
into a final video using FFmpeg.
"""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

from ..config import settings, STORAGE_DIRS


class VideoSynthesisService:
    """
    Composes a final video from:
    - Storyboard panel images
    - TTS audio (narration per panel)
    - BGM (background music)
    - SFX (sound effects per panel)
    - Panel durations from storyboard data

    Uses FFmpeg for all audio/video processing.
    """

    VIDEO_DIR = STORAGE_DIRS["video"]

    def __init__(self):
        self.video_dir = self.VIDEO_DIR
        self.video_dir.mkdir(parents=True, exist_ok=True)

    def compose(
        self,
        panels: list[dict],
        output_filename: Optional[str] = None,
        bgm_path: Optional[Path] = None,
        resolution: tuple[int, int] = (1080, 1920),  # 9:16 vertical
        fps: int = 24,
        transition: str = "fade",
        transition_duration: float = 0.5,
    ) -> Path:
        """
        Compose a video from storyboard panels with audio.

        Args:
            panels: List of dicts with:
                - image_path: Path to the panel image
                - audio_path: Path to the TTS audio for this panel (optional)
                - sfx_path: Path to the SFX for this panel (optional)
                - duration: Duration to show this panel in seconds
                - text: Narration text (for metadata)
            output_filename: Output MP4 filename
            bgm_path: Path to background music file
            resolution: Video resolution (width, height)
            fps: Frames per second
            transition: Transition type between panels
            transition_duration: Transition duration in seconds

        Returns:
            Path to the composed video file
        """
        import time
        if output_filename is None:
            output_filename = f"video_{int(time.time())}.mp4"

        output_path = self.video_dir / output_filename

        if not panels:
            raise ValueError("No panels provided")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Step 1: Create individual panel video clips
            clip_paths = []
            for i, panel in enumerate(panels):
                image_path = panel.get("image_path")
                duration = panel.get("duration", 3.0)
                clip_path = tmp / f"clip_{i:03d}.mp4"
                self._create_still_clip(image_path, duration, resolution, fps, clip_path)
                clip_paths.append(clip_path)

            # Step 2: Concatenate clips with transitions
            concat_path = tmp / "concat.mp4"
            if len(clip_paths) == 1:
                concat_path = clip_paths[0]
            else:
                self._concat_clips(clip_paths, concat_path, transition, transition_duration)

            # Step 3: Mix audio tracks
            audio_paths = []
            for i, panel in enumerate(panels):
                if panel.get("audio_path") and Path(panel["audio_path"]).exists():
                    audio_paths.append(Path(panel["audio_path"]))
                if panel.get("sfx_path") and Path(panel["sfx_path"]).exists():
                    audio_paths.append(Path(panel["sfx_path"]))

            final_audio = None
            if audio_paths:
                # Calculate total video duration
                total_duration = sum(p.get("duration", 3.0) for p in panels)
                final_audio = self._mix_audio(audio_paths, bgm_path, total_duration, tmp)

            # Step 4: Combine video and audio
            self._combine_audio_video(concat_path, final_audio, output_path, fps)

        return output_path

    def _create_still_clip(
        self,
        image_path: str | Path,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
        output_path: Path,
    ):
        """Create a video clip from a still image with the given duration."""
        width, height = resolution
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path),
        ]
        self._run_ffmpeg(cmd)

    def _concat_clips(
        self,
        clip_paths: list[Path],
        output_path: Path,
        transition: str = "fade",
        transition_duration: float = 0.5,
    ):
        """Concatenate clips using FFmpeg's concat demuxer."""
        concat_file = output_path.with_suffix(".txt")
        with open(concat_file, "w") as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path),
        ]
        self._run_ffmpeg(cmd)
        concat_file.unlink(missing_ok=True)

    def _mix_audio(
        self,
        audio_paths: list[Path],
        bgm_path: Optional[Path],
        total_duration: float,
        tmpdir: Path,
    ) -> Optional[Path]:
        """Mix multiple audio tracks together with background music."""
        if not audio_paths and not bgm_path:
            return None

        output_path = tmpdir / "mixed_audio.wav"

        # Build FFmpeg filter for mixing multiple inputs
        inputs = []
        for ap in audio_paths:
            inputs.extend(["-i", str(ap)])
        if bgm_path and bgm_path.exists():
            inputs.extend(["-i", str(bgm_path)])

        # Simple approach: concatenate sequential audio with amix
        # For now, just use the first audio track as primary
        primary = audio_paths[0] if audio_paths else bgm_path
        if not primary or not Path(primary).exists():
            return None

        if bgm_path and bgm_path.exists() and len(audio_paths) > 0:
            # Mix primary audio with BGM at lower volume
            cmd = [
                "ffmpeg", "-y",
                "-i", str(primary),
                "-i", str(bgm_path),
                "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.15[a1];[a0][a1]amix=inputs=2:duration=longest",
                "-t", str(total_duration),
                str(output_path),
            ]
            self._run_ffmpeg(cmd)
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(primary),
                "-t", str(total_duration),
                str(output_path),
            ]
            self._run_ffmpeg(cmd)

        return output_path

    def _combine_audio_video(
        self,
        video_path: Path,
        audio_path: Optional[Path],
        output_path: Path,
        fps: int = 24,
    ):
        """Combine a video track with an audio track."""
        if audio_path and audio_path.exists():
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(output_path),
            ]
        else:
            # No audio, just copy video
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-c:v", "copy",
                str(output_path),
            ]
        self._run_ffmpeg(cmd)

    def _run_ffmpeg(self, cmd: list[str]):
        """Run FFmpeg command and raise on failure."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")


video_synthesis_service = VideoSynthesisService()
