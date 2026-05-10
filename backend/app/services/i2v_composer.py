"""
Wan2.7 i2v Video Composer

Replaces FFmpeg static composition with AI-animated clips.
"""
import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings, STORAGE_DIRS
from ..providers.wan_video_provider import wan_video_provider


class I2VComposer:
    """Generates animated video clips via Wan2.7 i2v, then stitches with FFmpeg."""

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
        """
        Compose final video:
        1. Generate i2v clips for each panel image
        2. Concat all clips + add audio
        """
        sb = storyboard_panels or []

        # Step 1: Generate i2v animated clips
        clip_paths = []
        for i, panel in enumerate(panels):
            img_path = panel.get("image_path", "")
            if not img_path or not Path(img_path).exists():
                continue

            # Build prompt from storyboard
            prompt = "让画面动起来"
            if i < len(sb):
                desc = sb[i].get("scene_description", "")
                if desc:
                    prompt = desc[:200]  # keep reasonable length

            result = await wan_video_provider.generate({
                "image_path": img_path,
                "prompt": prompt,
                "output_filename": f"clip_{i:03d}.mp4",
            })

            if result.success and result.file_paths:
                clip_paths.append(result.file_paths[0])
            else:
                print(f"[i2v] Panel {i} failed: {result.error_message}, falling back to still")
                clip_paths.append(None)

        # Step 2: Build FFmpeg concat + audio
        return self._ffmpeg_concat(clip_paths, panels, bgm_path, resolution, fps)

    def _ffmpeg_concat(
        self,
        clip_paths: List[Optional[Path]],
        panels: List[Dict[str, Any]],
        bgm_path: Optional[Path],
        resolution: tuple,
        fps: int,
    ) -> Path:
        """Concat clips with FFmpeg, add audio, output final MP4."""
        import tempfile

        ts = int(time.time())
        output_path = self.video_dir / f"final_i2v_{ts}.mp4"

        # Build concat file
        concat_list = []
        for i, clip in enumerate(clip_paths):
            if clip and clip.exists():
                concat_list.append(f"file '{clip}'")
            elif i < len(panels):
                # Fallback: generate a still frame video from the image
                still = self._make_still(panels[i].get("image_path", ""), panels[i].get("duration", 3.0), resolution, fps, i)
                if still:
                    concat_list.append(f"file '{still}'")

        if not concat_list:
            raise RuntimeError("No clips to compose")

        concat_file = self.video_dir / f"concat_{ts}.txt"
        concat_file.write_text("\n".join(concat_list))

        # Build ffmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
        ]

        # Add audio
        audio_inputs = []
        for i, panel in enumerate(panels):
            audio_path = panel.get("audio_path")
            if audio_path and Path(audio_path).exists():
                audio_inputs.extend(["-i", audio_path])

        if bgm_path and bgm_path.exists():
            audio_inputs.extend(["-i", str(bgm_path)])

        if audio_inputs:
            cmd.extend(audio_inputs)

        cmd.extend([
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps),
            "-movflags", "+faststart",
            str(output_path),
        ])

        subprocess.run(cmd, check=True, capture_output=True)

        # Cleanup
        concat_file.unlink(missing_ok=True)

        return output_path

    def _make_still(
        self,
        img_path: str,
        duration: float,
        resolution: tuple,
        fps: int,
        index: int,
    ) -> Optional[Path]:
        """Create a still-frame video from an image (fallback if i2v fails)."""
        if not img_path or not Path(img_path).exists():
            return None

        ts = int(time.time())
        output = self.video_dir / f"still_{index:03d}_{ts}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-c:v", "libx264", "-t", str(duration),
            "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps), "-pix_fmt", "yuv420p",
            str(output),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output


i2v_composer = I2VComposer()
