"""
Tests for Translator module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json
import hashlib

from modules.translator import (
    TranslationSegment,
    Translator,
    OpenAITranslator,
    ClaudeTranslator,
    TranslatorFactory,
    TranslationCache
)


class TestTranslationSegment:
    """Test cases for TranslationSegment"""
    
    def test_translation_segment_creation(self):
        """Test creating a TranslationSegment"""
        segment = TranslationSegment(
            index=0,
            text="Hello world",
            start_time=0.0,
            end_time=2.5
        )
        
        assert segment.index == 0
        assert segment.text == "Hello world"
        assert segment.start_time == 0.0
        assert segment.end_time == 2.5
        assert segment.translated_text is None
    
    def test_translation_segment_with_translation(self):
        """Test TranslationSegment with translated text"""
        segment = TranslationSegment(
            index=1,
            text="Test",
            start_time=2.5,
            end_time=3.0,
            translated_text="测试"
        )
        
        assert segment.translated_text == "测试"


class TestTranslationCache:
    """Test cases for TranslationCache"""
    
    def test_cache_init(self, temp_dir):
        """Test cache initialization"""
        cache = TranslationCache(cache_dir=temp_dir)
        assert cache.cache_dir == temp_dir
        assert cache.cache_dir.exists()
    
    def test_cache_key_generation(self, temp_dir):
        """Test cache key generation"""
        cache = TranslationCache(cache_dir=temp_dir)
        
        key = cache._get_cache_key("Hello", "en", "zh")
        expected = hashlib.md5("Hello|en|zh".encode()).hexdigest()
        assert key == expected
    
    def test_cache_get_miss(self, temp_dir):
        """Test cache miss"""
        cache = TranslationCache(cache_dir=temp_dir)
        
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_set_and_get(self, temp_dir):
        """Test setting and getting from cache"""
        cache = TranslationCache(cache_dir=temp_dir)
        
        cache.set("test_key", "translated_text")
        result = cache.get("test_key")
        assert result == "translated_text"
    
    def test_cache_persistence(self, temp_dir):
        """Test cache persistence across instances"""
        cache1 = TranslationCache(cache_dir=temp_dir)
        cache1.set("persist_key", "persisted_value")
        
        # Create new cache instance
        cache2 = TranslationCache(cache_dir=temp_dir)
        result = cache2.get("persist_key")
        assert result == "persisted_value"


class TestOpenAITranslator:
    """Test cases for OpenAITranslator"""
    
    @patch("modules.translator.AsyncOpenAI")
    def test_init(self, mock_openai_class):
        """Test OpenAITranslator initialization"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        translator = OpenAITranslator(
            api_key="test-key",
            target_language="zh",
            model="gpt-4"
        )
        
        assert translator.target_language == "zh"
        assert translator.model == "gpt-4"
        mock_openai_class.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    @patch("modules.translator.AsyncOpenAI")
    async def test_translate_single(self, mock_openai_class):
        """Test translating a single text"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="你好世界"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        translator = OpenAITranslator(
            api_key="test-key",
            target_language="zh"
        )
        
        result = await translator.translate_single("Hello world", "en")
        assert result == "你好世界"
    
    @pytest.mark.asyncio
    @patch("modules.translator.AsyncOpenAI")
    async def test_translate_batch(self, mock_openai_class):
        """Test batch translation"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response1 = Mock()
        mock_response1.choices = [Mock(message=Mock(content="你好"))]
        mock_response2 = Mock()
        mock_response2.choices = [Mock(message=Mock(content="世界"))]
        
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[mock_response1, mock_response2]
        )
        mock_openai_class.return_value = mock_client
        
        translator = OpenAITranslator(
            api_key="test-key",
            target_language="zh"
        )
        
        segments = [
            TranslationSegment(0, "Hello", 0.0, 1.0),
            TranslationSegment(1, "World", 1.0, 2.0)
        ]
        
        result = await translator.translate_batch(segments, "en")
        
        assert len(result) == 2
        assert result[0].translated_text == "你好"
        assert result[1].translated_text == "世界"
    
    @pytest.mark.asyncio
    @patch("modules.translator.AsyncOpenAI")
    async def test_translate_with_cache(self, mock_openai_class, temp_dir):
        """Test translation with caching"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="缓存测试"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        # Create cache
        cache = TranslationCache(cache_dir=temp_dir)
        
        translator = OpenAITranslator(
            api_key="test-key",
            target_language="zh",
            cache=cache
        )
        
        # First call - should hit API
        result1 = await translator.translate_single("Cache test", "en")
        assert result1 == "缓存测试"
        assert mock_client.chat.completions.create.call_count == 1
        
        # Second call - should hit cache
        result2 = await translator.translate_single("Cache test", "en")
        assert result2 == "缓存测试"
        assert mock_client.chat.completions.create.call_count == 1  # No additional API call


class TestClaudeTranslator:
    """Test cases for ClaudeTranslator"""
    
    @patch("modules.translator.AsyncAnthropic")
    def test_init(self, mock_anthropic_class):
        """Test ClaudeTranslator initialization"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        translator = ClaudeTranslator(
            api_key="test-key",
            target_language="zh",
            model="claude-3-opus-20240229"
        )
        
        assert translator.target_language == "zh"
        assert translator.model == "claude-3-opus-20240229"
        mock_anthropic_class.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    @patch("modules.translator.AsyncAnthropic")
    async def test_translate_single(self, mock_anthropic_class):
        """Test translating with Claude"""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="你好世界")]
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_client
        
        translator = ClaudeTranslator(
            api_key="test-key",
            target_language="zh"
        )
        
        result = await translator.translate_single("Hello world", "en")
        assert result == "你好世界"


class TestTranslatorFactory:
    """Test cases for TranslatorFactory"""
    
    def test_create_openai_translator(self):
        """Test creating OpenAI translator"""
        translator = TranslatorFactory.create_translator(
            service="openai",
            api_key="test-key",
            target_language="zh"
        )
        
        assert isinstance(translator, OpenAITranslator)
        assert translator.target_language == "zh"
    
    def test_create_claude_translator(self):
        """Test creating Claude translator"""
        translator = TranslatorFactory.create_translator(
            service="claude",
            api_key="test-key",
            target_language="zh"
        )
        
        assert isinstance(translator, ClaudeTranslator)
        assert translator.target_language == "zh"
    
    def test_create_invalid_translator(self):
        """Test creating translator with invalid service"""
        with pytest.raises(ValueError, match="Unsupported translation service"):
            TranslatorFactory.create_translator(
                service="invalid",
                api_key="test-key",
                target_language="zh"
            )
    
    def test_create_translator_with_cache(self, temp_dir):
        """Test creating translator with cache"""
        cache = TranslationCache(cache_dir=temp_dir)
        
        translator = TranslatorFactory.create_translator(
            service="openai",
            api_key="test-key",
            target_language="zh",
            cache=cache
        )
        
        assert translator.cache == cache