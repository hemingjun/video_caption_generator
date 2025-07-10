"""视频字幕生成器 CLI 入口"""
import click
from pathlib import Path
import sys
from src.extractor.ffmpeg_extractor import AudioExtractor
from src.utils.helpers import setup_logger, is_video_file
from src.config.settings import get_settings


logger = setup_logger("cli")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """视频字幕生成器 - 自动提取、识别、翻译视频字幕"""
    pass


@cli.command()
@click.argument('video_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='输出音频文件路径')
@click.option('--sample-rate', '-r', default=16000, 
              help='输出音频采样率 (默认: 16000 Hz)')
def extract(video_path: Path, output: Path, sample_rate: int):
    """从视频中提取音频
    
    示例：
        python cli.py extract video.mp4
        python cli.py extract video.mp4 --output audio.wav
    """
    # 验证输入
    if not is_video_file(video_path):
        logger.error(f"不支持的视频格式: {video_path.suffix}")
        sys.exit(1)
    
    try:
        # 创建提取器
        extractor = AudioExtractor()
        
        # 提取音频
        audio_path = extractor.extract_audio(
            video_path, 
            output_path=output,
            sample_rate=sample_rate
        )
        
        click.echo(f"✅ 音频提取成功: {audio_path}")
        
        # 显示音频信息
        audio_size = audio_path.stat().st_size / (1024 * 1024)  # MB
        click.echo(f"📊 文件大小: {audio_size:.1f} MB")
        click.echo(f"🎵 采样率: {sample_rate} Hz")
        
    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        sys.exit(1)


@cli.command()
@click.argument('video_path', type=click.Path(exists=True, path_type=Path))
@click.option('--lang', '-l', default='zh', help='目标语言 (默认: zh)')
@click.option('--format', '-f', type=click.Choice(['srt', 'text', 'both']), 
              default='both', help='输出格式')
def process(video_path: Path, lang: str, format: str):
    """处理视频生成字幕（完整流程）
    
    示例：
        python cli.py process video.mp4
        python cli.py process video.mp4 --lang zh --format srt
    """
    click.echo("🚧 此功能将在第2阶段实现")
    click.echo("📌 当前仅支持音频提取功能，请使用 extract 命令")


@cli.command()
def info():
    """显示配置信息"""
    settings = get_settings()
    click.echo("📋 当前配置:")
    click.echo(f"  - Whisper 模型: {settings.whisper.model_size}")
    click.echo(f"  - 目标语言: {settings.translation.target_language}")
    click.echo(f"  - 输出格式: {settings.output.format}")
    click.echo(f"  - 临时目录: {settings.processing.temp_dir}")
    
    # 检查 FFmpeg
    extractor = AudioExtractor()
    if extractor.check_ffmpeg():
        click.echo("✅ FFmpeg 已安装")
    else:
        click.echo("❌ FFmpeg 未安装，请先安装 FFmpeg")


if __name__ == '__main__':
    cli()