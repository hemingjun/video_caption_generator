"""语音识别模块"""
from .whisper_transcriber import WhisperTranscriber, TranscriptionResult, TranscriptionSegment

__all__ = ['WhisperTranscriber', 'TranscriptionResult', 'TranscriptionSegment']