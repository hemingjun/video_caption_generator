"""
Tests for CLI interface
"""
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from caption_generator import main


class TestCLI:
    """Test cases for CLI interface"""
    
    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "Video Caption Generator" in result.output
        assert "Extract speech" in result.output
    
    def test_cli_version(self):
        """Test CLI version command"""
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output
    
    @patch("caption_generator.VideoCaptionGenerator")
    @patch("caption_generator.get_settings")
    def test_cli_basic_command(self, mock_get_settings, mock_generator_class, sample_video_path):
        """Test basic CLI command"""
        # Setup mocks
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_generator = Mock()
        mock_generator.process_video = AsyncMock(return_value={
            "video_path": str(sample_video_path),
            "detected_language": "en",
            "target_language": "zh",
            "segments_count": 5,
            "output_files": {"srt": "/output/video.zh.srt", "txt": "/output/video.zh.txt"},
            "temp_dir": None
        })
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_video_path)])
        
        # Check success
        assert result.exit_code == 0
        assert "Processing completed successfully" in result.output
        
        # Verify process_video was called with defaults
        mock_generator.process_video.assert_called_once()
        call_kwargs = mock_generator.process_video.call_args[1]
        assert call_kwargs["target_language"] == "zh"  # Default
        assert call_kwargs["whisper_model"] == "base"  # Default
        assert call_kwargs["translation_service"] == "openai"  # Default
    
    def test_cli_video_not_found(self, temp_dir):
        """Test CLI with non-existent video file"""
        runner = CliRunner()
        nonexistent = temp_dir / "nonexistent.mp4"
        
        result = runner.invoke(main, [str(nonexistent)])
        
        assert result.exit_code == 1
        assert "Video file not found" in result.output
    
    @patch("caption_generator.VideoCaptionGenerator")
    @patch("caption_generator.get_settings")
    def test_cli_with_options(self, mock_get_settings, mock_generator_class, sample_video_path, temp_dir):
        """Test CLI with various options"""
        # Setup mocks
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_generator = Mock()
        mock_generator.process_video = AsyncMock(return_value={
            "video_path": str(sample_video_path),
            "detected_language": "en",
            "target_language": "es",
            "segments_count": 3,
            "output_files": {"srt": "/output/video.es.srt", "json": "/output/video.es.json"},
            "temp_dir": str(temp_dir)
        })
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(main, [
            str(sample_video_path),
            "--target-language", "es",
            "--model", "large",
            "--output-dir", str(temp_dir),
            "--format", "srt",
            "--format", "json",
            "--translator", "claude",
            "--keep-temp",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        
        # Verify options were passed correctly
        call_kwargs = mock_generator.process_video.call_args[1]
        assert call_kwargs["target_language"] == "es"
        assert call_kwargs["whisper_model"] == "large"
        assert call_kwargs["output_dir"] == temp_dir
        assert set(call_kwargs["output_formats"]) == {"srt", "json"}
        assert call_kwargs["translation_service"] == "claude"
        assert call_kwargs["keep_temp"] is True
    
    @patch("caption_generator.VideoCaptionGenerator")
    @patch("caption_generator.get_settings")
    def test_cli_keyboard_interrupt(self, mock_get_settings, mock_generator_class, sample_video_path):
        """Test CLI handles keyboard interrupt gracefully"""
        # Setup mocks
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_generator = Mock()
        mock_generator.process_video = AsyncMock(side_effect=KeyboardInterrupt())
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_video_path)])
        
        assert result.exit_code == 130  # Standard exit code for SIGINT
        assert "cancelled by user" in result.output
    
    @patch("caption_generator.VideoCaptionGenerator")
    @patch("caption_generator.get_settings")
    def test_cli_general_error(self, mock_get_settings, mock_generator_class, sample_video_path):
        """Test CLI handles general errors"""
        # Setup mocks
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_generator = Mock()
        mock_generator.process_video = AsyncMock(side_effect=RuntimeError("Test error"))
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_video_path)])
        
        assert result.exit_code == 1
        assert "Error: Test error" in result.output
    
    @patch("caption_generator.VideoCaptionGenerator")
    @patch("caption_generator.get_settings")
    def test_cli_verbose_error(self, mock_get_settings, mock_generator_class, sample_video_path):
        """Test CLI shows full traceback in verbose mode"""
        # Setup mocks
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_generator = Mock()
        mock_generator.process_video = AsyncMock(side_effect=RuntimeError("Detailed error"))
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_video_path), "--verbose"])
        
        assert result.exit_code == 1
        assert "Error: Detailed error" in result.output
        # In verbose mode, should attempt to show more details
    
    def test_cli_multiple_formats(self):
        """Test CLI help shows multiple format options"""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "srt" in result.output
        assert "txt" in result.output
        assert "json" in result.output