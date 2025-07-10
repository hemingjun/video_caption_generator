"""文本格式化模块"""
import logging
from pathlib import Path
from typing import List, Optional

from ..translator.openai_translator import TranslationSegment


class TextFormatter:
    """文本格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        self.logger = logging.getLogger(__name__)
        
    def format(
        self,
        segments: List[TranslationSegment],
        include_original: bool = True
    ) -> str:
        """格式化为纯文本
        
        Args:
            segments: 翻译片段列表
            include_original: 是否包含原文
            
        Returns:
            格式化的文本
        """
        if not segments:
            return ""
        
        lines = []
        
        for segment in segments:
            if include_original:
                # 原文译文对照格式
                lines.append(segment.original)
                lines.append(segment.translated)
                lines.append("")  # 空行分隔
            else:
                # 仅译文
                lines.append(segment.translated)
        
        return "\n".join(lines)
    
    def save(
        self,
        segments: List[TranslationSegment],
        output_path: Path,
        include_original: bool = True
    ) -> None:
        """保存为文本文件
        
        Args:
            segments: 翻译片段列表
            output_path: 输出文件路径
            include_original: 是否包含原文
        """
        text_content = self.format(segments, include_original)
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        self.logger.info(f"Text file saved: {output_path}")
    
    def format_with_timestamps(
        self,
        segments: List[TranslationSegment],
        include_original: bool = True
    ) -> str:
        """格式化为带时间戳的文本（用于调试）
        
        Args:
            segments: 翻译片段列表
            include_original: 是否包含原文
            
        Returns:
            带时间戳的文本
        """
        if not segments:
            return ""
        
        lines = []
        
        for segment in segments:
            timestamp = self._format_timestamp(segment.start)
            if include_original:
                lines.append(f"[{timestamp}] {segment.original}")
                lines.append(f"           {segment.translated}")
                lines.append("")
            else:
                lines.append(f"[{timestamp}] {segment.translated}")
        
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