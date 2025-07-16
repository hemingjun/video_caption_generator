"""时间戳重分配模块"""
import re
import logging
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

from ..config.settings import get_settings


class SentenceInfo(BaseModel):
    """句子信息"""
    text: str
    char_count: int
    punctuation: str
    weight: float  # 时长权重


class TimestampRedistributor:
    """时间戳重分配器"""
    
    def __init__(self):
        """初始化重分配器"""
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # 配置参数
        self.sentence_min_gap = self.settings.translation.sentence_min_gap
        self.punctuation_weights = self.settings.translation.punctuation_pause_weights
        self.target_speech_rate = self.settings.translation.target_speech_rate
    
    def redistribute_timestamps(
        self, 
        translated_text: str,
        original_start: float,
        original_end: float,
        original_segments: List[Any] = None
    ) -> List[Dict[str, Any]]:
        """重新分配时间戳
        
        Args:
            translated_text: 翻译后的完整文本
            original_start: 原始开始时间
            original_end: 原始结束时间
            original_segments: 原始片段（用于对齐）
            
        Returns:
            重新分配时间戳后的片段列表（字典格式）
        """
        # 总可用时长
        total_duration = original_end - original_start
        self.logger.info(
            f"开始时间戳重分配：总时长 {total_duration:.1f}秒，"
            f"文本长度 {len(translated_text)} 字符"
        )
        
        # 分句
        sentences = self._split_into_sentences(translated_text)
        if not sentences:
            return []
        
        self.logger.debug(f"分割成 {len(sentences)} 个句子")
        
        # 计算每个句子的权重
        sentence_infos = self._analyze_sentences(sentences)
        
        # 分配时间戳
        redistributed_segments = self._allocate_timestamps(
            sentence_infos,
            original_start,
            total_duration
        )
        
        # 如果提供了原始片段，尝试保持一些关键对齐点
        if original_segments:
            redistributed_segments = self._align_key_points(
                redistributed_segments,
                original_segments
            )
        
        self.logger.info(f"时间戳重分配完成：生成 {len(redistributed_segments)} 个片段")
        return redistributed_segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """智能分句
        
        Args:
            text: 待分句的文本
            
        Returns:
            句子列表
        """
        # 定义句子结束标记
        sentence_endings = r'[。！？.!?]+'
        
        # 使用正则表达式分割，但保留标点
        parts = re.split(f'({sentence_endings})', text)
        
        sentences = []
        current_sentence = ""
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # 文本部分
                current_sentence = part.strip()
            else:  # 标点部分
                if current_sentence:
                    sentences.append(current_sentence + part)
                    current_sentence = ""
        
        # 处理最后可能没有标点的句子
        if current_sentence:
            sentences.append(current_sentence)
        
        # 过滤空句子
        sentences = [s for s in sentences if s.strip()]
        
        # 处理逗号分割（对于过长的句子）
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > 50:  # 如果句子太长
                # 尝试按逗号分割
                comma_parts = self._split_by_comma(sentence)
                final_sentences.extend(comma_parts)
            else:
                final_sentences.append(sentence)
        
        return final_sentences
    
    def _split_by_comma(self, sentence: str) -> List[str]:
        """按逗号智能分割长句
        
        Args:
            sentence: 长句子
            
        Returns:
            分割后的句子列表
        """
        # 检查是否需要分割
        if len(sentence) < 50 or '，' not in sentence and ',' not in sentence:
            return [sentence]
        
        # 提取句末标点
        sentence_ending = ''
        for ending in ['。', '！', '？', '.', '!', '?']:
            if sentence.endswith(ending):
                sentence_ending = ending
                sentence = sentence[:-len(ending)]
                break
        
        # 按逗号分割
        parts = re.split(r'[，,]', sentence)
        
        # 重组句子，确保每部分不太短
        result = []
        current = ""
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
                
            if not current:
                current = part
            elif len(current) + len(part) < 30:  # 如果合并后不太长
                current += "，" + part
            else:
                # 添加逗号或句号
                if i == len(parts) - 1 and sentence_ending:
                    current += sentence_ending
                else:
                    current += "，"
                result.append(current)
                current = part
        
        # 处理最后一部分
        if current:
            if sentence_ending:
                current += sentence_ending
            result.append(current)
        
        return result if result else [sentence + sentence_ending]
    
    def _analyze_sentences(self, sentences: List[str]) -> List[SentenceInfo]:
        """分析句子信息
        
        Args:
            sentences: 句子列表
            
        Returns:
            句子信息列表
        """
        sentence_infos = []
        
        for sentence in sentences:
            # 统计字符数（不包括标点和空格）
            char_count = len(re.sub(r'[^\w]', '', sentence))
            
            # 识别句末标点
            punctuation = ''
            for char in reversed(sentence):
                if char in self.punctuation_weights:
                    punctuation = char
                    break
            
            # 计算权重（字符数 + 标点停顿）
            base_weight = char_count / self.target_speech_rate * 60  # 基础时长（秒）
            pause_weight = self.punctuation_weights.get(punctuation, 0.5)
            total_weight = base_weight + pause_weight * self.sentence_min_gap
            
            info = SentenceInfo(
                text=sentence,
                char_count=char_count,
                punctuation=punctuation,
                weight=total_weight
            )
            sentence_infos.append(info)
            
            self.logger.debug(
                f"句子分析: '{sentence[:20]}...' "
                f"字数={char_count}, 标点='{punctuation}', "
                f"权重={total_weight:.2f}秒"
            )
        
        return sentence_infos
    
    def _allocate_timestamps(
        self,
        sentence_infos: List[SentenceInfo],
        start_time: float,
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """分配时间戳
        
        Args:
            sentence_infos: 句子信息列表
            start_time: 开始时间
            total_duration: 总时长
            
        Returns:
            带时间戳的片段列表
        """
        # 计算总权重
        total_weight = sum(info.weight for info in sentence_infos)
        
        # 计算需要的最小总时长（考虑句间间隔）
        min_gaps_duration = self.sentence_min_gap * (len(sentence_infos) - 1)
        available_duration = total_duration - min_gaps_duration
        
        if available_duration <= 0:
            # 时间不够，使用最小间隔
            self.logger.warning(
                f"可用时长不足：总时长={total_duration:.1f}s, "
                f"最小间隔需要={min_gaps_duration:.1f}s"
            )
            available_duration = total_duration
            actual_gap = 0
        else:
            actual_gap = self.sentence_min_gap
        
        # 分配时间戳
        segments = []
        current_time = start_time
        
        for i, info in enumerate(sentence_infos):
            # 计算该句子的时长
            if i == len(sentence_infos) - 1:
                # 最后一句，使用剩余时间
                duration = (start_time + total_duration) - current_time
            else:
                # 按权重比例分配
                duration = (info.weight / total_weight) * available_duration
            
            # 确保最小时长
            duration = max(0.5, duration)
            
            # 创建片段
            segment = {
                "original": "",  # 段落模式下原文为空
                "translated": info.text,
                "start": current_time,
                "end": current_time + duration
            }
            segments.append(segment)
            
            # 更新时间指针
            current_time = segment["end"]
            if i < len(sentence_infos) - 1:
                current_time += actual_gap
        
        # 确保最后一个片段不超过总时长
        if segments and segments[-1]["end"] > start_time + total_duration:
            segments[-1]["end"] = start_time + total_duration
        
        return segments
    
    def _align_key_points(
        self,
        redistributed: List[Dict[str, Any]],
        original: List[Any]
    ) -> List[Dict[str, Any]]:
        """对齐关键时间点（可选功能）
        
        Args:
            redistributed: 重分配后的片段
            original: 原始片段
            
        Returns:
            调整后的片段
        """
        # 暂时直接返回重分配结果
        # 未来可以实现更复杂的对齐逻辑
        return redistributed