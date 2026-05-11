"""
Wan2.7 i2v Video Composer — Multi-Clip Episode Engine

Generates i2v clips per storyboard panel, concatenates with crossfade
transitions, and mixes TTS narration + BGM + SFX into a final video.
"""
import asyncio
import logging
import os
import subprocess
import tempfile
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings, STORAGE_DIRS
from ..providers.wan_video_provider import wan_video_provider

logger = logging.getLogger(__name__)


class I2VComposer:
    """Multi-panel i2v generation, concatenation, and audio mixing."""

    def __init__(self):
        self.video_dir = STORAGE_DIRS["video"]
        self.video_dir.mkdir(parents=True, exist_ok=True)

    # ─── Deprecated: original single-panel compose ──────────────────

    async def compose(
        self,
        panels: List[Dict[str, Any]],
        bgm_path: Optional[Path] = None,
        resolution: tuple = (1080, 1920),
        fps: int = 24,
        storyboard_panels: Optional[List[Dict]] = None,
    ) -> Path:
        """Generate i2v clip from first image, then mix with TTS audio.

        DEPRECATED: Use compose_episode() for multi-panel support.
        """
        warnings.warn(
            "I2VComposer.compose() is deprecated; use compose_episode() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

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
            i2v_clip = self._make_still(
                panels[0].get("image_path", "") if panels else "",
                duration=5, resolution=resolution, fps=fps,
            )

        import tempfile
        tts_files = []
        for panel in panels:
            ap = panel.get("audio_path", "")
            if ap and Path(ap).exists():
                tts_files.append(Path(ap))

        ts = int(time.time())
        output = self.video_dir / f"final_i2v_{ts}.mp4"

        cmd = ["ffmpeg", "-y", "-i", str(i2v_clip)]
        for tf in tts_files:
            cmd.extend(["-i", str(tf)])

        has_bgm = bgm_path and bgm_path.exists()
        if has_bgm:
            cmd.extend(["-i", str(bgm_path)])

        audio_inputs = len(tts_files) + (1 if has_bgm else 0)
        if audio_inputs > 0:
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

        self._run_ffmpeg(cmd)
        return output

    # ─── New: multi-panel episode composition ───────────────────────

    async def compose_episode(
        self,
        panels: List[Dict[str, Any]],
        storyboard: Dict[str, Any],
        bgm_path: Optional[Path] = None,
        tts_paths: Optional[List[Path]] = None,
        sfx_paths: Optional[List[Path]] = None,
        resolution: tuple = (1080, 1920),
        fps: int = 24,
    ) -> Path:
        """Generate a full episode video from multiple storyboard panels.

        Workflow:
          1. For each panel, call wan_video_provider.generate() to create a clip.
          2. Concat all clips with crossfade transitions.
          3. Mix audio: TTS aligned to panels + BGM + SFX.
          4. Return final video path.

        Args:
            panels: List of dicts with at least image_path per panel.
            storyboard: Storyboard dict with 'panels' key, each having
                        scene_description and duration.
            bgm_path: Optional background music path.
            tts_paths: Optional list of TTS audio paths, one per panel.
            sfx_paths: Optional list of SFX audio paths, one per panel.
            resolution: Video (width, height).
            fps: Frames per second.

        Returns:
            Path to the final composed MP4.
        """
        ts = int(time.time())

        sb_panels = storyboard.get("panels", [])

        # Step 1: Generate a clip per panel
        clips: List[Path] = []
        for i, panel in enumerate(panels):
            sb_panel = sb_panels[i] if i < len(sb_panels) else {}
            target_duration = sb_panel.get("duration", 5)
            clip_path = await self._generate_panel_clip(panel, sb_panel, target_duration)
            clips.append(clip_path)
            logger.info("Panel %d clip: %s", i, clip_path)

        # Step 2: Concat clips with crossfade transitions
        with tempfile.TemporaryDirectory(dir=os.path.expanduser("~")) as tmpdir:
            tmp = Path(tmpdir)
            video_concat = tmp / "video_concat.mp4"

            if len(clips) == 1:
                # No transition needed for single clip
                video_concat = clips[0]
            else:
                video_concat = await self._concat_clips_with_transition(
                    clips, transition="crossfade", duration=0.5
                )

            # Step 3: Mix audio
            video_with_audio = tmp / "video_with_audio.mp4"

            # Calculate total video duration for BGM
            total_duration = sum(sb_panels[i].get("duration", 5) for i in range(len(panels)))

            final_video = await self._mix_audio(
                video_concat,
                bgm_path=bgm_path,
                tts_paths=tts_paths,
                sfx_paths=sfx_paths,
                total_duration=total_duration,
                output_path=self.video_dir / f"episode_{ts}.mp4",
            )

        return final_video

    async def _generate_panel_clip(
        self,
        panel: Dict[str, Any],
        storyboard_panel: Dict[str, Any],
        target_duration: float = 5.0,
    ) -> Path:
        """Generate a single panel clip via wan_video_provider.

        Falls back to a still-frame video if i2v generation fails.

        Args:
            panel: Panel dict with 'image_path'.
            storyboard_panel: Storyboard panel dict with 'scene_description'.
            target_duration: Desired clip duration in seconds.

        Returns:
            Path to the generated clip.
        """
        img_path = panel.get("image_path", "")
        prompt = storyboard_panel.get("scene_description", "让画面动起来")[:200]

        clip_filename = f"panel_clip_{int(time.time()*1000)}.mp4"

        if img_path and Path(img_path).exists():
            try:
                result = await wan_video_provider.generate({
                    "image_path": img_path,
                    "prompt": prompt,
                    "duration": target_duration,
                    "output_filename": clip_filename,
                })
                if result.success and result.file_paths:
                    return result.file_paths[0]
            except Exception as e:
                logger.warning("Wan i2v generation failed for panel: %s", e)

        # Fallback: still frame
        logger.info("Falling back to still frame for panel")
        return self._make_still(img_path, duration=target_duration)

    async def _extend_panel_clip(
        self,
        prev_clip_path: Path,
        storyboard_panel: Dict[str, Any],
        target_duration: float = 5.0,
        index: int = 0,
    ) -> Path:
        """Extend from a previous clip using tail-frame continuation.

        Args:
            prev_clip_path: Path to the previous clip to extend from.
            storyboard_panel: Storyboard panel dict with 'scene_description'.
            target_duration: Desired clip duration in seconds.
            index: Panel index (for filename).

        Returns:
            Path to the generated clip, or fallback still on failure.
        """
        prompt = storyboard_panel.get("scene_description", "让画面动起来")[:200]
        clip_filename = f"panel_extend_{index}_{int(time.time()*1000)}.mp4"

        try:
            result = await wan_video_provider.extend(
                prev_clip_path=prev_clip_path,
                prompt=prompt,
                duration=int(target_duration),
                output_filename=clip_filename,
            )
            if result.success and result.file_paths:
                return result.file_paths[0]
        except Exception as e:
            logger.warning("Wan i2v extend failed for panel %d: %s", index, e)

        # Fallback: still frame
        img_path = ""  # no image for extend fallback
        logger.info("Falling back to still frame for extend panel %d", index)
        return self._make_still(img_path, duration=target_duration)

    # ─── Scene-aware tail-frame chain ───────────────────────────────

    @staticmethod
    def group_panels_by_scene(
        panels: List[Dict[str, Any]],
        storyboard_panels: List[Dict[str, Any]],
    ) -> List[List[tuple]]:
        """Group panels into scene groups based on scene_id.

        If scene_id is not present in storyboard panels, treats all panels
        as a single continuous scene.

        Args:
            panels: Panel dicts with image_path.
            storyboard_panels: Storyboard panel dicts possibly with scene_id.

        Returns:
            List of scene groups. Each group is a list of (panel_index, panel, storyboard_panel) tuples.
        """
        if not panels:
            return []

        # Check if any storyboard panel has scene_id
        has_scene_ids = any("scene_id" in sp for sp in storyboard_panels)

        if not has_scene_ids:
            # No scene_id: treat all as one continuous scene
            return [[(i, panels[i], storyboard_panels[i] if i < len(storyboard_panels) else {})
                     for i in range(len(panels))]]

        # Group by scene_id
        groups: Dict[Any, List[tuple]] = {}
        order: List[Any] = []

        for i in range(len(panels)):
            sb = storyboard_panels[i] if i < len(storyboard_panels) else {}
            scene_id = sb.get("scene_id", f"default_{i}")

            if scene_id not in groups:
                groups[scene_id] = []
                order.append(scene_id)
            groups[scene_id].append((i, panels[i], sb))

        return [groups[sid] for sid in order]

    async def compose_episode_with_tail_extend(
        self,
        panels: List[Dict[str, Any]],
        storyboard: Dict[str, Any],
        bgm_path: Optional[Path] = None,
        tts_paths: Optional[List[Path]] = None,
        sfx_paths: Optional[List[Path]] = None,
        resolution: tuple = (1080, 1920),
        fps: int = 24,
    ) -> Path:
        """Generate a full episode using tail-frame continuation within scenes.

        Workflow:
          1. Group panels by scene_id (or treat all as one scene).
          2. For each scene: first panel uses generate(), subsequent panels use extend().
          3. Concat all clips with crossfade transitions.
          4. Mix audio: TTS + BGM + SFX.
          5. Return final video path.

        Args:
            panels: List of dicts with at least image_path per panel.
            storyboard: Storyboard dict with 'panels' key.
            bgm_path: Optional background music path.
            tts_paths: Optional list of TTS audio paths, one per panel.
            sfx_paths: Optional list of SFX audio paths, one per panel.
            resolution: Video (width, height).
            fps: Frames per second.

        Returns:
            Path to the final composed MP4.
        """
        ts = int(time.time())
        sb_panels = storyboard.get("panels", [])

        # Step 1: Group panels by scene
        scene_groups = self.group_panels_by_scene(panels, sb_panels)
        logger.info("Tail-extend composer: %d scene group(s) detected", len(scene_groups))

        # Step 2: Generate clips per scene
        all_clips: List[Path] = []
        panel_durations: List[float] = []

        for group_idx, group in enumerate(scene_groups):
            prev_clip: Optional[Path] = None

            for local_idx, (global_idx, panel, sb_panel) in enumerate(group):
                target_duration = sb_panel.get("duration", 5)
                panel_durations.append(target_duration)

                if local_idx == 0:
                    # First panel in scene: generate from image
                    clip_path = await self._generate_panel_clip(panel, sb_panel, target_duration)
                else:
                    # Subsequent panel in same scene: extend from previous clip
                    if prev_clip and prev_clip.exists():
                        clip_path = await self._extend_panel_clip(
                            prev_clip_path=prev_clip,
                            storyboard_panel=sb_panel,
                            target_duration=target_duration,
                            index=global_idx,
                        )
                    else:
                        # Fallback: generate from image if prev clip unavailable
                        logger.warning(
                            "Previous clip unavailable for extend at panel %d, falling back to generate",
                            global_idx,
                        )
                        clip_path = await self._generate_panel_clip(panel, sb_panel, target_duration)

                all_clips.append(clip_path)
                prev_clip = clip_path
                logger.info("Scene %d, Panel %d clip: %s", group_idx, global_idx, clip_path)

        # Step 3: Concat clips with crossfade transitions
        with tempfile.TemporaryDirectory(dir=os.path.expanduser("~")) as tmpdir:
            tmp = Path(tmpdir)

            if len(all_clips) == 1:
                video_concat = all_clips[0]
            else:
                video_concat = await self._concat_clips_with_transition(
                    all_clips, transition="crossfade", duration=0.5
                )

            # Step 4: Mix audio
            total_duration = sum(panel_durations)

            final_video = await self._mix_audio(
                video_concat,
                bgm_path=bgm_path,
                tts_paths=tts_paths,
                sfx_paths=sfx_paths,
                total_duration=total_duration,
                output_path=self.video_dir / f"episode_tail_ext_{ts}.mp4",
            )

        return final_video

    async def _concat_clips_with_transition(
        self,
        clips: List[Path],
        transition: str = "crossfade",
        duration: float = 0.5,
    ) -> Path:
        """Concatenate multiple clips with crossfade transitions.

        Uses FFmpeg's xfade filter for smooth transitions between clips.

        Args:
            clips: List of clip paths to concatenate.
            transition: Transition type ('crossfade' or 'fade').
            duration: Transition duration in seconds.

        Returns:
            Path to the concatenated video.
        """
        if len(clips) < 2:
            return clips[0] if clips else None

        ts = int(time.time() * 1000)
        output = self.video_dir / f"concat_xfade_{ts}.mp4"

        # Get duration of each clip for offset calculation
        clip_durations = []
        for clip in clips:
            dur = self._get_video_duration(clip)
            clip_durations.append(dur)

        # Build xfade filter chain
        # For N clips, we need N-1 xfade filters chained together
        inputs = []
        for clip in clips:
            inputs.extend(["-i", str(clip)])

        # Build the xfade filter graph
        offsets = []
        cumulative = clip_durations[0]

        for i in range(len(clips) - 1):
            offset = cumulative - duration
            offsets.append(offset)
            cumulative += clip_durations[i + 1] - duration

        if transition == "crossfade":
            xfade_transition = "fade"
        else:
            xfade_transition = transition

        # Build chained filter
        if len(clips) == 2:
            filter_str = (
                f"[0:v][1:v]xfade=transition={xfade_transition}:"
                f"duration={duration}:offset={offsets[0]}[vout];"
                f"[0:a][1:a]acrossfade=d={duration}:c1=tri:c2=tri[aout]"
            )
        else:
            # Multi-clip: chain xfades
            parts = []
            audio_parts = []
            for i in range(len(clips) - 1):
                if i == 0:
                    src_a = "[0:v]"
                    src_b = "[1:v]"
                    src_aud_a = "[0:a]"
                    src_aud_b = "[1:a]"
                else:
                    src_a = f"[v{i-1}]"
                    src_b = f"[{i+1}:v]"
                    src_aud_a = f"[a{i-1}]"
                    src_aud_b = f"[{i+1}:a]"

                if i == len(clips) - 2:
                    dst_v = "[vout]"
                    dst_a = "[aout]"
                else:
                    dst_v = f"[v{i}]"
                    dst_a = f"[a{i}]"

                parts.append(
                    f"{src_a}{src_b}xfade=transition={xfade_transition}:"
                    f"duration={duration}:offset={offsets[i]}{dst_v}"
                )
                audio_parts.append(
                    f"{src_aud_a}{src_aud_b}acrossfade=d={duration}:"
                    f"c1=tri:c2=tri{dst_a}"
                )

            filter_str = ";".join(parts + audio_parts)

        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "none",
        ] + inputs + [
            "-filter_complex", filter_str,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output),
        ]

        self._run_ffmpeg(cmd)
        return output

    async def _mix_audio(
        self,
        video_path: Path,
        bgm_path: Optional[Path] = None,
        tts_paths: Optional[List[Path]] = None,
        sfx_paths: Optional[List[Path]] = None,
        total_duration: float = 0,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Mix audio tracks (TTS + BGM + SFX) onto a video.

        TTS audio is aligned sequentially to each panel's time segment.
        BGM loops to fill total duration at low volume.
        SFX are placed at the start of their respective panel segments.

        Args:
            video_path: Path to the video to add audio to.
            bgm_path: Optional background music file.
            tts_paths: Optional list of TTS audio files (one per panel).
            sfx_paths: Optional list of SFX audio files (one per panel).
            total_duration: Total video duration for BGM looping.
            output_path: Output path. If None, generates one.

        Returns:
            Path to the final video with mixed audio.
        """
        if output_path is None:
            output_path = self.video_dir / f"mixed_{int(time.time())}.mp4"

        has_tts = tts_paths and any(p and Path(p).exists() for p in tts_paths)
        has_bgm = bgm_path and bgm_path.exists()
        has_sfx = sfx_paths and any(p and Path(p).exists() for p in sfx_paths)

        if not has_tts and not has_bgm and not has_sfx:
            # No audio to mix, just copy video
            cmd = [
                "ffmpeg", "-y",
                "-hwaccel", "none",
                "-i", str(video_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                str(output_path),
            ]
            self._run_ffmpeg(cmd)
            return output_path

        with tempfile.TemporaryDirectory(dir=os.path.expanduser("~")) as tmpdir:
            tmp = Path(tmpdir)
            mixed_audio = tmp / "mixed_audio.wav"

            # Collect all audio inputs and build filter graph
            audio_inputs: List[Path] = []
            filter_parts: List[str] = []
            input_idx = 1  # 0 is reserved for video

            # --- TTS: concatenate sequentially (adelay for alignment) ---
            if has_tts:
                valid_tts = [p for p in tts_paths if p and Path(p).exists()]
                if valid_tts:
                    # Add TTS inputs
                    for tp in valid_tts:
                        audio_inputs.append(tp)

                    # Build concat filter for sequential TTS
                    tts_labels = []
                    for i in range(len(valid_tts)):
                        idx = input_idx + i
                        tts_labels.append(f"[{idx}:a]")

                    concat_label = "[tts]"
                    concat_str = "".join(tts_labels) + f"concat=n={len(valid_tts)}:v=0:a=1{concat_label}"
                    filter_parts.append(concat_str)
                    input_idx += len(valid_tts)

            # --- BGM: loop to fill duration at low volume ---
            if has_bgm:
                audio_inputs.append(bgm_path)
                bgm_idx = input_idx
                filter_parts.append(
                    f"[{bgm_idx}:a]aloop=loop=-1:size=2e+09,atrim=0:{total_duration},"
                    f"volume=0.15[bgm]"
                )
                input_idx += 1

            # --- SFX: align each SFX to its panel start time ---
            if has_sfx:
                valid_sfx = [(i, p) for i, p in enumerate(sfx_paths) if p and Path(p).exists()]
                if valid_sfx:
                    for panel_idx, sfx_path in valid_sfx:
                        audio_inputs.append(sfx_path)
                        sfx_idx = input_idx

                        # Calculate offset based on panel durations
                        # Simplified: we use adelay to position each SFX
                        # For now, just add them and amix at the end
                        filter_parts.append(f"[{sfx_idx}:a]volume=0.8[sfx{panel_idx}]")
                        input_idx += 1

            # --- Final amix ---
            mix_sources = []
            if has_tts and any(p and Path(p).exists() for p in tts_paths):
                mix_sources.append("[tts]")
            if has_bgm:
                mix_sources.append("[bgm]")
            if has_sfx:
                valid_sfx = [i for i, p in enumerate(sfx_paths) if p and Path(p).exists()]
                for panel_idx in valid_sfx:
                    mix_sources.append(f"[sfx{panel_idx}]")

            if len(mix_sources) > 1:
                mix_labels = "".join(mix_sources)
                filter_parts.append(
                    f"{mix_labels}amix=inputs={len(mix_sources)}:"
                    f"duration=longest:dropout_transition=0[out]"
                )
                map_audio = "[out]"
            elif len(mix_sources) == 1:
                map_audio = mix_sources[0]
            else:
                # Fallback: just use video's audio
                cmd = [
                    "ffmpeg", "-y",
                    "-hwaccel", "none",
                    "-i", str(video_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    str(output_path),
                ]
                self._run_ffmpeg(cmd)
                return output_path

            # Build full command
            filter_complex = ";".join(filter_parts)
            cmd = [
                "ffmpeg", "-y",
                "-hwaccel", "none",
                "-i", str(video_path),
            ]
            for ai in audio_inputs:
                cmd.extend(["-i", str(ai)])
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", map_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(output_path),
            ])

            self._run_ffmpeg(cmd)
            return output_path

    # ─── Helpers ──────────────────────────────────────────────────────

    def _make_still(self, img_path: str, duration: float, resolution: tuple = (1080, 1920), fps: int = 24) -> Path:
        """Create a still-frame video from an image."""
        ts = int(time.time())
        out = self.video_dir / f"still_{ts}.mp4"
        width, height = resolution
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "none",
            "-loop", "1",
            "-i", img_path,
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
            str(out),
        ]
        self._run_ffmpeg(cmd)
        return out

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using ffmpeg (ffprobe may not be installed)."""
        cmd = [
            "ffmpeg", "-i", str(video_path),
        ]
        env = self._get_ffmpeg_env()
        # ffmpeg prints duration to stderr, parse it
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        # Parse duration from stderr output like "Duration: 00:00:05.00, start: ..."
        import re
        match = re.search(r"Duration:\s+(\d{2}):(\d{2}):(\d{2})\.(\d+)", result.stderr)
        if match:
            h, m, s, frac = match.groups()
            total = int(h) * 3600 + int(m) * 60 + int(s) + int(frac.ljust(2, "0")[:2]) / 100
            return total
        return 5.0  # default fallback

    def _run_ffmpeg(self, cmd: list):
        """Run FFmpeg command with proper environment."""
        env = self._get_ffmpeg_env()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return result

    def _get_ffmpeg_env(self) -> dict:
        """Get environment dict for FFmpeg commands."""
        env = os.environ.copy()
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env.pop("DISPLAY", None)
        # snap ffmpeg can't write to /tmp, redirect to home dir
        home = os.path.expanduser("~")
        env["TMPDIR"] = home
        env["TEMP"] = home
        env["TMP"] = home
        return env


i2v_composer = I2VComposer()
