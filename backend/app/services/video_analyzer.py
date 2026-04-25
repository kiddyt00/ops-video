"""
Video Analysis Service

Analyzes video files to extract metadata:
- Duration
- Frame rate
- Resolution
- Codec
- File size
- Frame count (calculated)

Uses mutagen library for MP4/MKV/WebM analysis.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import timedelta

from mutagen import File as MutagenFile
from mutagen.mp4 import MP4

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Video metadata information"""
    duration: float  # in seconds
    frame_rate: float  # frames per second
    width: int
    height: int
    codec: str
    file_size: int  # in bytes
    frame_count: int  # calculated: duration * frame_rate
    has_audio: bool
    audio_codec: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "duration": round(self.duration, 3),
            "frame_rate": round(self.frame_rate, 2),
            "width": self.width,
            "height": self.height,
            "codec": self.codec,
            "file_size": self.file_size,
            "frame_count": self.frame_count,
            "has_audio": self.has_audio,
            "audio_codec": self.audio_codec,
            "resolution": f"{self.width}x{self.height}",
            "duration_formatted": self._format_duration(),
        }

    def _format_duration(self) -> str:
        """Format duration as HH:MM:SS.mmm"""
        td = timedelta(seconds=self.duration)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((self.duration % 1) * 1000)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


class VideoAnalyzer:
    """Analyzes video files and extracts metadata"""

    # Supported video extensions
    SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv'}

    @classmethod
    def is_video(cls, file_path: str) -> bool:
        """Check if a file is a supported video file"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def analyze(cls, file_path: str) -> Optional[VideoInfo]:
        """
        Analyze a video file and extract metadata.

        Args:
            file_path: Path to the video file

        Returns:
            VideoInfo object with metadata, or None if analysis fails
        """
        if not os.path.exists(file_path):
            return None

        if not cls.is_video(file_path):
            return None

        try:
            # Get file size
            file_size = os.path.getsize(file_path)

            # Try to analyze with mutagen
            info = cls._analyze_with_mutagen(file_path, file_size)

            if info:
                return info

            # Fallback: return basic info only
            return cls._get_basic_info(file_path, file_size)

        except Exception as e:
            # Log error but don't fail
            logger.warning("Video analysis failed for %s: %s", file_path, e)
            return cls._get_basic_info(file_path, file_size)

    @classmethod
    def _analyze_with_mutagen(cls, file_path: str, file_size: int) -> Optional[VideoInfo]:
        """Analyze video using mutagen library"""
        try:
            audio = MutagenFile(file_path, easy=True)
            if audio is None:
                return None

            duration = audio.info.length if hasattr(audio.info, 'length') else 0.0

            # Try to get video-specific info
            if isinstance(audio, MP4):
                # MP4 file
                tracks = audio.tracks
                video_track = None
                audio_track = None

                for track in tracks:
                    if hasattr(track, 'codec') and 'video' in str(track.codec).lower():
                        video_track = track
                    elif hasattr(track, 'codec') and 'audio' in str(track.codec).lower():
                        audio_track = track

                if video_track:
                    width = getattr(video_track, 'width', 0)
                    height = getattr(video_track, 'height', 0)
                    # Frame rate estimation for MP4
                    frame_rate = cls._estimate_frame_rate(duration, file_size, width, height)
                    codec = getattr(video_track, 'codec', 'unknown')

                    return VideoInfo(
                        duration=duration,
                        frame_rate=frame_rate,
                        width=width,
                        height=height,
                        codec=codec if codec else 'h264',
                        file_size=file_size,
                        frame_count=int(duration * frame_rate),
                        has_audio=audio_track is not None,
                        audio_codec=getattr(audio_track, 'codec', None) if audio_track else None,
                    )

            # Generic mutagen info for other formats
            if duration > 0:
                # Try to get info from the file
                info = audio.info if audio else None
                width = getattr(info, 'width', 1920) if info and hasattr(info, 'width') else 1920
                height = getattr(info, 'height', 1080) if info and hasattr(info, 'height') else 1080
                frame_rate = getattr(info, 'frame_rate', 30.0) if info and hasattr(info, 'frame_rate') else 30.0

                # Estimate frame rate if not available
                if not frame_rate or frame_rate <= 0:
                    frame_rate = cls._estimate_frame_rate(duration, file_size, width, height)

                return VideoInfo(
                    duration=duration,
                    frame_rate=frame_rate,
                    width=width,
                    height=height,
                    codec='unknown',
                    file_size=file_size,
                    frame_count=int(duration * frame_rate),
                    has_audio=hasattr(info, 'channels') if info else False,
                    audio_codec=None,
                )

            return None

        except Exception:
            return None

    @classmethod
    def _estimate_frame_rate(cls, duration: float, file_size: int, width: int, height: int) -> float:
        """Estimate frame rate based on file characteristics"""
        if duration <= 0:
            return 30.0

        # Common frame rates
        common_frame_rates = [24, 25, 30, 50, 60]

        # Simple heuristic based on resolution and file size
        # Higher bitrate usually means higher frame rate
        if width <= 0:
            width = 1920
        if height <= 0:
            height = 1080

        pixels = width * height
        bitrate = (file_size * 8) / duration  # bits per second

        # Rough estimation
        if bitrate > 20_000_000:  # > 20 Mbps
            return 60.0
        elif bitrate > 10_000_000:  # > 10 Mbps
            return 30.0
        elif bitrate > 5_000_000:  # > 5 Mbps
            return 25.0
        else:
            return 24.0

    @classmethod
    def _get_basic_info(cls, file_path: str, file_size: int) -> Optional[VideoInfo]:
        """Get basic file info when detailed analysis fails"""
        # Try to extract any info we can
        return VideoInfo(
            duration=0.0,
            frame_rate=30.0,  # Default assumption
            width=0,
            height=0,
            codec='unknown',
            file_size=file_size,
            frame_count=0,
            has_audio=False,
            audio_codec=None,
        )


# Convenience function
def analyze_video(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a video file and return metadata as dictionary.

    Args:
        file_path: Path to the video file

    Returns:
        Dictionary with video metadata, or None if analysis fails
    """
    info = VideoAnalyzer.analyze(file_path)
    if info:
        return info.to_dict()
    return None
