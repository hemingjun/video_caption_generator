#!/usr/bin/env python3
"""
Video Caption Generator - Main Entry Point
A CLI tool to extract speech from videos and translate to target languages
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import tempfile
import shutil

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from config import get_settings
from modules.audio_extractor import AudioExtractor
from modules.speech_recognizer import SpeechRecognizer
from modules.translator import TranslatorFactory, TranslationSegment
from modules.output_handler import OutputHandler
from utils.logger import setup_logger
from utils.file_utils import cleanup_temp_files, get_file_size_mb, estimate_processing_time

# Initialize console and logger
console = Console()
logger = setup_logger("video_caption_generator")

# Version
__version__ = "1.0.0"


class VideoCaptionGenerator:
    """Main class for video caption generation"""
    
    def __init__(self, settings=None):
        """Initialize with settings"""
        self.settings = settings or get_settings()
        self.temp_dir = None
        
    async def process_video(
        self,
        video_path: Path,
        target_language: str,
        source_language: Optional[str] = None,
        whisper_model: str = "base",
        output_dir: Optional[Path] = None,
        output_formats: List[str] = None,
        translation_service: str = "openai",
        keep_temp: bool = False
    ) -> dict:
        """
        Process a video file to generate translated captions
        
        Args:
            video_path: Path to input video
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
            whisper_model: Whisper model size
            output_dir: Output directory
            output_formats: List of output formats
            translation_service: Translation service to use
            keep_temp: Keep temporary files
            
        Returns:
            Dictionary with processing results
        """
        if output_formats is None:
            output_formats = ["srt", "txt"]
            
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="vcg_"))
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        try:
            # Step 1: Extract audio
            console.print("\n[bold blue]Step 1/4:[/bold blue] Extracting audio from video...")
            audio_extractor = AudioExtractor()
            audio_path = await self._extract_audio_with_progress(
                audio_extractor, video_path, self.temp_dir
            )
            
            # Step 2: Speech recognition
            console.print("\n[bold blue]Step 2/4:[/bold blue] Performing speech recognition...")
            recognizer = SpeechRecognizer(model_name=whisper_model)
            transcription = await self._recognize_speech_with_progress(
                recognizer, audio_path, source_language
            )
            
            # Step 3: Translation (if needed)
            segments = transcription.get("segments", [])
            detected_language = transcription.get("language", "en")
            
            if detected_language != target_language:
                console.print(f"\n[bold blue]Step 3/4:[/bold blue] Translating from {detected_language} to {target_language}...")
                segments = await self._translate_segments_with_progress(
                    segments, detected_language, target_language, translation_service
                )
            else:
                console.print(f"\n[bold blue]Step 3/4:[/bold blue] No translation needed (already in {target_language})")
            
            # Step 4: Save outputs
            console.print("\n[bold blue]Step 4/4:[/bold blue] Saving output files...")
            output_handler = OutputHandler(output_dir)
            saved_files = await self._save_outputs_with_progress(
                output_handler, segments, video_path, output_formats, target_language, transcription
            )
            
            # Show results
            self._display_results(saved_files, video_path)
            
            return {
                "video_path": str(video_path),
                "detected_language": detected_language,
                "target_language": target_language,
                "segments_count": len(segments),
                "output_files": saved_files,
                "temp_dir": str(self.temp_dir) if keep_temp else None
            }
            
        finally:
            # Cleanup
            if not keep_temp and self.temp_dir:
                try:
                    shutil.rmtree(self.temp_dir)
                    logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")
    
    async def _extract_audio_with_progress(self, extractor, video_path, temp_dir):
        """Extract audio with progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting audio...", total=None)
            
            # Run extraction in thread
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                None,
                lambda: extractor.extract_audio(video_path, temp_dir / "audio.wav")
            )
            
            progress.update(task, completed=True)
            
        file_size = get_file_size_mb(audio_path)
        console.print(f"✓ Audio extracted: {file_size:.1f} MB")
        return audio_path
    
    async def _recognize_speech_with_progress(self, recognizer, audio_path, source_language):
        """Recognize speech with progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            # Estimate time based on file size
            file_size = get_file_size_mb(audio_path)
            estimated_time = estimate_processing_time(file_size, has_gpu=recognizer.device != "cpu")
            
            task = progress.add_task(
                f"Processing with Whisper ({recognizer.model_name} model)...",
                total=100
            )
            
            # Simulate progress (actual Whisper doesn't provide progress)
            async def update_progress():
                for i in range(100):
                    await asyncio.sleep(estimated_time / 100)
                    progress.update(task, advance=1)
            
            # Run recognition and progress update concurrently
            progress_task = asyncio.create_task(update_progress())
            
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                lambda: recognizer.transcribe(audio_path, source_language)
            )
            
            # Cancel progress if finished early
            progress_task.cancel()
            progress.update(task, completed=100)
            
        segments_count = len(transcription.get("segments", []))
        console.print(f"✓ Recognized {segments_count} segments")
        return transcription
    
    async def _translate_segments_with_progress(self, segments, source_lang, target_lang, service):
        """Translate segments with progress display"""
        # Get API key based on service
        if service == "openai":
            api_key = self.settings.api.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")
        else:
            api_key = self.settings.api.claude_api_key
            if not api_key:
                raise ValueError("Claude API key not configured")
        
        # Create translator
        translator = TranslatorFactory.create_translator(
            service=service,
            api_key=api_key,
            target_language=target_lang,
            model=self.settings.translation.openai_model if service == "openai" else self.settings.translation.claude_model
        )
        
        # Convert to TranslationSegment objects
        translation_segments = [
            TranslationSegment(
                index=i,
                text=seg.get("text", ""),
                start_time=seg.get("start", 0),
                end_time=seg.get("end", 0)
            )
            for i, seg in enumerate(segments)
        ]
        
        # Translate with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Translating with {service.title()}...",
                total=len(translation_segments)
            )
            
            translated_segments = await translator.translate_batch(
                translation_segments,
                source_lang=source_lang,
                progress=progress,
                task_id=task
            )
        
        # Convert back to dict format
        result_segments = []
        for seg in translated_segments:
            result_segments.append({
                "start": seg.start_time,
                "end": seg.end_time,
                "text": seg.text,
                "translated_text": seg.translated_text
            })
        
        console.print(f"✓ Translated {len(result_segments)} segments")
        return result_segments
    
    async def _save_outputs_with_progress(self, handler, segments, video_path, formats, target_lang, transcription):
        """Save outputs with progress display"""
        saved_files = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Saving {len(formats)} output files...", total=len(formats))
            
            # Prepare transcription result with segments
            result = {
                "segments": segments,
                "text": transcription.get("text", ""),
                "language": transcription.get("language", ""),
                "target_language": target_lang
            }
            
            # Save each format
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(
                None,
                lambda: handler.save_all_formats(result, video_path, formats, target_lang)
            )
            
            saved_files.update(files)
            progress.update(task, advance=len(formats))
        
        return saved_files
    
    def _display_results(self, saved_files, video_path):
        """Display processing results in a nice table"""
        table = Table(title="Processing Complete", show_header=True)
        table.add_column("Output Type", style="cyan")
        table.add_column("File Path", style="green")
        table.add_column("Size", style="yellow")
        
        for fmt, path in saved_files.items():
            size = get_file_size_mb(path)
            table.add_row(
                fmt.upper(),
                str(path),
                f"{size:.2f} MB" if size > 0.01 else f"{size*1024:.0f} KB"
            )
        
        console.print("\n")
        console.print(table)


@click.command()
@click.argument("video_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-t", "--target-language",
    default="zh",
    help="Target language code (default: zh for Chinese)"
)
@click.option(
    "-s", "--source-language",
    default=None,
    help="Source language code (auto-detect if not specified)"
)
@click.option(
    "-m", "--model",
    default="base",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    help="Whisper model size (default: base)"
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: ./output)"
)
@click.option(
    "-f", "--format",
    "output_formats",
    multiple=True,
    type=click.Choice(["srt", "txt", "json"]),
    default=["srt", "txt"],
    help="Output formats (can specify multiple)"
)
@click.option(
    "--translator",
    type=click.Choice(["openai", "claude"]),
    default="openai",
    help="Translation service to use"
)
@click.option(
    "--keep-temp",
    is_flag=True,
    help="Keep temporary files after processing"
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose logging"
)
@click.version_option(version=__version__)
def main(
    video_path: Path,
    target_language: str,
    source_language: Optional[str],
    model: str,
    output_dir: Optional[Path],
    output_formats: List[str],
    translator: str,
    keep_temp: bool,
    verbose: bool
):
    """
    Video Caption Generator - Extract speech and translate to target language
    
    Example:
        vcg video.mp4 -t zh -m small -f srt txt
    """
    # Show banner
    banner = Panel.fit(
        f"[bold cyan]Video Caption Generator v{__version__}[/bold cyan]\n"
        "[dim]Extract speech from videos and translate to any language[/dim]",
        border_style="blue"
    )
    console.print(banner)
    
    # Validate video file
    if not video_path.exists():
        console.print(f"[red]Error: Video file not found: {video_path}[/red]")
        sys.exit(1)
    
    # Get file info
    file_size = get_file_size_mb(video_path)
    console.print(f"\n📹 Processing: [bold]{video_path.name}[/bold] ({file_size:.1f} MB)")
    
    # Initialize generator
    try:
        settings = get_settings()
        generator = VideoCaptionGenerator(settings)
        
        # Configure logging
        if verbose:
            setup_logger("video_caption_generator", level="DEBUG")
        
        # Process video
        result = asyncio.run(generator.process_video(
            video_path=video_path,
            target_language=target_language,
            source_language=source_language,
            whisper_model=model,
            output_dir=output_dir,
            output_formats=list(output_formats),
            translation_service=translator,
            keep_temp=keep_temp
        ))
        
        # Success message
        console.print("\n[bold green]✅ Processing completed successfully![/bold green]")
        
        if keep_temp and result.get("temp_dir"):
            console.print(f"[dim]Temporary files kept at: {result['temp_dir']}[/dim]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Processing cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()