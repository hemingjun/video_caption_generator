"""
Tests for AudioExtractor module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import ffmpeg

from modules.audio_extractor import AudioExtractor


class TestAudioExtractor:
    """Test cases for AudioExtractor"""
    
    def test_init(self):
        """Test AudioExtractor initialization"""
        extractor = AudioExtractor()
        assert extractor is not None
        assert extractor.temp_dir.exists()
    
    def test_init_with_custom_temp_dir(self, temp_dir):
        """Test initialization with custom temp directory"""
        extractor = AudioExtractor(temp_dir=temp_dir)
        assert extractor.temp_dir == temp_dir
    
    @patch("ffmpeg.run")
    @patch("ffmpeg.probe")
    def test_extract_audio_success(self, mock_probe, mock_run, sample_video_path, temp_dir):
        """Test successful audio extraction"""
        # Setup mocks
        mock_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '120.0'}
        }
        
        extractor = AudioExtractor()
        output_path = temp_dir / "audio.wav"
        
        # Create fake output file
        output_path.write_bytes(b"dummy audio")
        
        result = extractor.extract_audio(sample_video_path, output_path, show_progress=False)
        
        assert result == output_path
        assert mock_run.called
    
    def test_extract_audio_invalid_input(self, temp_dir):
        """Test extraction with non-existent video file"""
        extractor = AudioExtractor()
        invalid_path = temp_dir / "nonexistent.mp4"
        output_path = temp_dir / "audio.wav"
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_audio(invalid_path, output_path)
    
    @patch("ffmpeg.run")
    @patch("ffmpeg.probe")
    def test_extract_audio_no_audio_stream(self, mock_probe, mock_run, sample_video_path, temp_dir):
        """Test extraction when video has no audio stream"""
        # Setup mock to return no audio streams
        mock_probe.return_value = {
            'streams': [{'codec_type': 'video'}],  # Only video stream
            'format': {'duration': '120.0'}
        }
        
        extractor = AudioExtractor()
        output_path = temp_dir / "audio.wav"
        
        with pytest.raises(ValueError, match="No audio stream found"):
            extractor.extract_audio(sample_video_path, output_path)
    
    @patch("ffmpeg.run")
    @patch("ffmpeg.probe")
    def test_extract_audio_ffmpeg_failure(self, mock_probe, mock_run, sample_video_path, temp_dir):
        """Test handling of ffmpeg failure"""
        # Setup mocks
        mock_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '120.0'}
        }
        
        # Simulate ffmpeg error
        mock_run.side_effect = ffmpeg.Error(
            cmd='ffmpeg',
            stdout=b'',
            stderr=b'Error: Invalid input file'
        )
        
        extractor = AudioExtractor()
        output_path = temp_dir / "audio.wav"
        
        with pytest.raises(RuntimeError, match="FFmpeg error"):
            extractor.extract_audio(sample_video_path, output_path)
    
    def test_validate_video_formats(self):
        """Test video format validation"""
        extractor = AudioExtractor()
        
        # Valid formats
        valid_formats = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
        for fmt in valid_formats:
            path = Path(f"test{fmt}")
            assert extractor._is_valid_video_format(path) is True
        
        # Invalid formats
        invalid_formats = [".txt", ".jpg", ".png", ".pdf"]
        for fmt in invalid_formats:
            path = Path(f"test{fmt}")
            assert extractor._is_valid_video_format(path) is False
    
    def test_validate_video_file_not_exists(self, temp_dir):
        """Test validate_video_file with non-existent file"""
        extractor = AudioExtractor()
        invalid_path = temp_dir / "nonexistent.mp4"
        
        with pytest.raises(FileNotFoundError):
            extractor.validate_video_file(invalid_path)
    
    def test_validate_video_file_not_a_file(self, temp_dir):
        """Test validate_video_file with directory instead of file"""
        extractor = AudioExtractor()
        
        with pytest.raises(ValueError, match="Path is not a file"):
            extractor.validate_video_file(temp_dir)
    
    def test_validate_video_file_unsupported_format(self, temp_dir):
        """Test validate_video_file with unsupported format"""
        extractor = AudioExtractor()
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("not a video")
        
        with pytest.raises(ValueError, match="Unsupported video format"):
            extractor.validate_video_file(invalid_file)
    
    @patch("ffmpeg.probe")
    def test_get_video_duration(self, mock_probe, sample_video_path):
        """Test getting video duration"""
        # Mock ffprobe output
        mock_probe.return_value = {
            'format': {'duration': '120.5'}
        }
        
        extractor = AudioExtractor()
        duration = extractor.get_video_duration(sample_video_path)
        
        assert duration == 120.5
        mock_probe.assert_called_once_with(str(sample_video_path))
    
    @patch("ffmpeg.run")
    @patch("ffmpeg.probe")
    def test_extract_audio_with_time_range(self, mock_probe, mock_run, sample_video_path, temp_dir):
        """Test extracting audio with start and end time"""
        # Setup mocks
        mock_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '120.0'}
        }
        
        extractor = AudioExtractor()
        output_path = temp_dir / "audio.wav"
        
        # Create fake output file
        output_path.write_bytes(b"dummy audio")
        
        # Extract 10 seconds starting from 30s
        result = extractor.extract_audio(
            sample_video_path,
            output_path,
            start_time=30,
            duration=10,
            show_progress=False
        )
        
        assert result == output_path
        assert mock_run.called
    
    @patch("ffmpeg.probe")
    def test_get_video_info(self, mock_probe, sample_video_path):
        """Test getting video information"""
        # Mock comprehensive video info
        mock_probe.return_value = {
            'format': {
                'format_name': 'mp4',
                'duration': '120.5',
                'size': '1048576',
                'bit_rate': '8000000'
            },
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '30/1'
                },
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac',
                    'sample_rate': '48000',
                    'channels': 2
                }
            ]
        }
        
        extractor = AudioExtractor()
        info = extractor.get_video_info(sample_video_path)
        
        assert info['filename'] == sample_video_path.name
        assert info['format'] == 'mp4'
        assert info['duration'] == 120.5
        assert info['size'] == 1048576
        assert len(info['streams']) == 2
        assert info['streams'][0]['type'] == 'video'
        assert info['streams'][1]['type'] == 'audio'
    
    def test_cleanup_temp_files(self, temp_dir):
        """Test cleanup of temporary files"""
        extractor = AudioExtractor(temp_dir=temp_dir)
        
        # Create some temp audio files
        temp_files = [
            temp_dir / "video1_audio.wav",
            temp_dir / "video2_audio.wav",
            temp_dir / "other_file.txt"  # Should not be deleted
        ]
        
        for f in temp_files:
            f.write_bytes(b"dummy content")
        
        # Cleanup
        extractor.cleanup_temp_files()
        
        # Check results
        assert not (temp_dir / "video1_audio.wav").exists()
        assert not (temp_dir / "video2_audio.wav").exists()
        assert (temp_dir / "other_file.txt").exists()  # Should still exist