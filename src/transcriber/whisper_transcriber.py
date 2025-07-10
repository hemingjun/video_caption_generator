"""Whisper 语音识别模块 - 使用 OpenAI Whisper API"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel

from ..config.settings import get_settings
from ..utils.helpers import get_file_size, ensure_dir


class TranscriptionSegment(BaseModel):
    """转录片段"""
    text: str
    start: float
    end: float
    
    
class TranscriptionResult(BaseModel):
    """转录结果"""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float


class WhisperTranscriber:
    """Whisper 语音识别器"""
    
    def __init__(self):
        """初始化语音识别器"""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # 初始化 OpenAI 客户端
        api_key = self.settings.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")
            
        self.client = OpenAI(api_key=api_key)
        self.chunk_duration = self.settings.processing.chunk_duration
        
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """转录音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录结果
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        self.logger.info(f"Starting transcription: {audio_path}")
        
        # 检查文件大小
        file_size_mb = get_file_size(audio_path) / (1024 * 1024)
        self.logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # OpenAI Whisper API 文件大小限制为 25MB
        if file_size_mb > 25:
            raise ValueError(
                f"Audio file too large: {file_size_mb:.2f} MB. "
                "Maximum supported size is 25 MB. "
                "Please use shorter audio segments."
            )
        
        try:
            # 调用 Whisper API
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    temperature=0.0
                )
            
            # 解析响应
            segments = []
            for seg in response.segments:
                segments.append(TranscriptionSegment(
                    text=seg.text.strip(),
                    start=seg.start,
                    end=seg.end
                ))
            
            result = TranscriptionResult(
                text=response.text,
                segments=segments,
                language=response.language,
                duration=response.duration
            )
            
            self.logger.info(
                f"Transcription completed: {len(segments)} segments, "
                f"duration: {result.duration:.2f}s, language: {result.language}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Transcription failed: {str(e)}") from e
    
    def transcribe_with_chunks(self, audio_path: Path) -> TranscriptionResult:
        """分段转录长音频文件（预留接口）
        
        注意：当前版本要求音频文件小于 25MB。
        未来版本将支持自动分段处理大文件。
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录结果
        """
        # 当前版本直接调用基础转录功能
        # 未来可扩展为支持音频分段处理
        return self.transcribe(audio_path)
    
    def format_transcript(self, result: TranscriptionResult) -> str:
        """格式化转录结果为文本
        
        Args:
            result: 转录结果
            
        Returns:
            格式化的文本
        """
        lines = []
        for segment in result.segments:
            timestamp = self._format_timestamp(segment.start)
            lines.append(f"[{timestamp}] {segment.text}")
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间戳 (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"