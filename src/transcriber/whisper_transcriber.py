"""Whisper 语音识别模块 - 使用 OpenAI Whisper API"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel
import subprocess
import math

from ..config.settings import get_settings
from ..utils.helpers import get_file_size, ensure_dir
from ..utils.exceptions import ConfigurationError, TranscriptionError, AudioExtractionError


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
            raise ConfigurationError("OpenAI API key not configured", config_key="openai.api_key")
            
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
            raise FileProcessingError(f"Audio file not found: {audio_path}", file_path=str(audio_path))
            
        self.logger.info(f"Starting transcription: {audio_path}")
        
        # 检查文件大小
        file_size_mb = get_file_size(audio_path) / (1024 * 1024)
        self.logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # OpenAI Whisper API 文件大小限制为 25MB
        if file_size_mb > 25:
            raise ValidationError(
                f"Audio file too large: {file_size_mb:.2f} MB. "
                "Maximum supported size is 25 MB. "
                "Please use shorter audio segments.",
                field="file_size", value=file_size_mb
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
            raise TranscriptionError(f"Transcription failed: {str(e)}", audio_path=str(audio_path)) from e
    
    def transcribe_with_chunks(self, audio_path: Path, chunk_duration: int = 300) -> TranscriptionResult:
        """分段转录长音频文件
        
        当音频文件超过 25MB 时，自动分段处理。
        
        Args:
            audio_path: 音频文件路径
            chunk_duration: 每个分段的时长（秒），默认5分钟
            
        Returns:
            合并后的转录结果
        """
        # 检查文件大小
        file_size_mb = get_file_size(audio_path) / (1024 * 1024)
        
        # 如果文件小于 20MB（留一些余量），直接转录
        if file_size_mb < 20:
            return self.transcribe(audio_path)
        
        # 获取音频时长
        audio_duration = self._get_audio_duration(audio_path)
        
        # 计算分段数量
        num_chunks = math.ceil(audio_duration / chunk_duration)
        self.logger.info(f"音频时长 {audio_duration:.1f}秒，将分为 {num_chunks} 个分段处理")
        
        # 分段处理
        all_segments = []
        temp_dir = audio_path.parent / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            for i in range(num_chunks):
                start_time = i * chunk_duration
                duration = min(chunk_duration, audio_duration - start_time)
                
                # 切分音频
                chunk_path = temp_dir / f"chunk_{i:03d}.wav"
                self._split_audio(audio_path, chunk_path, start_time, duration)
                
                # 转录分段
                self.logger.info(f"转录分段 {i+1}/{num_chunks}...")
                chunk_result = self.transcribe(chunk_path)
                
                # 调整时间戳
                for segment in chunk_result.segments:
                    adjusted_segment = TranscriptionSegment(
                        text=segment.text,
                        start=segment.start + start_time,
                        end=segment.end + start_time
                    )
                    all_segments.append(adjusted_segment)
                
                # 删除临时文件
                chunk_path.unlink()
            
            # 合并结果
            full_text = " ".join(seg.text for seg in all_segments)
            result = TranscriptionResult(
                text=full_text,
                segments=all_segments,
                language=chunk_result.language if 'chunk_result' in locals() else 'auto',
                duration=audio_duration
            )
            
            self.logger.info(f"分段转录完成，总计 {len(all_segments)} 个片段")
            return result
            
        finally:
            # 清理临时目录
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except:
                    pass  # 忽略删除失败
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频文件时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            时长（秒）
        """
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            raise AudioExtractionError(f"获取音频时长失败: {e}", audio_path=str(audio_path))
    
    def _split_audio(self, input_path: Path, output_path: Path, start: float, duration: float) -> None:
        """切分音频文件
        
        Args:
            input_path: 输入音频路径
            output_path: 输出音频路径
            start: 开始时间（秒）
            duration: 持续时间（秒）
        """
        try:
            cmd = [
                'ffmpeg', '-y', '-i', str(input_path),
                '-ss', str(start),
                '-t', str(duration),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            raise AudioExtractionError(f"切分音频失败: {e}")
    
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