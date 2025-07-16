"""段落边界检测模块"""
import logging
from typing import List, Tuple
from pydantic import BaseModel

from ..transcriber.whisper_transcriber import TranscriptionSegment
from ..config.settings import get_settings


class Paragraph(BaseModel):
    """段落数据结构"""
    segments: List[TranscriptionSegment]
    start: float
    end: float
    text: str
    
    @property
    def duration(self) -> float:
        """段落时长"""
        return self.end - self.start


class ParagraphDetector:
    """段落边界检测器"""
    
    def __init__(self):
        """初始化检测器"""
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # 段落检测参数
        self.silence_threshold = self.settings.translation.paragraph_silence_threshold
        self.max_duration = self.settings.translation.paragraph_max_duration
        self.min_duration = self.settings.translation.paragraph_min_duration
    
    def detect_paragraphs(self, segments: List[TranscriptionSegment]) -> List[Paragraph]:
        """检测段落边界，将片段组合成段落
        
        Args:
            segments: 转录片段列表
            
        Returns:
            段落列表
        """
        if not segments:
            return []
        
        self.logger.info(f"开始段落检测：{len(segments)} 个片段")
        
        paragraphs = []
        current_segments = []
        paragraph_start = segments[0].start
        
        for i, segment in enumerate(segments):
            current_segments.append(segment)
            
            # 检查是否应该结束当前段落
            should_end_paragraph = False
            
            # 1. 检查是否是最后一个片段
            if i == len(segments) - 1:
                should_end_paragraph = True
            else:
                # 2. 检查与下一个片段的时间间隔
                next_segment = segments[i + 1]
                silence_duration = next_segment.start - segment.end
                
                if silence_duration >= self.silence_threshold:
                    self.logger.debug(
                        f"检测到静音间隔 {silence_duration:.1f}秒，"
                        f"位置: {segment.end:.1f}s"
                    )
                    should_end_paragraph = True
                
                # 3. 检查段落时长
                current_duration = segment.end - paragraph_start
                if current_duration >= self.max_duration:
                    self.logger.debug(
                        f"段落达到最大时长 {current_duration:.1f}秒"
                    )
                    should_end_paragraph = True
                
                # 4. 检查语义完整性（句末标点）
                if self._is_sentence_end(segment.text) and current_duration >= self.min_duration:
                    # 如果下一句开头是小写或连词，不分段
                    if not self._should_continue_with_next(segment.text, next_segment.text):
                        should_end_paragraph = True
            
            # 创建段落
            if should_end_paragraph and current_segments:
                paragraph_text = " ".join(seg.text for seg in current_segments)
                paragraph = Paragraph(
                    segments=current_segments.copy(),
                    start=paragraph_start,
                    end=segment.end,
                    text=paragraph_text
                )
                
                # 检查段落最小时长
                if paragraph.duration >= self.min_duration or i == len(segments) - 1:
                    paragraphs.append(paragraph)
                    self.logger.debug(
                        f"创建段落 {len(paragraphs)}: "
                        f"[{paragraph.start:.1f}-{paragraph.end:.1f}] "
                        f"时长 {paragraph.duration:.1f}秒, "
                        f"包含 {len(paragraph.segments)} 个片段"
                    )
                    current_segments = []
                    if i < len(segments) - 1:
                        paragraph_start = segments[i + 1].start
                else:
                    # 段落太短，继续累积
                    self.logger.debug(
                        f"段落时长 {paragraph.duration:.1f}秒 小于最小时长，继续累积"
                    )
        
        self.logger.info(f"段落检测完成：生成 {len(paragraphs)} 个段落")
        return paragraphs
    
    def _is_sentence_end(self, text: str) -> bool:
        """判断文本是否以句末标点结尾
        
        Args:
            text: 文本
            
        Returns:
            是否是句末
        """
        sentence_endings = [
            '.', '!', '?', '。', '！', '？',
            '."', '!"', '?"', '。"', '！"', '？"',
            ".\'", "!\'", "?\'", "。'", "！'", "？'"
        ]
        
        text = text.strip()
        return any(text.endswith(ending) for ending in sentence_endings)
    
    def _should_continue_with_next(self, current_text: str, next_text: str) -> bool:
        """判断是否应该与下一句继续组成段落
        
        Args:
            current_text: 当前句子
            next_text: 下一句子
            
        Returns:
            是否应该继续
        """
        # 检查下一句是否以小写字母开头
        if next_text and next_text[0].islower():
            return True
        
        # 检查下一句是否以连词或从句引导词开头
        continuations = [
            'but', 'and', 'or', 'so', 'yet', 'because', 'although', 'though',
            'while', 'whereas', 'since', 'unless', 'if', 'when', 'where',
            'which', 'that', 'who', 'whom', 'whose'
        ]
        
        next_lower = next_text.lower()
        return any(next_lower.startswith(word) for word in continuations)
    
    def merge_short_paragraphs(self, paragraphs: List[Paragraph]) -> List[Paragraph]:
        """合并过短的段落
        
        Args:
            paragraphs: 原始段落列表
            
        Returns:
            合并后的段落列表
        """
        if not paragraphs:
            return paragraphs
        
        merged = []
        i = 0
        
        while i < len(paragraphs):
            current = paragraphs[i]
            
            # 如果当前段落太短且不是最后一个
            if current.duration < self.min_duration and i < len(paragraphs) - 1:
                # 尝试与下一个段落合并
                next_para = paragraphs[i + 1]
                combined_duration = next_para.end - current.start
                
                # 如果合并后不超过最大时长，则合并
                if combined_duration <= self.max_duration:
                    combined_segments = current.segments + next_para.segments
                    combined_text = current.text + " " + next_para.text
                    
                    merged_paragraph = Paragraph(
                        segments=combined_segments,
                        start=current.start,
                        end=next_para.end,
                        text=combined_text
                    )
                    merged.append(merged_paragraph)
                    i += 2  # 跳过下一个段落
                    
                    self.logger.debug(
                        f"合并短段落：{current.duration:.1f}s + {next_para.duration:.1f}s "
                        f"= {merged_paragraph.duration:.1f}s"
                    )
                    continue
            
            # 否则保持原样
            merged.append(current)
            i += 1
        
        return merged