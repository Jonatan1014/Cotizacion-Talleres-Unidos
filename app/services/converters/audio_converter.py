"""
Audio Converter - Handles audio format conversions
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil
import subprocess

from app.services.base_converter import BaseConverter, ConversionResult


class AudioConverter(BaseConverter):
    """
    Converter for audio files.
    
    Uses FFmpeg for audio conversions.
    """
    
    @property
    def supported_input_formats(self) -> List[str]:
        return ["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "opus"]
    
    @property
    def supported_output_formats(self) -> List[str]:
        return ["mp3", "wav", "ogg", "flac", "aac", "m4a"]
    
    @property
    def category(self) -> str:
        return "audio"
    
    def _get_ffmpeg_path(self) -> Optional[str]:
        """Find FFmpeg executable path."""
        ffmpeg = shutil.which("ffmpeg")
        return ffmpeg
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionResult:
        """Convert audio from one format to another."""
        options = options or {}
        target_format = target_format.lower().lstrip('.')
        
        ffmpeg_path = self._get_ffmpeg_path()
        if not ffmpeg_path:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message="FFmpeg is not installed or not found in PATH"
            )
        
        try:
            result = await self._convert_with_ffmpeg(
                input_path,
                output_path,
                target_format,
                ffmpeg_path,
                options
            )
            return result
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message=str(e)
            )
    
    async def _convert_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        ffmpeg_path: str,
        options: Dict[str, Any]
    ) -> ConversionResult:
        """Convert using FFmpeg."""
        
        # Ensure output has correct extension
        output_path = output_path.with_suffix(f".{target_format}")
        
        # Build FFmpeg command
        cmd = [ffmpeg_path, "-i", str(input_path), "-y"]  # -y to overwrite
        
        # Add format-specific options
        bitrate = options.get("bitrate", "192k")
        sample_rate = options.get("sample_rate")
        channels = options.get("channels")
        
        if target_format == "mp3":
            cmd.extend(["-codec:a", "libmp3lame", "-b:a", bitrate])
        elif target_format == "ogg":
            cmd.extend(["-codec:a", "libvorbis", "-b:a", bitrate])
        elif target_format == "flac":
            cmd.extend(["-codec:a", "flac"])
        elif target_format == "wav":
            cmd.extend(["-codec:a", "pcm_s16le"])
        elif target_format == "aac":
            cmd.extend(["-codec:a", "aac", "-b:a", bitrate])
        elif target_format == "m4a":
            cmd.extend(["-codec:a", "aac", "-b:a", bitrate])
        
        # Optional sample rate
        if sample_rate:
            cmd.extend(["-ar", str(sample_rate)])
        
        # Optional channels
        if channels:
            cmd.extend(["-ac", str(channels)])
        
        # Output file
        cmd.append(str(output_path))
        
        # Run conversion
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message=f"FFmpeg conversion failed: {stderr.decode()}"
            )
        
        if output_path.exists():
            return ConversionResult(
                success=True,
                output_path=output_path,
                output_format=target_format,
                file_size=output_path.stat().st_size,
                metadata={
                    "bitrate": bitrate,
                    "sample_rate": sample_rate,
                    "channels": channels
                }
            )
        
        return ConversionResult(
            success=False,
            output_path=None,
            output_format=target_format,
            error_message="Output file not found after conversion"
        )
