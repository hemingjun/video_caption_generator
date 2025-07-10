"""
Integration tests for complete video caption generation workflow
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile

from caption_generator import VideoCaptionGenerator
from modules.translator import TranslationSegment


class TestFullWorkflow:
    """Integration tests for the complete workflow"""
    
    @pytest.mark.asyncio
    @patch("modules.audio_extractor.ffmpeg.run")
    @patch("modules.audio_extractor.ffmpeg.probe")
    @patch("modules.speech_recognizer.whisper.load_model")
    @patch("modules.translator.AsyncOpenAI")
    async def test_complete_workflow(
        self,
        mock_openai_class,
        mock_whisper_load,
        mock_ffmpeg_probe,
        mock_ffmpeg_run,
        sample_video_path,
        temp_dir,
        mock_settings
    ):
        """Test complete video to caption workflow"""
        # Setup audio extraction mocks
        mock_ffmpeg_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '10.0'}
        }
        
        # Setup Whisper mock
        mock_whisper_model = Mock()
        mock_whisper_model.transcribe.return_value = {
            "text": "Hello world. This is a test.",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello world"
                },
                {
                    "start": 2.5,
                    "end": 5.0,
                    "text": "This is a test"
                }
            ],
            "language": "en"
        }
        mock_whisper_load.return_value = mock_whisper_model
        
        # Setup OpenAI translation mock
        mock_openai_client = AsyncMock()
        mock_response1 = Mock()
        mock_response1.choices = [Mock(message=Mock(content="你好世界"))]
        mock_response2 = Mock()
        mock_response2.choices = [Mock(message=Mock(content="这是一个测试"))]
        
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=[mock_response1, mock_response2]
        )
        mock_openai_class.return_value = mock_openai_client
        
        # Create generator
        generator = VideoCaptionGenerator(mock_settings)
        
        # Create a dummy audio file that will be "extracted"
        audio_path = temp_dir / "audio.wav"
        audio_path.write_bytes(b"dummy audio content")
        
        # Run the workflow
        result = await generator.process_video(
            video_path=sample_video_path,
            target_language="zh",
            output_dir=temp_dir,
            output_formats=["srt", "txt"],
            translation_service="openai",
            whisper_model="base",
            keep_temp=True
        )
        
        # Verify results
        assert result["video_path"] == str(sample_video_path)
        assert result["detected_language"] == "en"
        assert result["target_language"] == "zh"
        assert result["segments_count"] == 2
        assert "srt" in result["output_files"]
        assert "txt" in result["output_files"]
        
        # Check output files exist
        srt_file = Path(result["output_files"]["srt"])
        txt_file = Path(result["output_files"]["txt"])
        assert srt_file.exists()
        assert txt_file.exists()
        
        # Verify SRT content
        srt_content = srt_file.read_text(encoding='utf-8')
        assert "你好世界" in srt_content
        assert "这是一个测试" in srt_content
        
        # Verify TXT content
        txt_content = txt_file.read_text(encoding='utf-8')
        assert "你好世界" in txt_content
        assert "这是一个测试" in txt_content
    
    @pytest.mark.asyncio
    @patch("modules.audio_extractor.ffmpeg.run")
    @patch("modules.audio_extractor.ffmpeg.probe")
    @patch("modules.speech_recognizer.whisper.load_model")
    async def test_workflow_no_translation_needed(
        self,
        mock_whisper_load,
        mock_ffmpeg_probe,
        mock_ffmpeg_run,
        sample_video_path,
        temp_dir,
        mock_settings
    ):
        """Test workflow when no translation is needed"""
        # Setup mocks
        mock_ffmpeg_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '10.0'}
        }
        
        # Whisper returns Chinese text
        mock_whisper_model = Mock()
        mock_whisper_model.transcribe.return_value = {
            "text": "你好世界。这是一个测试。",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "你好世界"
                }
            ],
            "language": "zh"
        }
        mock_whisper_load.return_value = mock_whisper_model
        
        generator = VideoCaptionGenerator(mock_settings)
        
        # Create dummy audio file
        audio_path = temp_dir / "audio.wav"
        audio_path.write_bytes(b"dummy audio")
        
        # Run workflow with target language same as source
        result = await generator.process_video(
            video_path=sample_video_path,
            target_language="zh",
            output_dir=temp_dir,
            output_formats=["srt"]
        )
        
        # Verify no translation occurred
        assert result["detected_language"] == "zh"
        assert result["target_language"] == "zh"
        
        # Check output
        srt_file = Path(result["output_files"]["srt"])
        srt_content = srt_file.read_text(encoding='utf-8')
        assert "你好世界" in srt_content
    
    @pytest.mark.asyncio
    @patch("modules.audio_extractor.ffmpeg.run")
    @patch("modules.audio_extractor.ffmpeg.probe")
    async def test_workflow_audio_extraction_failure(
        self,
        mock_ffmpeg_probe,
        mock_ffmpeg_run,
        sample_video_path,
        temp_dir,
        mock_settings
    ):
        """Test workflow when audio extraction fails"""
        # Setup mock to fail
        mock_ffmpeg_probe.return_value = {
            'streams': [{'codec_type': 'video'}],  # No audio stream
            'format': {'duration': '10.0'}
        }
        
        generator = VideoCaptionGenerator(mock_settings)
        
        # Should raise error
        with pytest.raises(RuntimeError, match="Audio extraction failed"):
            await generator.process_video(
                video_path=sample_video_path,
                target_language="zh",
                output_dir=temp_dir
            )
    
    @pytest.mark.asyncio
    @patch("modules.audio_extractor.ffmpeg.run")
    @patch("modules.audio_extractor.ffmpeg.probe")
    @patch("modules.speech_recognizer.whisper.load_model")
    @patch("modules.translator.AsyncAnthropic")
    async def test_workflow_with_claude_translator(
        self,
        mock_anthropic_class,
        mock_whisper_load,
        mock_ffmpeg_probe,
        mock_ffmpeg_run,
        sample_video_path,
        temp_dir,
        mock_settings
    ):
        """Test workflow using Claude for translation"""
        # Setup mocks
        mock_ffmpeg_probe.return_value = {
            'streams': [{'codec_type': 'audio'}],
            'format': {'duration': '10.0'}
        }
        
        # Whisper mock
        mock_whisper_model = Mock()
        mock_whisper_model.transcribe.return_value = {
            "text": "Hello world",
            "segments": [{"start": 0.0, "end": 2.5, "text": "Hello world"}],
            "language": "en"
        }
        mock_whisper_load.return_value = mock_whisper_model
        
        # Claude translation mock
        mock_anthropic_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="你好世界")]
        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_anthropic_client
        
        generator = VideoCaptionGenerator(mock_settings)
        
        # Create dummy audio
        audio_path = temp_dir / "audio.wav"
        audio_path.write_bytes(b"dummy audio")
        
        # Run with Claude translator
        result = await generator.process_video(
            video_path=sample_video_path,
            target_language="zh",
            output_dir=temp_dir,
            translation_service="claude"
        )
        
        # Verify Claude was used
        assert mock_anthropic_client.messages.create.called
        assert result["detected_language"] == "en"
        assert result["target_language"] == "zh"
    
    @pytest.mark.asyncio
    async def test_workflow_cleanup(self, sample_video_path, temp_dir, mock_settings):
        """Test that temporary files are cleaned up"""
        generator = VideoCaptionGenerator(mock_settings)
        
        # Mock all the necessary components
        with patch("modules.audio_extractor.ffmpeg.run") as mock_run, \
             patch("modules.audio_extractor.ffmpeg.probe") as mock_probe, \
             patch("modules.speech_recognizer.whisper.load_model") as mock_whisper, \
             patch("modules.translator.AsyncOpenAI") as mock_openai:
            
            # Setup basic mocks
            mock_probe.return_value = {
                'streams': [{'codec_type': 'audio'}],
                'format': {'duration': '10.0'}
            }
            
            mock_whisper_model = Mock()
            mock_whisper_model.transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en"
            }
            mock_whisper.return_value = mock_whisper_model
            
            mock_openai_client = AsyncMock()
            mock_openai_client.chat.completions.create = AsyncMock()
            mock_openai.return_value = mock_openai_client
            
            # Track temp directory
            temp_dirs = []
            original_mkdtemp = tempfile.mkdtemp
            
            def track_mkdtemp(*args, **kwargs):
                temp_dir = original_mkdtemp(*args, **kwargs)
                temp_dirs.append(temp_dir)
                # Create dummy audio file
                Path(temp_dir, "audio.wav").write_bytes(b"dummy")
                return temp_dir
            
            with patch("tempfile.mkdtemp", side_effect=track_mkdtemp):
                # Run without keep_temp
                await generator.process_video(
                    video_path=sample_video_path,
                    target_language="zh",
                    output_dir=temp_dir,
                    keep_temp=False
                )
            
            # Verify temp directory was cleaned up
            assert len(temp_dirs) == 1
            assert not Path(temp_dirs[0]).exists()