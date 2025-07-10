"""OpenAI 翻译模块"""
import logging
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel

from ..config.settings import get_settings
from ..transcriber.whisper_transcriber import TranscriptionSegment


class TranslationSegment(BaseModel):
    """翻译片段"""
    original: str
    translated: str
    start: float
    end: float


class TranslationResult(BaseModel):
    """翻译结果"""
    segments: List[TranslationSegment]
    source_language: str
    target_language: str


class OpenAITranslator:
    """OpenAI 翻译器"""
    
    def __init__(self):
        """初始化翻译器"""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # 初始化 OpenAI 客户端
        api_key = self.settings.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")
            
        self.client = OpenAI(api_key=api_key)
        self.model = self.settings.openai.model
        self.batch_size = self.settings.translation.batch_size
        self.target_language = self.settings.translation.target_language
        
    def translate(
        self, 
        segments: List[TranscriptionSegment],
        source_language: str
    ) -> TranslationResult:
        """翻译转录片段
        
        Args:
            segments: 转录片段列表
            source_language: 源语言
            
        Returns:
            翻译结果
        """
        if not segments:
            return TranslationResult(
                segments=[],
                source_language=source_language,
                target_language=self.target_language
            )
        
        self.logger.info(
            f"Starting translation: {len(segments)} segments, "
            f"{source_language} -> {self.target_language}"
        )
        
        # 合并不完整的句子
        merged_segments = self._merge_incomplete_segments(segments)
        self.logger.info(
            f"Merged incomplete sentences: {len(segments)} -> {len(merged_segments)} segments"
        )
        
        # 按批次处理
        translated_segments = []
        for i in range(0, len(merged_segments), self.batch_size):
            batch = merged_segments[i:i + self.batch_size]
            batch_result = self._translate_batch(batch, source_language)
            translated_segments.extend(batch_result)
        
        result = TranslationResult(
            segments=translated_segments,
            source_language=source_language,
            target_language=self.target_language
        )
        
        self.logger.info(f"Translation completed: {len(translated_segments)} segments")
        return result
    
    def _translate_batch(
        self,
        segments: List[TranscriptionSegment],
        source_language: str
    ) -> List[TranslationSegment]:
        """批量翻译片段
        
        Args:
            segments: 转录片段批次
            source_language: 源语言
            
        Returns:
            翻译片段列表
        """
        # 准备批量翻译请求
        texts = [seg.text for seg in segments]
        
        # 添加调试信息
        self.logger.info(f"Translating batch of {len(texts)} texts")
        self.logger.debug(f"Texts to translate: {texts}")
        
        # 构建系统提示
        system_prompt = self._build_system_prompt(source_language)
        
        # 构建用户消息
        user_message = self._build_batch_message(texts)
        
        try:
            # 调用 OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析响应
            content = response.choices[0].message.content
            self.logger.debug(f"API response: {content}")
            
            translations = self._parse_translations(content)
            self.logger.info(f"Parsed {len(translations)} translations")
            
            # 检查翻译数量是否匹配
            if len(translations) != len(segments):
                self.logger.warning(
                    f"Translation count mismatch: "
                    f"expected {len(segments)}, got {len(translations)}. "
                    f"Using intelligent alignment."
                )
                self.logger.debug(f"Original texts: {texts}")
                self.logger.debug(f"Translations received: {translations}")
                
                # 使用智能对齐
                return self._align_translations(segments, translations)
            
            # 数量匹配时的正常处理
            result = []
            for seg, trans in zip(segments, translations):
                result.append(TranslationSegment(
                    original=seg.text,
                    translated=trans,
                    start=seg.start,
                    end=seg.end
                ))
                
            return result
            
        except Exception as e:
            self.logger.error(f"Translation batch failed: {str(e)}")
            raise RuntimeError(f"Translation failed: {str(e)}") from e
    
    def _build_system_prompt(self, source_language: str) -> str:
        """构建系统提示
        
        Args:
            source_language: 源语言
            
        Returns:
            系统提示
        """
        target_lang_name = self._get_language_name(self.target_language)
        
        prompt = f"""You are a professional translator specializing in video subtitles.
Translate the following text segments from {source_language} to {target_lang_name}.

Requirements:
1. Maintain the original meaning and tone
2. Keep translations concise for subtitle display
3. Preserve proper nouns and technical terms appropriately
4. Return translations in the exact same order as input
5. Output format: JSON array of translated strings only

Example input: ["Hello", "How are you?"]
Example output: ["你好", "你好吗？"]"""
        
        return prompt
    
    def _build_batch_message(self, texts: List[str]) -> str:
        """构建批量翻译消息
        
        Args:
            texts: 待翻译文本列表
            
        Returns:
            JSON 格式的消息
        """
        return json.dumps(texts, ensure_ascii=False)
    
    def _parse_translations(self, content: str) -> List[str]:
        """解析翻译响应
        
        Args:
            content: API 响应内容
            
        Returns:
            翻译文本列表
        """
        try:
            # 尝试解析 JSON
            translations = json.loads(content)
            if not isinstance(translations, list):
                raise ValueError("Response is not a list")
            return [str(t) for t in translations]
        except json.JSONDecodeError:
            # 如果不是有效 JSON，尝试按行分割
            lines = content.strip().split('\n')
            return [line.strip() for line in lines if line.strip()]
    
    def _get_language_name(self, code: str) -> str:
        """获取语言名称
        
        Args:
            code: 语言代码
            
        Returns:
            语言名称
        """
        language_map = {
            "zh-cn": "Simplified Chinese",
            "zh-tw": "Traditional Chinese",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian",
            "ar": "Arabic"
        }
        return language_map.get(code.lower(), code)
    
    def _merge_incomplete_segments(
        self, 
        segments: List[TranscriptionSegment]
    ) -> List[TranscriptionSegment]:
        """合并不完整的句子片段
        
        Args:
            segments: 原始转录片段列表
            
        Returns:
            合并后的片段列表
        """
        if not segments:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            current = segments[i]
            merged_text = current.text
            start_time = current.start
            end_time = current.end
            
            # 检查是否需要与后续片段合并
            j = i + 1
            while j < len(segments) and self._should_merge(merged_text, segments[j].text):
                merged_text = merged_text + " " + segments[j].text
                end_time = segments[j].end
                j += 1
            
            # 创建合并后的片段
            merged_segment = TranscriptionSegment(
                text=merged_text,
                start=start_time,
                end=end_time
            )
            merged.append(merged_segment)
            
            # 移动到下一个未处理的片段
            i = j
        
        return merged
    
    def _should_merge(self, current_text: str, next_text: str) -> bool:
        """判断是否应该合并两个句子片段
        
        Args:
            current_text: 当前句子文本
            next_text: 下一个句子文本
            
        Returns:
            是否应该合并
        """
        # 检查当前句子是否以特定标点结尾
        incomplete_endings = [',', ';', ':', '—', '–']
        ends_incomplete = any(current_text.rstrip().endswith(p) for p in incomplete_endings)
        
        # 检查下一句是否以小写字母开头（表示句子延续）
        starts_lowercase = next_text and next_text[0].islower()
        
        # 检查下一句是否以连词开头
        conjunctions = ['but', 'and', 'or', 'so', 'yet', 'because', 'although', 'though', 
                       'while', 'whereas', 'since', 'unless', 'if', 'when', 'where']
        starts_with_conjunction = any(next_text.lower().startswith(conj) for conj in conjunctions)
        
        # 检查下一句是否是从句
        subordinate_starters = ['which', 'that', 'who', 'whom', 'whose', 'where', 'when']
        starts_with_subordinate = any(next_text.lower().startswith(sub) for sub in subordinate_starters)
        
        # 如果满足任一条件，则合并
        return ends_incomplete or starts_lowercase or starts_with_conjunction or starts_with_subordinate
    
    def _align_translations(
        self,
        segments: List[TranscriptionSegment],
        translations: List[str]
    ) -> List[TranslationSegment]:
        """智能对齐翻译结果和时间戳
        
        当翻译数量与原文不匹配时，智能推测哪些句子被合并，
        并相应地调整时间戳。
        
        Args:
            segments: 原始转录片段列表
            translations: 翻译文本列表
            
        Returns:
            对齐后的翻译片段列表
        """
        aligned_segments = []
        seg_idx = 0
        
        for trans_idx, translation in enumerate(translations):
            if seg_idx >= len(segments):
                # 如果原文片段用完了，记录警告并跳过
                self.logger.warning(
                    f"Translation {trans_idx} has no corresponding original segment"
                )
                break
            
            # 开始时间取自当前原文片段
            start_time = segments[seg_idx].start
            end_time = segments[seg_idx].end
            original_texts = [segments[seg_idx].text]
            
            # 检测是否需要合并多个原文片段
            # 如果还有更多翻译要处理，且原文片段还有剩余
            remaining_translations = len(translations) - trans_idx
            remaining_segments = len(segments) - seg_idx
            
            # 如果原文片段多于剩余翻译，可能需要合并
            if remaining_segments > remaining_translations and seg_idx + 1 < len(segments):
                # 计算需要合并的片段数
                segments_to_merge = remaining_segments - remaining_translations + 1
                
                # 合并相应数量的片段
                for i in range(1, min(segments_to_merge, remaining_segments)):
                    if seg_idx + i < len(segments):
                        original_texts.append(segments[seg_idx + i].text)
                        end_time = segments[seg_idx + i].end
                
                seg_idx += segments_to_merge
            else:
                seg_idx += 1
            
            # 创建对齐的翻译片段
            aligned_segment = TranslationSegment(
                original=" ".join(original_texts),
                translated=translation,
                start=start_time,
                end=end_time
            )
            aligned_segments.append(aligned_segment)
            
            self.logger.debug(
                f"Aligned: [{start_time:.1f}-{end_time:.1f}] "
                f"{len(original_texts)} original(s) -> 1 translation"
            )
        
        # 检查是否还有未处理的原文片段
        if seg_idx < len(segments):
            self.logger.warning(
                f"{len(segments) - seg_idx} original segments were not aligned"
            )
        
        return aligned_segments