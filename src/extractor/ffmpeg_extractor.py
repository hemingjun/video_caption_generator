"""音频提取模块 - 使用 FFmpeg 从视频中提取音频"""
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import ffmpeg
from src.utils.helpers import setup_logger, ensure_dir, get_output_path
from src.config.settings import get_settings


logger = setup_logger(__name__)


class AudioExtractor:
    """音频提取器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = ensure_dir(self.settings.processing.temp_dir)
    
    def check_ffmpeg(self) -> bool:
        """检查 FFmpeg 是否已安装"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg 未安装或不在 PATH 中")
            return False
    
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            probe = ffmpeg.probe(str(video_path))
            video_info = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'), 
                None
            )
            audio_info = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'), 
                None
            )
            
            return {
                'duration': float(probe['format']['duration']),
                'size': int(probe['format']['size']),
                'video_codec': video_info['codec_name'] if video_info else None,
                'audio_codec': audio_info['codec_name'] if audio_info else None,
                'has_audio': audio_info is not None
            }
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {}
    
    def extract_audio(
        self, 
        video_path: Path, 
        output_path: Optional[Path] = None,
        sample_rate: int = 16000
    ) -> Path:
        """从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径，默认为临时目录
            sample_rate: 采样率，Whisper 需要 16kHz
            
        Returns:
            提取的音频文件路径
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg 未安装")
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取视频信息
        info = self.get_video_info(video_path)
        if not info.get('has_audio', False):
            raise ValueError(f"视频文件没有音频流: {video_path}")
        
        # 设置输出路径
        if output_path is None:
            output_path = self.temp_dir / f"{video_path.stem}.wav"
        else:
            ensure_dir(output_path.parent)
        
        logger.info(f"开始提取音频: {video_path}")
        logger.info(f"视频时长: {info.get('duration', 0):.1f}秒")
        
        try:
            # 使用 ffmpeg-python 构建命令
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream, 
                str(output_path),
                acodec='pcm_s16le',  # WAV 格式
                ar=sample_rate,      # 采样率
                ac=1,                # 单声道
                loglevel='error'
            )
            ffmpeg.run(stream, overwrite_output=True)
            
            logger.info(f"音频提取成功: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"音频提取失败: {e.stderr.decode()}")
            raise RuntimeError(f"音频提取失败: {e}")
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        if not self.settings.processing.keep_temp_files:
            for file in self.temp_dir.glob("*.wav"):
                try:
                    file.unlink()
                    logger.debug(f"删除临时文件: {file}")
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {file}, {e}")