"""SRT 字幕格式化模块"""
import logging
from pathlib import Path
from typing import List, Optional

from ..translator.openai_translator import TranslationSegment
from ..config.settings import get_settings


class SRTFormatter:
    """SRT 字幕格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.gap_duration = self.settings.translation.gap_duration
        
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
            
            # 时间戳（结束时间减去间隔）
            start_time = self._format_timestamp(segment.start)
            # 确保结束时间不小于开始时间
            adjusted_end = max(segment.start + 0.1, segment.end - self.gap_duration)
            end_time = self._format_timestamp(adjusted_end)
            srt_lines.append(f"{start_time} --> {end_time}")
            
            # 内容（验证并清理）
            if include_original:
                # 验证原文
                original_text = self._validate_text(segment.original, f"segment {idx} original")
                srt_lines.append(original_text)
                
            # 验证翻译文本
            translated_text = self._validate_text(segment.translated, f"segment {idx} translated")
            srt_lines.append(translated_text)
            
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
    
    def _validate_text(self, text: str, context: str = "") -> str:
        """验证和清理文本内容
        
        Args:
            text: 要验证的文本
            context: 上下文信息（用于日志）
            
        Returns:
            清理后的文本
        """
        # 检查是否包含JSON格式
        if text.strip().startswith(('[', '{')) or '```' in text:
            self.logger.warning(f"Detected JSON/markdown content in {context}: {text[:100]}...")
            
            # 尝试提取纯文本
            import re
            # 移除markdown代码块标记
            text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
            # 如果是JSON数组，尝试提取第一个元素
            if text.strip().startswith('['):
                try:
                    import json
                    items = json.loads(text)
                    if isinstance(items, list) and items:
                        text = str(items[0])
                        self.logger.info(f"Extracted first item from JSON array in {context}")
                except:
                    # 如果解析失败，返回错误消息
                    text = f"[格式错误：{context}]"
                    self.logger.error(f"Failed to parse JSON in {context}")
        
        # 清理多余的空白字符
        text = text.strip()
        
        # 确保文本不为空
        if not text:
            text = f"[空白内容：{context}]"
            self.logger.warning(f"Empty content in {context}")
        
        return text