"""配置管理模块"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseModel):
    """OpenAI API 配置"""
    api_key: str = Field(default="", description="API密钥")
    model: str = Field(default="gpt-3.5-turbo", description="使用的模型")
    max_retries: int = Field(default=3, description="重试次数")
    timeout: int = Field(default=30, description="超时时间")

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v):
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.getenv(env_var, "")
        return v


class WhisperConfig(BaseModel):
    """Whisper 配置"""
    model_size: str = Field(default="base", description="模型大小")
    device: str = Field(default="cpu", description="运行设备")
    compute_type: str = Field(default="int8", description="计算类型")
    language: str = Field(default="auto", description="源语言")


class TranslationConfig(BaseModel):
    """翻译配置"""
    target_language: str = Field(default="zh-cn", description="目标语言")
    batch_size: int = Field(default=10, description="批量大小")
    preserve_style: bool = Field(default=True, description="保持风格")
    target_speech_rate: int = Field(default=240, description="目标语速（字/分钟）")
    gap_duration: float = Field(default=0.5, description="句子间隔时间（秒）")
    
    # 段落模式配置
    paragraph_mode: bool = Field(default=True, description="是否启用段落模式")
    paragraph_silence_threshold: float = Field(default=1.5, description="段落分隔的静音时长（秒）")
    paragraph_max_duration: float = Field(default=30.0, description="单个段落最大时长（秒）")
    paragraph_min_duration: float = Field(default=3.0, description="单个段落最小时长（秒）")
    
    # 时间戳重分配配置
    redistribute_timestamps: bool = Field(default=True, description="是否重新分配时间戳")
    sentence_min_gap: float = Field(default=0.5, description="句子之间的最小间隔（秒）")
    punctuation_pause_weights: Dict[str, float] = Field(
        default={
            "。": 1.0, "！": 1.0, "？": 1.0,  # 句号类
            "，": 0.5, "；": 0.7,  # 逗号类  
            "…": 0.8,  # 省略号
            ".": 1.0, "!": 1.0, "?": 1.0,  # 英文句号类
            ",": 0.5, ";": 0.7  # 英文逗号类
        },
        description="不同标点的停顿权重"
    )


class OutputConfig(BaseModel):
    """输出配置"""
    format: str = Field(default="both", description="输出格式")
    srt_max_line_length: int = Field(default=42, description="SRT行长度")
    include_original: bool = Field(default=True, description="包含原文")


class ProcessingConfig(BaseModel):
    """处理配置"""
    chunk_duration: int = Field(default=300, description="分段时长")
    temp_dir: str = Field(default="./temp", description="临时目录")
    keep_temp_files: bool = Field(default=False, description="保留临时文件")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="./logs/video_caption.log", description="日志文件")


class WhisperPricing(BaseModel):
    """Whisper API价格配置"""
    price_per_minute: float = Field(default=0.006, description="每分钟价格")
    currency: str = Field(default="USD", description="货币单位")


class GPTPricing(BaseModel):
    """GPT API价格配置"""
    input_per_million_tokens: float = Field(default=5.0, description="输入每百万token价格")
    output_per_million_tokens: float = Field(default=20.0, description="输出每百万token价格")
    currency: str = Field(default="USD", description="货币单位")


class APIPricingConfig(BaseModel):
    """API价格配置"""
    whisper: WhisperPricing = Field(default_factory=WhisperPricing)
    gpt4o: GPTPricing = Field(default_factory=GPTPricing)
    pricing_url: str = Field(default="https://openai.com/api/pricing/", description="价格页面URL")
    last_updated: str = Field(default="2025-01-10", description="最后更新日期")


class Settings(BaseModel):
    """应用配置"""
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    api_pricing: APIPricingConfig = Field(default_factory=APIPricingConfig)

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Settings":
        """从文件加载配置"""
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                return cls(**config_data)
        return cls()

    def save_to_file(self, config_path: Path) -> None:
        """保存配置到文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[Path] = None) -> Settings:
    """获取全局配置实例
    
    Args:
        config_file: 自定义配置文件路径
    """
    global _settings
    if _settings is None or config_file is not None:
        config_path = config_file if config_file else Path("config.yaml")
        _settings = Settings.load_from_file(config_path)
    return _settings


def reload_settings(config_path: Optional[Path] = None) -> Settings:
    """重新加载配置"""
    global _settings
    if config_path is None:
        config_path = Path("config.yaml")
    _settings = Settings.load_from_file(config_path)
    return _settings