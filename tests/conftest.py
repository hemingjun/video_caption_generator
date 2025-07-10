"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import os

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_video_path(temp_dir):
    """Create a dummy video file for testing"""
    video_path = temp_dir / "test_video.mp4"
    video_path.write_bytes(b"dummy video content")
    return video_path


@pytest.fixture
def sample_audio_path(temp_dir):
    """Create a dummy audio file for testing"""
    audio_path = temp_dir / "test_audio.wav"
    audio_path.write_bytes(b"dummy audio content")
    return audio_path


@pytest.fixture
def mock_settings():
    """Mock settings object"""
    settings = Mock()
    settings.api.openai_api_key = "test-openai-key"
    settings.api.claude_api_key = "test-claude-key"
    settings.translation.openai_model = "gpt-4"
    settings.translation.claude_model = "claude-3-opus-20240229"
    settings.translation.cache_enabled = True
    settings.whisper.device = "cpu"
    settings.whisper.compute_type = "int8"
    settings.output.default_formats = ["srt", "txt"]
    settings.output.default_dir = Path("./output")
    return settings


@pytest.fixture
def sample_segments():
    """Sample transcription segments"""
    return [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "Hello world",
            "tokens": [50364, 15947, 1002, 50514],
            "temperature": 0.0,
            "avg_logprob": -0.2,
            "compression_ratio": 1.5,
            "no_speech_prob": 0.01
        },
        {
            "start": 2.5,
            "end": 5.0,
            "text": "This is a test",
            "tokens": [50514, 1047, 307, 257, 1500, 50664],
            "temperature": 0.0,
            "avg_logprob": -0.15,
            "compression_ratio": 1.3,
            "no_speech_prob": 0.02
        }
    ]


@pytest.fixture
def sample_transcription(sample_segments):
    """Sample Whisper transcription result"""
    return {
        "text": "Hello world. This is a test.",
        "segments": sample_segments,
        "language": "en"
    }


@pytest.fixture
def mock_ffmpeg(monkeypatch):
    """Mock ffmpeg commands"""
    def mock_run(*args, **kwargs):
        return Mock(stdout=b"", stderr=b"", returncode=0)
    
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model"""
    model = Mock()
    model.transcribe = Mock()
    model.device = "cpu"
    return model


@pytest.fixture
def env_setup(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.setenv("VCG_ENV", "test")