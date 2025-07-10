"""SRT 字幕格式化模块"""
import logging
from pathlib import Path
from typing import List, Optional

from ..translator.openai_translator import TranslationSegment


class SRTFormatter:
    """SRT 字幕格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        self.logger = logging.getLogger(__name__)
        
    def format(
        self,
        segments: List[TranslationSegment],
        include_original: bool = True
    ) -> str:
        """格式化为 SRT 字幕
        
        Args:
            segments: 翻译片段列表
            include_original: 是否包含原文
            
        Returns:
            SRT 格式字符串
        """
        if not segments:
            return ""
        
        srt_lines = []
        
        for idx, segment in enumerate(segments, 1):
            # 序号
            srt_lines.append(str(idx))
            
            # 时间戳
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            srt_lines.append(f"{start_time} --> {end_time}")
            
            # 内容
            if include_original:
                srt_lines.append(segment.original)
                srt_lines.append(segment.translated)
            else:
                srt_lines.append(segment.translated)
            
            # 空行分隔
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def save(
        self,
        segments: List[TranslationSegment],
        output_path: Path,
        include_original: bool = True
    ) -> None:
        """保存为 SRT 文件
        
        Args:
            segments: 翻译片段列表
            output_path: 输出文件路径
            include_original: 是否包含原文
        """
        srt_content = self.format(segments, include_original)
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        
        self.logger.info(f"SRT file saved: {output_path}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为 SRT 格式
        
        Args:
            seconds: 秒数
            
        Returns:
            SRT 时间戳格式 (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        whole_secs = int(secs)
        millis = int((secs - whole_secs) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{whole_secs:02d},{millis:03d}"