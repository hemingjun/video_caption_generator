"""
Output handler module for Video Caption Generator
Supports multiple output formats: SRT, TXT, JSON
"""
import json
from pathlib import Path
from typing import List, Union, Optional, Dict, Any
from datetime import timedelta
from rich.console import Console

console = Console()


class OutputHandler:
    """Handle different output formats for transcribed and translated content"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize output handler
        
        Args:
            output_dir: Default output directory
        """
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_srt(
        self,
        segments: List[Dict[str, Any]],
        output_path: Union[str, Path],
        use_translated: bool = True
    ) -> Path:
        """
        Save segments as SRT subtitle file
        
        Args:
            segments: List of segments with timing and text
            output_path: Path for output file
            use_translated: Use translated text if available
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                # Write subtitle index
                f.write(f"{i}\n")
                
                # Write timing
                start_time = self._format_srt_time(segment.get('start', 0))
                end_time = self._format_srt_time(segment.get('end', 0))
                f.write(f"{start_time} --> {end_time}\n")
                
                # Write text
                if use_translated and 'translated_text' in segment:
                    text = segment['translated_text']
                else:
                    text = segment.get('text', '')
                
                f.write(f"{text}\n\n")
        
        console.print(f"[green]✓[/green] SRT file saved: {output_path}")
        return output_path
    
    def save_text(
        self,
        text: str,
        output_path: Union[str, Path],
        segments: Optional[List[Dict[str, Any]]] = None,
        include_timestamps: bool = False
    ) -> Path:
        """
        Save as plain text file
        
        Args:
            text: Full text to save
            output_path: Path for output file
            segments: Optional segments for timestamp inclusion
            include_timestamps: Include timestamps with segments
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if segments and include_timestamps:
                for segment in segments:
                    timestamp = f"[{self._format_timestamp(segment.get('start', 0))} - {self._format_timestamp(segment.get('end', 0))}]"
                    
                    if 'translated_text' in segment:
                        text_content = segment['translated_text']
                    else:
                        text_content = segment.get('text', '')
                    
                    f.write(f"{timestamp} {text_content}\n\n")
            else:
                f.write(text)
        
        console.print(f"[green]✓[/green] Text file saved: {output_path}")
        return output_path
    
    def save_json(
        self,
        data: Dict[str, Any],
        output_path: Union[str, Path],
        pretty: bool = True
    ) -> Path:
        """
        Save data as JSON file
        
        Args:
            data: Data to save
            output_path: Path for output file
            pretty: Pretty print JSON
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        console.print(f"[green]✓[/green] JSON file saved: {output_path}")
        return output_path
    
    def save_bilingual_srt(
        self,
        segments: List[Dict[str, Any]],
        output_path: Union[str, Path]
    ) -> Path:
        """
        Save bilingual SRT with both original and translated text
        
        Args:
            segments: List of segments with original and translated text
            output_path: Path for output file
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                # Write subtitle index
                f.write(f"{i}\n")
                
                # Write timing
                start_time = self._format_srt_time(segment.get('start', 0))
                end_time = self._format_srt_time(segment.get('end', 0))
                f.write(f"{start_time} --> {end_time}\n")
                
                # Write original text
                original_text = segment.get('text', '')
                f.write(f"{original_text}\n")
                
                # Write translated text if available
                if 'translated_text' in segment:
                    translated_text = segment['translated_text']
                    f.write(f"{translated_text}\n")
                
                f.write("\n")
        
        console.print(f"[green]✓[/green] Bilingual SRT file saved: {output_path}")
        return output_path
    
    def generate_output_paths(
        self,
        input_path: Union[str, Path],
        formats: List[str],
        suffix: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Generate output paths for different formats
        
        Args:
            input_path: Input file path
            formats: List of output formats ('srt', 'txt', 'json')
            suffix: Optional suffix to add to filename
            
        Returns:
            Dictionary mapping format to output path
        """
        input_path = Path(input_path)
        base_name = input_path.stem
        
        if suffix:
            base_name = f"{base_name}_{suffix}"
        
        paths = {}
        for fmt in formats:
            output_name = f"{base_name}.{fmt}"
            paths[fmt] = self.output_dir / output_name
        
        return paths
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        seconds = int(td.total_seconds() % 60)
        milliseconds = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to readable timestamp (HH:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def save_all_formats(
        self,
        transcription_result: Dict[str, Any],
        input_path: Union[str, Path],
        formats: List[str] = None,
        language_suffix: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Save transcription results in multiple formats
        
        Args:
            transcription_result: Complete transcription result
            input_path: Original input file path
            formats: List of formats to save (default: all)
            language_suffix: Language suffix for filename
            
        Returns:
            Dictionary mapping format to saved file path
        """
        if formats is None:
            formats = ['srt', 'txt', 'json']
        
        # Generate output paths
        suffix = language_suffix or transcription_result.get('target_language', '')
        output_paths = self.generate_output_paths(input_path, formats, suffix)
        
        saved_paths = {}
        
        # Prepare segments data
        segments = []
        for seg in transcription_result.get('segments', []):
            segment_dict = {
                'start': seg.get('start', 0),
                'end': seg.get('end', 0),
                'text': seg.get('text', ''),
            }
            if 'translated_text' in seg:
                segment_dict['translated_text'] = seg['translated_text']
            segments.append(segment_dict)
        
        # Save SRT
        if 'srt' in formats:
            saved_paths['srt'] = self.save_srt(
                segments,
                output_paths['srt'],
                use_translated=True
            )
        
        # Save text
        if 'txt' in formats:
            # Use translated text if available, otherwise original
            if any('translated_text' in seg for seg in segments):
                full_text = '\n'.join([
                    seg.get('translated_text', seg.get('text', ''))
                    for seg in segments
                ])
            else:
                full_text = transcription_result.get('text', '')
            
            saved_paths['txt'] = self.save_text(
                full_text,
                output_paths['txt'],
                segments=segments,
                include_timestamps=False
            )
        
        # Save JSON
        if 'json' in formats:
            saved_paths['json'] = self.save_json(
                transcription_result,
                output_paths['json']
            )
        
        return saved_paths