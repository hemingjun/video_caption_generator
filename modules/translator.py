"""
Translation module for Video Caption Generator
Supports OpenAI and Claude APIs
"""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import aiohttp
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


class TranslationCache:
    """Simple file-based translation cache"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize translation cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir or Path.home() / ".vcg_cache" / "translations"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "translation_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to save translation cache: {e}[/yellow]")
    
    def get(self, key: str) -> Optional[str]:
        """Get translation from cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: str):
        """Set translation in cache"""
        self.cache[key] = value
        self._save_cache()
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()


@dataclass
class TranslationSegment:
    """Represents a text segment for translation"""
    index: int
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    translated_text: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'index': self.index,
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'translated_text': self.translated_text
        }


class Translator(ABC):
    """Abstract base class for translators"""
    
    def __init__(
        self,
        api_key: str,
        target_language: str = "zh",
        max_retries: int = 3,
        timeout: int = 30,
        use_cache: bool = True
    ):
        """
        Initialize translator
        
        Args:
            api_key: API key for the service
            target_language: Target language code
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            use_cache: Whether to use translation cache
        """
        self.api_key = api_key
        self.target_language = target_language
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_cache = use_cache
        self.cache = TranslationCache() if use_cache else None
    
    @abstractmethod
    async def translate_text(self, text: str, source_lang: Optional[str] = None) -> str:
        """Translate a single text"""
        pass
    
    @abstractmethod
    async def translate_batch(
        self,
        segments: List[TranslationSegment],
        source_lang: Optional[str] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> List[TranslationSegment]:
        """Translate multiple segments"""
        pass
    
    def _get_language_name(self, code: str) -> str:
        """Convert language code to full name"""
        language_map = {
            'zh': 'Chinese',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ru': 'Russian',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'it': 'Italian',
            'nl': 'Dutch',
            'pl': 'Polish',
            'tr': 'Turkish',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            'hi': 'Hindi'
        }
        return language_map.get(code, code)
    
    def _get_cache_key(self, text: str, source_lang: Optional[str], target_lang: str) -> str:
        """Generate cache key for translation"""
        cache_string = f"{text}_{source_lang or 'auto'}_{target_lang}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _split_long_text(self, text: str, max_length: int = 4000) -> List[str]:
        """Split long text into smaller chunks"""
        if len(text) <= max_length:
            return [text]
        
        # Split by sentences
        sentences = text.replace('. ', '.|').split('|')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class OpenAITranslator(Translator):
    """OpenAI GPT-based translator"""
    
    def __init__(
        self,
        api_key: str,
        target_language: str = "zh",
        model: str = "gpt-4-turbo-preview",
        max_retries: int = 3,
        timeout: int = 30,
        use_cache: bool = True
    ):
        super().__init__(api_key, target_language, max_retries, timeout, use_cache)
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    async def translate_text(self, text: str, source_lang: Optional[str] = None) -> str:
        """Translate text using OpenAI API"""
        if not text.strip():
            return ""
        
        # Check cache first
        if self.cache:
            cache_key = self._get_cache_key(text, source_lang, self.target_language)
            cached_translation = self.cache.get(cache_key)
            if cached_translation:
                return cached_translation
        
        target_lang_name = self._get_language_name(self.target_language)
        
        # Build prompt
        system_prompt = (
            f"You are a professional translator. Translate the given text to {target_lang_name}. "
            "Maintain the original meaning and tone. Only return the translated text without any explanation."
        )
        
        if source_lang:
            source_lang_name = self._get_language_name(source_lang)
            system_prompt = (
                f"You are a professional translator. Translate the given {source_lang_name} text to {target_lang_name}. "
                "Maintain the original meaning and tone. Only return the translated text without any explanation."
            )
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                
                translated = response.choices[0].message.content.strip()
                
                # Save to cache
                if self.cache:
                    self.cache.set(cache_key, translated)
                
                return translated
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"OpenAI translation failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def translate_batch(
        self,
        segments: List[TranslationSegment],
        source_lang: Optional[str] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> List[TranslationSegment]:
        """Translate multiple segments with batching"""
        if not segments:
            return []
        
        # Group segments for batch translation
        batch_size = 10
        batches = [segments[i:i + batch_size] for i in range(0, len(segments), batch_size)]
        
        translated_segments = []
        
        for batch_idx, batch in enumerate(batches):
            # Combine texts with markers
            combined_text = "\n---\n".join([seg.text for seg in batch])
            
            # Translate combined text
            translated_combined = await self.translate_text(combined_text, source_lang)
            
            # Split translated text
            translated_parts = translated_combined.split("\n---\n")
            
            # Assign translations back to segments
            for i, seg in enumerate(batch):
                if i < len(translated_parts):
                    seg.translated_text = translated_parts[i].strip()
                else:
                    seg.translated_text = seg.text  # Fallback
                translated_segments.append(seg)
            
            # Update progress
            if progress and task_id is not None:
                completed = (batch_idx + 1) * batch_size
                progress.update(task_id, completed=min(completed, len(segments)))
        
        return translated_segments


class ClaudeTranslator(Translator):
    """Anthropic Claude-based translator"""
    
    def __init__(
        self,
        api_key: str,
        target_language: str = "zh",
        model: str = "claude-3-opus-20240229",
        max_retries: int = 3,
        timeout: int = 30,
        use_cache: bool = True
    ):
        super().__init__(api_key, target_language, max_retries, timeout, use_cache)
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)
    
    async def translate_text(self, text: str, source_lang: Optional[str] = None) -> str:
        """Translate text using Claude API"""
        if not text.strip():
            return ""
        
        # Check cache first
        if self.cache:
            cache_key = self._get_cache_key(text, source_lang, self.target_language)
            cached_translation = self.cache.get(cache_key)
            if cached_translation:
                return cached_translation
        
        target_lang_name = self._get_language_name(self.target_language)
        
        # Build prompt
        if source_lang:
            source_lang_name = self._get_language_name(source_lang)
            prompt = (
                f"Translate the following {source_lang_name} text to {target_lang_name}. "
                f"Only return the translated text without any explanation:\n\n{text}"
            )
        else:
            prompt = (
                f"Translate the following text to {target_lang_name}. "
                f"Only return the translated text without any explanation:\n\n{text}"
            )
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract text from response
                translated = response.content[0].text.strip()
                
                # Save to cache
                if self.cache:
                    self.cache.set(cache_key, translated)
                
                return translated
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Claude translation failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def translate_batch(
        self,
        segments: List[TranslationSegment],
        source_lang: Optional[str] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> List[TranslationSegment]:
        """Translate multiple segments with batching"""
        if not segments:
            return []
        
        # Similar implementation to OpenAI
        batch_size = 10
        batches = [segments[i:i + batch_size] for i in range(0, len(segments), batch_size)]
        
        translated_segments = []
        
        for batch_idx, batch in enumerate(batches):
            # Combine texts with markers
            combined_text = "\n---\n".join([seg.text for seg in batch])
            
            # Translate combined text
            translated_combined = await self.translate_text(combined_text, source_lang)
            
            # Split translated text
            translated_parts = translated_combined.split("\n---\n")
            
            # Assign translations back to segments
            for i, seg in enumerate(batch):
                if i < len(translated_parts):
                    seg.translated_text = translated_parts[i].strip()
                else:
                    seg.translated_text = seg.text  # Fallback
                translated_segments.append(seg)
            
            # Update progress
            if progress and task_id is not None:
                completed = (batch_idx + 1) * batch_size
                progress.update(task_id, completed=min(completed, len(segments)))
        
        return translated_segments


class TranslatorFactory:
    """Factory for creating translator instances"""
    
    @staticmethod
    def create_translator(
        service: str,
        api_key: str,
        target_language: str = "zh",
        **kwargs
    ) -> Translator:
        """
        Create a translator instance
        
        Args:
            service: Translation service ('openai' or 'claude')
            api_key: API key for the service
            target_language: Target language code
            **kwargs: Additional arguments for the translator
            
        Returns:
            Translator instance
            
        Raises:
            ValueError: If service is not supported
        """
        if service == "openai":
            return OpenAITranslator(api_key, target_language, **kwargs)
        elif service == "claude":
            return ClaudeTranslator(api_key, target_language, **kwargs)
        else:
            raise ValueError(f"Unsupported translation service: {service}")


async def translate_segments_with_progress(
    translator: Translator,
    segments: List[TranslationSegment],
    source_lang: Optional[str] = None
) -> List[TranslationSegment]:
    """Helper function to translate segments with progress display"""
    with Progress() as progress:
        task = progress.add_task(
            f"Translating {len(segments)} segments...",
            total=len(segments)
        )
        
        result = await translator.translate_batch(
            segments,
            source_lang,
            progress,
            task
        )
        
        return result