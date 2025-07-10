"""
Speech recognition module using OpenAI Whisper
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import whisper
import torch
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from dataclasses import dataclass
import sys
sys.path.append(str(Path(__file__).parent.parent))
from performance_config import PerformanceConfig

console = Console()


@dataclass
class TranscriptionSegment:
    """Represents a transcribed segment with timing information"""
    start: float
    end: float
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'language': self.language,
            'confidence': self.confidence
        }


class SpeechRecognizer:
    """Speech recognition using OpenAI Whisper"""
    
    MODEL_SIZES = {
        'tiny': {'size': '39M', 'description': 'Fastest, lowest accuracy'},
        'base': {'size': '74M', 'description': 'Good balance of speed and accuracy'},
        'small': {'size': '244M', 'description': 'Better accuracy, slower'},
        'medium': {'size': '769M', 'description': 'High accuracy, quite slow'},
        'large': {'size': '1550M', 'description': 'Best accuracy, very slow'}
    }
    
    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        download_root: Optional[str] = None
    ):
        """
        Initialize speech recognizer
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda/cpu), auto-detect if None
            download_root: Directory to store downloaded models
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.download_root = download_root
        self.model = None
        
        # Validate model name
        if model_name not in self.MODEL_SIZES:
            raise ValueError(
                f"Invalid model name: {model_name}. "
                f"Available models: {', '.join(self.MODEL_SIZES.keys())}"
            )
    
    def _get_device(self, device: Optional[str]) -> str:
        """Determine the device to use for inference"""
        if device:
            return device
        
        # Auto-detect CUDA availability
        if torch.cuda.is_available():
            console.print("[green]CUDA available, using GPU for inference[/green]")
            return "cuda"
        else:
            console.print("[yellow]CUDA not available, using CPU for inference[/yellow]")
            return "cpu"
    
    def load_model(self, show_progress: bool = True) -> None:
        """
        Load Whisper model
        
        Args:
            show_progress: Show download/loading progress
        """
        if self.model:
            return  # Model already loaded
        
        console.print(f"Loading Whisper [cyan]{self.model_name}[/cyan] model...")
        
        try:
            if show_progress:
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(
                        f"Downloading/Loading {self.model_name} model...",
                        total=100
                    )
                    
                    # Load model
                    self.model = whisper.load_model(
                        self.model_name,
                        device=self.device,
                        download_root=self.download_root
                    )
                    
                    progress.update(task, completed=100)
            else:
                self.model = whisper.load_model(
                    self.model_name,
                    device=self.device,
                    download_root=self.download_root
                )
            
            model_info = self.MODEL_SIZES[self.model_name]
            console.print(
                f"[green]✓[/green] Model loaded successfully "
                f"(size: {model_info['size']}, device: {self.device})"
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {str(e)}")
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",
        show_progress: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            language: Source language code (auto-detect if None)
            task: Task type ('transcribe' or 'translate')
            show_progress: Show transcription progress
            **kwargs: Additional arguments for whisper.transcribe()
            
        Returns:
            Dictionary with transcription results
        """
        if not self.model:
            self.load_model(show_progress)
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        console.print(f"Transcribing audio: {audio_path.name}")
        
        try:
            # Get optimal compute type
            compute_type = PerformanceConfig.get_whisper_compute_type(
                self.model_name,
                self.device == "cuda"
            )
            
            # Default parameters with performance optimizations
            transcribe_params = {
                'language': language,
                'task': task,
                'verbose': False,
                'temperature': 0,  # Use deterministic decoding for consistency
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6,
                'condition_on_previous_text': True,
                'initial_prompt': None,
                'word_timestamps': False,
                'beam_size': PerformanceConfig.WHISPER_BEAM_SIZE,
                'best_of': PerformanceConfig.WHISPER_BEST_OF,
            }
            
            # Check if we should use VAD (Voice Activity Detection)
            # Note: This would require additional implementation
            
            # Update with user parameters
            transcribe_params.update(kwargs)
            
            # Transcribe with progress
            if show_progress:
                # Whisper doesn't provide native progress callbacks
                # We'll show an indeterminate progress bar
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    task_id = progress.add_task(
                        "Transcribing audio...",
                        total=None
                    )
                    
                    result = self.model.transcribe(
                        str(audio_path),
                        **transcribe_params
                    )
                    
                    progress.update(task_id, completed=True)
            else:
                result = self.model.transcribe(
                    str(audio_path),
                    **transcribe_params
                )
            
            console.print("[green]✓[/green] Transcription completed")
            
            # Process results
            segments = self._process_segments(result.get('segments', []))
            
            return {
                'text': result.get('text', '').strip(),
                'segments': segments,
                'language': result.get('language', language),
                'duration': self._get_audio_duration(segments)
            }
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}")
    
    def _process_segments(self, raw_segments: List[Dict]) -> List[TranscriptionSegment]:
        """Process raw segments into TranscriptionSegment objects"""
        segments = []
        
        for seg in raw_segments:
            segment = TranscriptionSegment(
                start=seg['start'],
                end=seg['end'],
                text=seg['text'].strip(),
                confidence=seg.get('confidence')
            )
            segments.append(segment)
        
        return segments
    
    def _get_audio_duration(self, segments: List[TranscriptionSegment]) -> float:
        """Get total audio duration from segments"""
        if not segments:
            return 0.0
        return max(seg.end for seg in segments)
    
    def detect_language(
        self,
        audio_path: Union[str, Path],
        show_progress: bool = True
    ) -> tuple[str, float]:
        """
        Detect language of audio file
        
        Args:
            audio_path: Path to audio file
            show_progress: Show detection progress
            
        Returns:
            Tuple of (language_code, probability)
        """
        if not self.model:
            self.load_model(show_progress)
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Load audio
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            
            # Get most likely language
            language = max(probs, key=probs.get)
            probability = probs[language]
            
            console.print(
                f"Detected language: [cyan]{language}[/cyan] "
                f"(confidence: {probability:.2%})"
            )
            
            return language, probability
            
        except Exception as e:
            raise RuntimeError(f"Language detection failed: {str(e)}")
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self.model:
            return {
                'loaded': False,
                'name': self.model_name,
                'size': self.MODEL_SIZES[self.model_name]['size'],
                'description': self.MODEL_SIZES[self.model_name]['description']
            }
        
        return {
            'loaded': True,
            'name': self.model_name,
            'size': self.MODEL_SIZES[self.model_name]['size'],
            'description': self.MODEL_SIZES[self.model_name]['description'],
            'device': str(self.device),
            'parameters': sum(p.numel() for p in self.model.parameters())
        }
    
    @classmethod
    def list_available_models(cls) -> None:
        """Print available Whisper models"""
        console.print("\n[bold]Available Whisper Models:[/bold]")
        for name, info in cls.MODEL_SIZES.items():
            console.print(
                f"  • [cyan]{name:8}[/cyan] - "
                f"Size: {info['size']:6} - {info['description']}"
            )
        console.print()