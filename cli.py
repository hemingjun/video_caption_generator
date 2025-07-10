"""视频字幕生成器 CLI 入口"""
import click
from pathlib import Path
import sys
from src.extractor.ffmpeg_extractor import AudioExtractor
from src.transcriber.whisper_transcriber import WhisperTranscriber
from src.translator.openai_translator import OpenAITranslator
from src.formatter.srt_formatter import SRTFormatter
from src.formatter.text_formatter import TextFormatter
from src.utils.helpers import setup_logger, is_video_file, process_path_arguments
from src.config.settings import get_settings
from src.utils.cost_calculator import CostCalculator


logger = setup_logger("cli")

# 设置其他模块的日志级别
import logging
logging.getLogger("src.translator.openai_translator").setLevel(logging.DEBUG)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """视频字幕生成器 - 自动提取、识别、翻译视频字幕"""
    pass


@cli.command()
@click.argument('video_path', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='输出音频文件路径')
@click.option('--sample-rate', '-r', default=16000, 
              help='输出音频采样率 (默认: 16000 Hz)')
def extract(video_path: tuple, output: Path, sample_rate: int):
    """从视频中提取音频
    
    示例：
        python cli.py extract video.mp4
        python cli.py extract "video with spaces.mp4"
        python cli.py extract video with spaces.mp4
    """
    # 处理路径参数
    try:
        video_file = process_path_arguments(video_path)
    except click.BadParameter as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 验证输入
    if not is_video_file(video_file):
        logger.error(f"不支持的视频格式: {video_file.suffix}")
        sys.exit(1)
    
    try:
        # 创建提取器
        extractor = AudioExtractor()
        
        # 提取音频
        audio_path = extractor.extract_audio(
            video_file, 
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
@click.argument('video_path', nargs=-1, required=True)
@click.option('--lang', '-l', default='zh-cn', help='目标语言 (默认: zh-cn)')
@click.option('--format', '-f', type=click.Choice(['srt', 'text', 'both']), 
              default='both', help='输出格式')
@click.option('--output-dir', '-o', type=click.Path(path_type=Path),
              help='输出目录 (默认: 与视频同目录)')
def process(video_path: tuple, lang: str, format: str, output_dir: Path):
    """处理视频生成字幕（完整流程）
    
    示例：
        python cli.py process video.mp4
        python cli.py process "video with spaces.mp4"
        python cli.py process video with spaces.mp4
        python cli.py process San Diego.mp4 --lang zh-cn
    """
    # 处理路径参数
    try:
        video_file = process_path_arguments(video_path)
    except click.BadParameter as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 验证输入
    if not is_video_file(video_file):
        logger.error(f"不支持的视频格式: {video_file.suffix}")
        sys.exit(1)
    
    # 更新配置中的目标语言
    settings = get_settings()
    settings.translation.target_language = lang
    
    # 确定输出目录
    if output_dir is None:
        output_dir = video_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    base_name = video_file.stem
    srt_path = output_dir / f"{base_name}_{lang}.srt"
    txt_path = output_dir / f"{base_name}_{lang}.txt"
    
    try:
        # 1. 提取音频
        click.echo("🎵 正在提取音频...")
        extractor = AudioExtractor()
        audio_path = extractor.extract_audio(video_file)
        audio_size_mb = audio_path.stat().st_size / (1024 * 1024)
        click.echo(f"✅ 音频提取完成 ({audio_size_mb:.1f} MB)")
        
        # 2. 语音识别
        click.echo("🎤 正在进行语音识别...")
        transcriber = WhisperTranscriber()
        transcription = transcriber.transcribe(audio_path)
        click.echo(f"✅ 语音识别完成 (语言: {transcription.language}, "
                  f"时长: {transcription.duration:.1f}秒, "
                  f"片段数: {len(transcription.segments)})")
        
        # 3. 翻译
        click.echo(f"🌐 正在翻译到 {lang}...")
        translator = OpenAITranslator()
        
        # 使用进度条显示翻译进度
        translation = translator.translate(
            transcription.segments,
            transcription.language
        )
        
        click.echo(f"✅ 翻译完成")
        
        # 4. 生成输出文件
        click.echo("💾 正在生成字幕文件...")
        
        if format in ['srt', 'both']:
            srt_formatter = SRTFormatter()
            srt_formatter.save(
                translation.segments,
                srt_path,
                include_original=settings.output.include_original
            )
            click.echo(f"✅ SRT 文件已保存: {srt_path}")
        
        if format in ['text', 'both']:
            text_formatter = TextFormatter()
            text_formatter.save(
                translation.segments,
                txt_path,
                include_original=settings.output.include_original
            )
            click.echo(f"✅ 文本文件已保存: {txt_path}")
        
        # 清理临时文件
        if not settings.processing.keep_temp_files:
            audio_path.unlink()
            click.echo("🧹 临时文件已清理")
        
        click.echo("🎉 处理完成！")
        
        # 计算并显示API费用
        cost_calculator = CostCalculator(settings.api_pricing.model_dump())
        
        # 计算费用
        whisper_cost = cost_calculator.calculate_whisper_cost(transcription.duration)
        gpt_cost = 0.0
        if translation.input_tokens and translation.output_tokens:
            gpt_cost = cost_calculator.calculate_gpt_cost(
                translation.input_tokens,
                translation.output_tokens
            )
        
        # 显示费用汇总
        click.echo()
        click.echo(cost_calculator.format_cost_summary(
            whisper_cost=whisper_cost,
            gpt_cost=gpt_cost,
            duration_seconds=transcription.duration,
            input_tokens=translation.input_tokens or 0,
            output_tokens=translation.output_tokens or 0
        ))
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)


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