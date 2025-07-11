"""
自定义异常类

提供统一的异常处理机制，提升用户体验。
"""


class VideoCaptionError(Exception):
    """视频字幕生成器基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        """
        初始化异常
        
        Args:
            message: 错误信息
            error_code: 错误代码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AudioExtractionError(VideoCaptionError):
    """音频提取相关异常"""
    
    def __init__(self, message: str, video_path: str = None, **kwargs):
        super().__init__(message, error_code="AUDIO_EXTRACT", **kwargs)
        if video_path:
            self.details['video_path'] = video_path


class TranscriptionError(VideoCaptionError):
    """语音识别相关异常"""
    
    def __init__(self, message: str, audio_path: str = None, **kwargs):
        super().__init__(message, error_code="TRANSCRIPTION", **kwargs)
        if audio_path:
            self.details['audio_path'] = audio_path


class TranslationError(VideoCaptionError):
    """翻译相关异常"""
    
    def __init__(self, message: str, source_lang: str = None, target_lang: str = None, **kwargs):
        super().__init__(message, error_code="TRANSLATION", **kwargs)
        if source_lang:
            self.details['source_lang'] = source_lang
        if target_lang:
            self.details['target_lang'] = target_lang


class ConfigurationError(VideoCaptionError):
    """配置相关异常"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIG", **kwargs)
        if config_key:
            self.details['config_key'] = config_key


class FileProcessingError(VideoCaptionError):
    """文件处理相关异常"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message, error_code="FILE_PROCESS", **kwargs)
        if file_path:
            self.details['file_path'] = file_path


class APIError(VideoCaptionError):
    """API调用相关异常"""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, **kwargs):
        super().__init__(message, error_code="API_ERROR", **kwargs)
        if api_name:
            self.details['api_name'] = api_name
        if status_code:
            self.details['status_code'] = status_code


class ValidationError(VideoCaptionError):
    """数据验证相关异常"""
    
    def __init__(self, message: str, field: str = None, value: any = None, **kwargs):
        super().__init__(message, error_code="VALIDATION", **kwargs)
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = value