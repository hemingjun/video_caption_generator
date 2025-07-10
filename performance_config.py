"""
Performance optimization configurations
"""
from typing import Optional
import multiprocessing


class PerformanceConfig:
    """Performance optimization settings"""
    
    # CPU settings
    MAX_WORKERS = min(multiprocessing.cpu_count(), 8)
    
    # Memory settings
    MAX_SEGMENT_BATCH_SIZE = 50  # Max segments to translate in one batch
    MAX_TEXT_LENGTH_PER_REQUEST = 2000  # Max characters per translation request
    
    # Audio processing
    AUDIO_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for large files
    MAX_AUDIO_DURATION = 3600  # Max 1 hour audio in one go
    
    # Whisper optimization
    WHISPER_BEAM_SIZE = 5  # Beam size for whisper
    WHISPER_BEST_OF = 5  # Best of N for whisper
    WHISPER_TEMPERATURE = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]  # Temperature sampling
    
    # Translation optimization
    TRANSLATION_TIMEOUT = 30  # Timeout per translation request in seconds
    TRANSLATION_MAX_RETRIES = 3  # Max retries for failed translations
    TRANSLATION_RETRY_DELAY = 1  # Delay between retries in seconds
    
    # Cache settings
    CACHE_MAX_SIZE = 1000  # Max number of cached translations
    CACHE_TTL = 86400 * 7  # Cache TTL in seconds (7 days)
    
    @classmethod
    def get_optimal_batch_size(cls, total_segments: int) -> int:
        """Get optimal batch size based on total segments"""
        if total_segments <= 10:
            return total_segments
        elif total_segments <= 50:
            return 10
        elif total_segments <= 200:
            return 20
        else:
            return cls.MAX_SEGMENT_BATCH_SIZE
    
    @classmethod
    def get_whisper_compute_type(cls, model_size: str, has_gpu: bool) -> str:
        """Get optimal compute type for Whisper based on model and hardware"""
        if has_gpu:
            # GPU optimizations
            if model_size in ["tiny", "base", "small"]:
                return "float16"
            else:
                return "float32"
        else:
            # CPU optimizations
            if model_size in ["tiny", "base"]:
                return "int8"
            else:
                return "float32"
    
    @classmethod
    def should_use_vad(cls, audio_duration: float) -> bool:
        """Determine if Voice Activity Detection should be used"""
        # Use VAD for longer audio files to skip silence
        return audio_duration > 300  # 5 minutes