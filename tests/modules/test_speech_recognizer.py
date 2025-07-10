"""
Tests for SpeechRecognizer module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

from modules.speech_recognizer import SpeechRecognizer


class TestSpeechRecognizer:
    """Test cases for SpeechRecognizer"""
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_init_with_cpu(self, mock_load_model):
        """Test SpeechRecognizer initialization with CPU"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        
        assert recognizer.model_name == "base"
        assert recognizer.device == "cpu"
        mock_load_model.assert_called_once_with("base", device="cpu")
    
    @patch("modules.speech_recognizer.torch.cuda.is_available")
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_init_with_gpu(self, mock_load_model, mock_cuda_available):
        """Test SpeechRecognizer initialization with GPU"""
        mock_cuda_available.return_value = True
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base", device="auto")
        
        assert recognizer.device == "cuda"
        mock_load_model.assert_called_once_with("base", device="cuda")
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_transcribe_success(self, mock_load_model, sample_audio_path):
        """Test successful transcription"""
        # Setup mock model
        mock_model = Mock()
        mock_result = {
            "text": "Hello world. This is a test.",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello world",
                    "tokens": [50364, 15947, 1002, 50514],
                    "temperature": 0.0,
                    "avg_logprob": -0.2,
                    "compression_ratio": 1.5,
                    "no_speech_prob": 0.01
                }
            ],
            "language": "en"
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        result = recognizer.transcribe(sample_audio_path)
        
        assert result["text"] == "Hello world. This is a test."
        assert len(result["segments"]) == 1
        assert result["language"] == "en"
        
        # Verify transcribe was called with correct parameters
        mock_model.transcribe.assert_called_once()
        call_args = mock_model.transcribe.call_args
        assert str(sample_audio_path) == call_args[0][0]
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_transcribe_with_language(self, mock_load_model, sample_audio_path):
        """Test transcription with specified language"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "你好世界",
            "segments": [],
            "language": "zh"
        }
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        result = recognizer.transcribe(sample_audio_path, language="zh")
        
        # Verify language parameter was passed
        mock_model.transcribe.assert_called_once()
        kwargs = mock_model.transcribe.call_args[1]
        assert kwargs.get("language") == "zh"
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_transcribe_file_not_found(self, mock_load_model):
        """Test transcription with non-existent file"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        
        with pytest.raises(FileNotFoundError):
            recognizer.transcribe(Path("nonexistent.wav"))
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_transcribe_with_task(self, mock_load_model, sample_audio_path):
        """Test transcription with translate task"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "segments": [],
            "language": "zh"
        }
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        result = recognizer.transcribe(sample_audio_path, task="translate")
        
        # Verify task parameter was passed
        kwargs = mock_model.transcribe.call_args[1]
        assert kwargs.get("task") == "translate"
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_model_sizes(self, mock_load_model):
        """Test different model sizes"""
        model_sizes = ["tiny", "base", "small", "medium", "large"]
        
        for size in model_sizes:
            mock_model = Mock()
            mock_load_model.return_value = mock_model
            
            recognizer = SpeechRecognizer(model_name=size)
            assert recognizer.model_name == size
            mock_load_model.assert_called_with(size, device="cpu")
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_transcribe_with_options(self, mock_load_model, sample_audio_path):
        """Test transcription with various options"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Test",
            "segments": [],
            "language": "en"
        }
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        
        # Test with different options
        result = recognizer.transcribe(
            sample_audio_path,
            language="en",
            task="transcribe",
            temperature=0.0,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4
        )
        
        # Verify all options were passed
        kwargs = mock_model.transcribe.call_args[1]
        assert kwargs.get("temperature") == 0.0
        assert kwargs.get("no_speech_threshold") == 0.6
        assert kwargs.get("logprob_threshold") == -1.0
        assert kwargs.get("compression_ratio_threshold") == 2.4
    
    @patch("modules.speech_recognizer.whisper.load_model")
    def test_get_supported_languages(self, mock_load_model):
        """Test getting supported languages"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        recognizer = SpeechRecognizer(model_name="base")
        
        # Common languages that should be supported
        common_languages = ["en", "zh", "es", "fr", "de", "ja", "ko", "ru"]
        supported = recognizer.get_supported_languages()
        
        for lang in common_languages:
            assert lang in supported