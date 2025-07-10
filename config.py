"""
Configuration management for Video Caption Generator
"""
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class APIConfig(BaseModel):
    """API configuration settings"""
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    api_timeout: int = Field(30, ge=10, le=300, description="API timeout in seconds")
    api_max_retries: int = Field(3, ge=1, le=10, description="Maximum API retry attempts")
    api_retry_delay: float = Field(1.0, ge=0.1, le=10.0, description="Delay between retries")


class WhisperConfig(BaseModel):
    """Whisper model configuration"""
    model: Literal["tiny", "base", "small", "medium", "large"] = Field(
        "base", 
        description="Whisper model size"
    )
    device: Literal["cpu", "cuda"] = Field("cpu", description="Device for inference")
    language: Optional[str] = Field(None, description="Source language (auto-detect if None)")
    
    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device availability"""
        if v == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    print("Warning: CUDA requested but not available, falling back to CPU")
                    return "cpu"
            except ImportError:
                print("Warning: PyTorch not installed with CUDA support, using CPU")
                return "cpu"
        return v


class TranslationConfig(BaseModel):
    """Translation configuration"""
    default_translator: Literal["openai", "claude"] = Field(
        "openai", 
        description="Default translation service"
    )
    target_language: str = Field("zh", description="Target language code")
    max_segment_length: int = Field(
        5000, 
        ge=100, 
        le=10000, 
        description="Maximum segment length for translation"
    )
    batch_size: int = Field(10, ge=1, le=50, description="Batch size for translation")
    max_concurrent_requests: int = Field(
        5, 
        ge=1, 
        le=20, 
        description="Maximum concurrent API requests"
    )


class OutputConfig(BaseModel):
    """Output configuration"""
    output_format: Literal["srt", "txt", "json"] = Field("srt", description="Output format")
    output_dir: Path = Field(Path("./output"), description="Output directory")
    temp_dir: Path = Field(Path("./temp"), description="Temporary files directory")
    keep_temp_files: bool = Field(False, description="Keep temporary files after processing")
    
    @field_validator("output_dir", "temp_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist"""
        v.mkdir(parents=True, exist_ok=True)
        return v


class LogConfig(BaseModel):
    """Logging configuration"""
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", 
        description="Logging level"
    )
    log_file: Optional[Path] = Field(Path("./logs/app.log"), description="Log file path")
    log_format: Literal["simple", "detailed"] = Field(
        "detailed", 
        description="Log format style"
    )
    
    @field_validator("log_file")
    @classmethod
    def create_log_dir(cls, v: Optional[Path]) -> Optional[Path]:
        """Ensure log directory exists"""
        if v:
            v.parent.mkdir(parents=True, exist_ok=True)
        return v


class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Sub-configurations
    api: APIConfig = Field(default_factory=APIConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LogConfig = Field(default_factory=LogConfig)
    
    # Global settings
    show_progress: bool = Field(True, description="Show progress bars")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    def __init__(self, **kwargs):
        """Initialize settings with environment variables"""
        super().__init__(**kwargs)
        
        # Override with environment variables
        import os
        
        # API settings
        if api_key := os.getenv("OPENAI_API_KEY"):
            self.api.openai_api_key = api_key
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.api.anthropic_api_key = api_key
            
        # Default settings from env
        if translator := os.getenv("DEFAULT_TRANSLATOR"):
            if translator in ["openai", "claude"]:
                self.translation.default_translator = translator
        if lang := os.getenv("DEFAULT_TARGET_LANG"):
            self.translation.target_language = lang
        if model := os.getenv("DEFAULT_WHISPER_MODEL"):
            if model in ["tiny", "base", "small", "medium", "large"]:
                self.whisper.model = model
        if fmt := os.getenv("DEFAULT_OUTPUT_FORMAT"):
            if fmt in ["srt", "txt", "json"]:
                self.output.output_format = fmt
                
        # Advanced settings
        if device := os.getenv("WHISPER_DEVICE"):
            if device in ["cpu", "cuda"]:
                self.whisper.device = device
        if timeout := os.getenv("API_TIMEOUT"):
            try:
                self.api.api_timeout = int(timeout)
            except ValueError:
                pass
                
    def validate_translator(self) -> None:
        """Validate selected translator has required API key"""
        if self.translation.default_translator == "openai" and not self.api.openai_api_key:
            raise ValueError("OpenAI API key required for OpenAI translator")
        if self.translation.default_translator == "claude" and not self.api.anthropic_api_key:
            raise ValueError("Anthropic API key required for Claude translator")
    
    def get_active_api_key(self) -> str:
        """Get the API key for the active translator"""
        if self.translation.default_translator == "openai":
            return self.api.openai_api_key or ""
        else:
            return self.api.anthropic_api_key or ""


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def update_settings(**kwargs) -> Settings:
    """Update settings dynamically"""
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings