"""
Audio extraction module for Video Caption Generator
Extracts audio from video files using ffmpeg
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, Union
import ffmpeg
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class AudioExtractor:
    """Extract audio from video files"""
    
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', 
        '.webm', '.m4v', '.mpg', '.mpeg', '.3gp'
    }
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize audio extractor
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_video_file(self, video_path: Union[str, Path]) -> Path:
        """
        Validate video file exists and has supported format
        
        Args:
            video_path: Path to video file
            
        Returns:
            Validated Path object
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format is not supported
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if not video_path.is_file():
            raise ValueError(f"Path is not a file: {video_path}")
        
        if video_path.suffix.lower() not in self.SUPPORTED_VIDEO_FORMATS:
            raise ValueError(
                f"Unsupported video format: {video_path.suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_VIDEO_FORMATS))}"
            )
        
        return video_path
    
    def extract_audio(
        self,
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        show_progress: bool = True,
        start_time: Optional[float] = None,
        duration: Optional[float] = None
    ) -> Path:
        """
        Extract audio from video and convert to WAV format
        
        Args:
            video_path: Path to input video file
            output_path: Path for output audio file (optional)
            sample_rate: Audio sample rate (default 16kHz for Whisper)
            channels: Number of audio channels (default 1 for mono)
            show_progress: Show extraction progress
            
        Returns:
            Path to extracted audio file
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format is not supported
            RuntimeError: If audio extraction fails
        """
        # Validate input
        video_path = self.validate_video_file(video_path)
        
        # Generate output path if not provided
        if output_path is None:
            output_filename = f"{video_path.stem}_audio.wav"
            output_path = self.temp_dir / output_filename
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Check if video has audio stream
            probe = ffmpeg.probe(str(video_path))
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            
            if not audio_streams:
                raise ValueError(f"No audio stream found in video: {video_path}")
            
            # Build ffmpeg command
            input_kwargs = {}
            if start_time is not None:
                input_kwargs['ss'] = start_time
            if duration is not None:
                input_kwargs['t'] = duration
                
            stream = ffmpeg.input(str(video_path), **input_kwargs)
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec='pcm_s16le',  # 16-bit PCM
                ar=sample_rate,      # Sample rate
                ac=channels,         # Channels (mono)
                format='wav',
                loglevel='error'     # Only show errors
            )
            stream = ffmpeg.overwrite_output(stream)
            
            # Extract audio with progress
            if show_progress:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(
                        f"Extracting audio from {video_path.name}...", 
                        total=None
                    )
                    
                    # Run ffmpeg
                    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
                    progress.update(task, completed=True)
                    
                console.print(f"[green]✓[/green] Audio extracted successfully")
            else:
                ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            # Verify output file
            if not output_path.exists():
                raise RuntimeError("Audio extraction failed: output file not created")
            
            # Check file size
            file_size = output_path.stat().st_size
            if file_size == 0:
                raise RuntimeError("Audio extraction failed: output file is empty")
            
            return output_path
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg error during audio extraction: {error_message}")
        except Exception as e:
            # Clean up on error
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"Audio extraction failed: {str(e)}")
    
    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """
        Get video file information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        video_path = self.validate_video_file(video_path)
        
        try:
            probe = ffmpeg.probe(str(video_path))
            
            # Extract relevant information
            info = {
                'filename': video_path.name,
                'format': probe['format']['format_name'],
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'bit_rate': int(probe['format'].get('bit_rate', 0)),
                'streams': []
            }
            
            # Process streams
            for stream in probe['streams']:
                stream_info = {
                    'type': stream['codec_type'],
                    'codec': stream['codec_name']
                }
                
                if stream['codec_type'] == 'video':
                    stream_info.update({
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'fps': eval(stream.get('r_frame_rate', '0/1'))
                    })
                elif stream['codec_type'] == 'audio':
                    stream_info.update({
                        'sample_rate': int(stream.get('sample_rate', 0)),
                        'channels': stream.get('channels', 0)
                    })
                
                info['streams'].append(stream_info)
            
            return info
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"Failed to get video info: {error_message}")
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary audio files"""
        pattern = "*_audio.wav"
        for temp_file in self.temp_dir.glob(pattern):
            try:
                temp_file.unlink()
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to delete {temp_file}: {e}")
    
    def _is_valid_video_format(self, video_path: Path) -> bool:
        """Check if video format is supported"""
        return video_path.suffix.lower() in self.SUPPORTED_VIDEO_FORMATS
    
    def get_video_duration(self, video_path: Union[str, Path]) -> float:
        """
        Get video duration in seconds
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        video_path = Path(video_path)
        
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            raise RuntimeError(f"Failed to get video duration: {str(e)}")