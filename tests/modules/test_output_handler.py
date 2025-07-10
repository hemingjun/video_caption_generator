"""
Tests for OutputHandler module
"""
import pytest
from pathlib import Path
import json

from modules.output_handler import OutputHandler
from utils.time_utils import format_srt_time


class TestOutputHandler:
    """Test cases for OutputHandler"""
    
    def test_init_default_dir(self):
        """Test initialization with default directory"""
        handler = OutputHandler()
        assert handler.output_dir == Path("./output")
    
    def test_init_custom_dir(self, temp_dir):
        """Test initialization with custom directory"""
        custom_dir = temp_dir / "custom_output"
        handler = OutputHandler(custom_dir)
        assert handler.output_dir == custom_dir
        assert custom_dir.exists()
    
    def test_generate_srt(self, sample_transcription):
        """Test SRT generation"""
        handler = OutputHandler()
        
        # Add translated text to segments
        for seg in sample_transcription["segments"]:
            seg["translated_text"] = f"翻译: {seg['text']}"
        
        srt_content = handler._generate_srt(sample_transcription)
        
        # Verify SRT format
        lines = srt_content.strip().split('\n')
        
        # First subtitle
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:02,500"
        assert lines[2] == "翻译: Hello world"
        assert lines[3] == ""
        
        # Second subtitle
        assert lines[4] == "2"
        assert lines[5] == "00:00:02,500 --> 00:00:05,000"
        assert lines[6] == "翻译: This is a test"
    
    def test_generate_srt_no_translation(self, sample_transcription):
        """Test SRT generation without translation"""
        handler = OutputHandler()
        
        srt_content = handler._generate_srt(sample_transcription)
        
        lines = srt_content.strip().split('\n')
        assert lines[2] == "Hello world"  # Original text
        assert lines[6] == "This is a test"
    
    def test_generate_txt(self, sample_transcription):
        """Test plain text generation"""
        handler = OutputHandler()
        
        # Add translated text
        for seg in sample_transcription["segments"]:
            seg["translated_text"] = f"翻译: {seg['text']}"
        
        txt_content = handler._generate_txt(sample_transcription)
        
        expected = "翻译: Hello world\n翻译: This is a test"
        assert txt_content == expected
    
    def test_generate_json(self, sample_transcription):
        """Test JSON generation"""
        handler = OutputHandler()
        
        json_content = handler._generate_json(sample_transcription)
        data = json.loads(json_content)
        
        assert data["language"] == "en"
        assert data["target_language"] == sample_transcription.get("target_language", "")
        assert len(data["segments"]) == 2
        assert data["segments"][0]["text"] == "Hello world"
    
    def test_save_srt(self, temp_dir, sample_transcription, sample_video_path):
        """Test saving SRT file"""
        handler = OutputHandler(temp_dir)
        
        output_path = handler.save_srt(sample_transcription, sample_video_path, "zh")
        
        assert output_path.exists()
        assert output_path.suffix == ".srt"
        assert "zh" in output_path.name
        assert sample_video_path.stem in output_path.name
    
    def test_save_txt(self, temp_dir, sample_transcription, sample_video_path):
        """Test saving TXT file"""
        handler = OutputHandler(temp_dir)
        
        output_path = handler.save_txt(sample_transcription, sample_video_path, "zh")
        
        assert output_path.exists()
        assert output_path.suffix == ".txt"
        assert "zh" in output_path.name
    
    def test_save_json(self, temp_dir, sample_transcription, sample_video_path):
        """Test saving JSON file"""
        handler = OutputHandler(temp_dir)
        
        output_path = handler.save_json(sample_transcription, sample_video_path, "zh")
        
        assert output_path.exists()
        assert output_path.suffix == ".json"
        
        # Verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert "segments" in data
            assert "language" in data
    
    def test_save_all_formats(self, temp_dir, sample_transcription, sample_video_path):
        """Test saving all formats at once"""
        handler = OutputHandler(temp_dir)
        
        formats = ["srt", "txt", "json"]
        saved_files = handler.save_all_formats(
            sample_transcription,
            sample_video_path,
            formats,
            "zh"
        )
        
        assert len(saved_files) == 3
        assert all(Path(path).exists() for path in saved_files.values())
        assert "srt" in saved_files
        assert "txt" in saved_files
        assert "json" in saved_files
    
    def test_save_with_empty_segments(self, temp_dir, sample_video_path):
        """Test saving with empty segments"""
        handler = OutputHandler(temp_dir)
        
        empty_transcription = {
            "segments": [],
            "text": "",
            "language": "en"
        }
        
        output_path = handler.save_srt(empty_transcription, sample_video_path, "zh")
        
        assert output_path.exists()
        content = output_path.read_text(encoding='utf-8')
        assert content == ""  # Empty SRT
    
    def test_save_with_long_segments(self, temp_dir, sample_video_path):
        """Test saving with long text segments"""
        handler = OutputHandler(temp_dir)
        
        long_text = "This is a very long text " * 50
        transcription = {
            "segments": [{
                "start": 0.0,
                "end": 10.0,
                "text": long_text,
                "translated_text": f"翻译: {long_text}"
            }],
            "text": long_text,
            "language": "en"
        }
        
        output_path = handler.save_srt(transcription, sample_video_path, "zh")
        
        assert output_path.exists()
        content = output_path.read_text(encoding='utf-8')
        assert f"翻译: {long_text}" in content
    
    def test_filename_sanitization(self, temp_dir):
        """Test filename sanitization"""
        handler = OutputHandler(temp_dir)
        
        # Video path with special characters
        video_path = Path("/path/to/video with spaces & special!.mp4")
        transcription = {"segments": [], "text": "", "language": "en"}
        
        output_path = handler.save_srt(transcription, video_path, "zh")
        
        # Check that filename is sanitized
        assert output_path.exists()
        assert "&" not in output_path.name
        assert "!" not in output_path.name