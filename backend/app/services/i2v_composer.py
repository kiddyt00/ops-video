"""
Wan2.7 i2v Video Composer

Generates one i2v animated clip, then adds TTS narration + BGM.
"""
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings, STORAGE_DIRS
from ..providers.wan_video_provider import wan_video_provider


class I2VComposer:
    """i2v generation + audio mixing."""

    def __init__(self):
        self.video_dir = STORAGE_DIRS["video"]
        self.video_dir.mkdir(parents=True, exist_ok=True)

    async def compose(
        self,
        panels: List[Dict[str, Any]],
        bgm_path: Optional[Path] = None,
        resolution: tuple = (1080, 1920),
        fps: int = 24,
        storyboard_panels: Optional[List[Dict]] = None,
    ) -> Path:
        """Generate i2v clip from first image, then mix with TTS audio."""

        # Step 1: Generate one i2v clip
        i2v_clip = None
        if panels:
            p = panels[0]
            img = p.get("image_path", "")
            sb = storyboard_panels or []
            prompt = sb[0].get("scene_description", "让画面动起来")[:200] if sb else "让画面动起来"

            if img and Path(img).exists():
                result = await wan_video_provider.generate({
                    "image_path": img,
                    "prompt": prompt,
                    "duration": 5,
                    "output_filename": "clip_i2v.mp4",
                })
                if result.success and result.file_paths:
                    i2v_clip = result.file_paths[0]

        if not i2v_clip:
            # Fallback: still frame from first image
            i2v_clip = self._make_still(
                panels[0].get("image_path", "") if panels else "",
                duration=5, resolution=resolution, fps=fps,
            )

        # Step 2: Collect TTS audio files (from panels)
        import tempfile
        tts_files = []
        for panel in panels:
            ap = panel.get("audio_path", "")
            if ap and Path(ap).exists():
                tts_files.append(Path(ap))

        # Step 3: Mix audio tracks into video
        ts = int(time.time())
        output = self.video_dir / f"final_i2v_{ts}.mp4"

        # Build ffmpeg command
        cmd = ["ffmpeg", "-y", "-i", str(i2v_clip)]

        # Add TTS audio inputs
        for tf in tts_files:
            cmd.extend(["-i", str(tf)])

        # Add BGM
        has_bgm = bgm_path and bgm_path.exists()
        if has_bgm:
            cmd.extend(["-i", str(bgm_path)])

        # Build filter: mix all audio tracks
        audio_inputs = len(tts_files) + (1 if has_bgm else 0)
        if audio_inputs > 0:
            # Mix all audio inputs into one track
            amix_inputs = "".join(f"[{i+1}:a]" for i in range(audio_inputs))
            afilter = f"{amix_inputs}amix=inputs={audio_inputs}:duration=first:dropout_transition=0[audio]"
            cmd.extend([
                "-filter_complex", afilter,
                "-map", "0:v",
                "-map", "[audio]",
            ])
        else:
            cmd.extend(["-map", "0:v", "-map", "0:a?"])

        cmd.extend([
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps),
            "-movflags", "+faststart",
            "-shortest",
            str(output),
        ])

        subprocess.run(cmd, check=True, capture_output=True)
        return output

    def _make_still(self, img_path: str, duration: float, resolution: tuple, fps: int) -> Path:
        """Still frame fallback."""
        ts = int(time.time())
        out = self.video_dir / f"still_{ts}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-c:v", "libx264", "-t", str(duration),
            "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps), "-pix_fmt", "yuv420p", str(out),
        ], check=True, capture_output=True)
        return out


i2v_composer = I2VComposer()
