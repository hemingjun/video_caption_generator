"""视频字幕生成器 CLI 入口"""
import click
from pathlib import Path
import sys
from typing import List, Optional
from tqdm import tqdm
from src.extractor.ffmpeg_extractor import AudioExtractor
from src.transcriber.whisper_transcriber import WhisperTranscriber
from src.translator.openai_translator import OpenAITranslator
from src.formatter.srt_formatter import SRTFormatter
from src.formatter.text_formatter import TextFormatter
from src.utils.helpers import setup_logger, is_video_file, process_path_arguments, get_video_files, setup_default_logger
from src.config.settings import get_settings
from src.utils.cost_calculator import CostCalculator
from src.utils.checkpoint import CheckpointManager, CheckpointStage
from src.utils.exceptions import VideoCaptionError


# 初始化配置
settings = get_settings()

# 设置日志
log_file = settings.logging.file if settings.logging.file else None
logger = setup_logger(
    "cli",
    level=settings.logging.level,
    log_file=log_file
)

# 设置全局日志
setup_default_logger(settings.model_dump())


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
@click.option('--recursive', '-r', is_flag=True, help='递归处理子目录')
@click.option('--resume', is_flag=True, help='从断点继续处理')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='自定义配置文件路径')
@click.option('--no-paragraph-mode', is_flag=True, 
              help='禁用段落模式，使用传统逐句翻译模式')
@click.option('--paragraph-silence', type=float,
              help='段落分隔的静音时长（秒）')
@click.option('--paragraph-max-duration', type=float,
              help='单个段落最大时长（秒）')
@click.option('--no-redistribute-timestamps', is_flag=True,
              help='禁用时间戳重分配')
def process(video_path: tuple, lang: str, format: str, output_dir: Path, 
           recursive: bool, resume: bool, config: Path,
           no_paragraph_mode: bool, paragraph_silence: float,
           paragraph_max_duration: float, no_redistribute_timestamps: bool):
    """处理视频生成字幕（完整流程）
    
    示例：
        # 处理单个文件
        python cli.py process video.mp4
        python cli.py process "video with spaces.mp4"
        
        # 处理目录中的所有视频
        python cli.py process ./videos/
        python cli.py process ./videos/ --recursive
        
        # 使用自定义配置
        python cli.py process video.mp4 --config my_config.yaml
        
        # 从断点继续
        python cli.py process video.mp4 --resume
    """
    # 如果指定了配置文件，重新加载配置
    if config:
        global settings
        settings = get_settings(config_file=config)
        logger.info(f"使用配置文件: {config}")
    
    # 应用命令行参数覆盖配置
    if no_paragraph_mode:
        settings.translation.paragraph_mode = False
        logger.info("使用传统逐句翻译模式")
    
    if paragraph_silence is not None:
        settings.translation.paragraph_silence_threshold = paragraph_silence
        logger.info(f"段落静音阈值设置为: {paragraph_silence}秒")
    
    if paragraph_max_duration is not None:
        settings.translation.paragraph_max_duration = paragraph_max_duration
        logger.info(f"段落最大时长设置为: {paragraph_max_duration}秒")
    
    if no_redistribute_timestamps:
        settings.translation.redistribute_timestamps = False
        logger.info("禁用时间戳重分配")
    
    # 处理路径参数
    try:
        input_path = process_path_arguments(video_path)
    except click.BadParameter as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 判断是文件还是目录
    video_files: List[Path] = []
    
    if input_path.is_file():
        # 单个文件
        if not is_video_file(input_path):
            logger.error(f"不支持的视频格式: {input_path.suffix}")
            sys.exit(1)
        video_files = [input_path]
    elif input_path.is_dir():
        # 目录处理
        if recursive:
            # 递归查找所有视频文件
            video_files = list(input_path.rglob("*"))
            video_files = [f for f in video_files if f.is_file() and is_video_file(f)]
        else:
            # 只处理当前目录
            video_files = get_video_files(input_path)
        
        if not video_files:
            logger.error(f"目录中没有找到视频文件: {input_path}")
            sys.exit(1)
        
        click.echo(f"📁 找到 {len(video_files)} 个视频文件")
    else:
        logger.error(f"路径不存在: {input_path}")
        sys.exit(1)
    
    # 更新配置中的目标语言
    settings.translation.target_language = lang
    
    # 初始化断点管理器
    checkpoint_manager = CheckpointManager() if resume else None
    
    # 总费用累计
    total_whisper_cost = 0.0
    total_gpt_cost = 0.0
    total_duration = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    
    # 处理每个视频文件
    with tqdm(total=len(video_files), desc="处理视频", unit="个") as pbar:
        for video_file in video_files:
            try:
                # 显示当前文件
                pbar.set_description(f"处理: {video_file.name}")
                
                # 处理单个视频
                result = process_single_video(
                    video_file, lang, format, output_dir, 
                    settings, checkpoint_manager
                )
                
                # 累计费用
                if result:
                    total_whisper_cost += result['whisper_cost']
                    total_gpt_cost += result['gpt_cost']
                    total_duration += result['duration']
                    total_input_tokens += result['input_tokens']
                    total_output_tokens += result['output_tokens']
                
                # 更新进度
                pbar.update(1)
                
            except Exception as e:
                logger.error(f"处理 {video_file.name} 失败: {e}")
                if len(video_files) == 1:
                    sys.exit(1)
                # 批量处理时继续处理下一个
                pbar.update(1)
                continue
    
    # 显示总费用汇总
    if len(video_files) > 1:
        click.echo("\n" + "="*50)
        click.echo("📊 批量处理完成")
        click.echo(f"  处理文件数: {len(video_files)}")
        
        cost_calculator = CostCalculator(settings.api_pricing.model_dump())
        click.echo(cost_calculator.format_cost_summary(
            whisper_cost=total_whisper_cost,
            gpt_cost=total_gpt_cost,
            duration_seconds=total_duration,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens
        ))


def process_single_video(
    video_file: Path,
    lang: str,
    format: str,
    output_dir: Optional[Path],
    settings: any,
    checkpoint_manager: Optional[CheckpointManager]
) -> Optional[dict]:
    """处理单个视频文件
    
    Returns:
        处理结果字典，包含费用信息
    """
    # 确定输出目录
    if output_dir is None:
        output_dir = video_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    base_name = video_file.stem
    srt_path = output_dir / f"{base_name}_{lang}.srt"
    txt_path = output_dir / f"{base_name}_{lang}.txt"
    
    # 检查断点
    checkpoint_data = None
    if checkpoint_manager:
        checkpoint_data = checkpoint_manager.load_checkpoint(video_file)
        if checkpoint_data:
            logger.info(f"从断点继续: {checkpoint_data['stage']}")
    
    try:
        # 初始化组件
        extractor = AudioExtractor()
        transcriber = WhisperTranscriber()
        translator = OpenAITranslator()
        
        # 1. 提取音频
        audio_path = None
        if not checkpoint_data or checkpoint_data['stage'] == CheckpointStage.AUDIO_EXTRACTION:
            logger.info(f"提取音频: {video_file.name}")
            audio_path = extractor.extract_audio(video_file)
            
            if checkpoint_manager:
                checkpoint_manager.save_checkpoint(
                    video_file,
                    {"audio_path": str(audio_path)},
                    CheckpointStage.TRANSCRIPTION,
                    progress=25.0
                )
        else:
            # 从断点恢复音频路径
            audio_path = Path(checkpoint_data['state'].get('audio_path'))
        
        # 2. 语音识别
        transcription = None
        if not checkpoint_data or checkpoint_data['stage'] in [CheckpointStage.TRANSCRIPTION, CheckpointStage.AUDIO_EXTRACTION]:
            logger.info(f"语音识别: {video_file.name}")
            # 检查文件大小，决定是否使用分段处理
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 20:
                logger.info(f"音频文件较大 ({file_size_mb:.1f}MB)，使用分段处理")
                transcription = transcriber.transcribe_with_chunks(audio_path, chunk_duration=settings.processing.chunk_duration)
            else:
                transcription = transcriber.transcribe(audio_path)
            
            if checkpoint_manager:
                checkpoint_manager.save_checkpoint(
                    video_file,
                    {
                        "audio_path": str(audio_path),
                        "transcription": {
                            "language": transcription.language,
                            "duration": transcription.duration,
                            "segments": [s.model_dump() for s in transcription.segments]
                        }
                    },
                    CheckpointStage.TRANSLATION,
                    progress=50.0
                )
        else:
            # 从断点恢复转录结果
            from src.transcriber.whisper_transcriber import TranscriptionResult, TranscriptionSegment
            trans_data = checkpoint_data['state']['transcription']
            segments = [TranscriptionSegment(**s) for s in trans_data['segments']]
            transcription = TranscriptionResult(
                segments=segments,
                language=trans_data['language'],
                duration=trans_data['duration']
            )
        
        # 3. 翻译
        translation = None
        if not checkpoint_data or checkpoint_data['stage'] in [CheckpointStage.TRANSLATION, CheckpointStage.TRANSCRIPTION, CheckpointStage.AUDIO_EXTRACTION]:
            logger.info(f"翻译到{lang}: {video_file.name}")
            translation = translator.translate(
                transcription.segments,
                transcription.language
            )
            
            if checkpoint_manager:
                checkpoint_manager.save_checkpoint(
                    video_file,
                    {
                        "audio_path": str(audio_path),
                        "translation_complete": True,
                        "input_tokens": translation.input_tokens,
                        "output_tokens": translation.output_tokens
                    },
                    CheckpointStage.FORMATTING,
                    progress=75.0
                )
        else:
            # 从断点恢复翻译结果
            from src.translator.openai_translator import TranslationResult
            translation = TranslationResult(
                segments=translation.segments,  # 需要保存和恢复
                input_tokens=checkpoint_data['state'].get('input_tokens'),
                output_tokens=checkpoint_data['state'].get('output_tokens')
            )
        
        # 4. 生成输出文件
        logger.info(f"生成字幕文件: {video_file.name}")
        
        if format in ['srt', 'both']:
            srt_formatter = SRTFormatter()
            srt_formatter.save(
                translation.segments,
                srt_path,
                include_original=settings.output.include_original
            )
        
        if format in ['text', 'both']:
            text_formatter = TextFormatter()
            text_formatter.save(
                translation.segments,
                txt_path,
                include_original=settings.output.include_original
            )
        
        # 清理临时文件
        if not settings.processing.keep_temp_files and audio_path and audio_path.exists():
            audio_path.unlink()
        
        # 删除断点
        if checkpoint_manager:
            checkpoint_manager.remove_checkpoint(video_file)
        
        logger.info(f"完成: {video_file.name}")
        
        # 计算费用
        cost_calculator = CostCalculator(settings.api_pricing.model_dump())
        whisper_cost = cost_calculator.calculate_whisper_cost(transcription.duration)
        gpt_cost = 0.0
        if translation.input_tokens and translation.output_tokens:
            gpt_cost = cost_calculator.calculate_gpt_cost(
                translation.input_tokens,
                translation.output_tokens
            )
        
        return {
            'whisper_cost': whisper_cost,
            'gpt_cost': gpt_cost,
            'duration': transcription.duration,
            'input_tokens': translation.input_tokens or 0,
            'output_tokens': translation.output_tokens or 0
        }
        
    except Exception as e:
        logger.error(f"处理 {video_file.name} 失败: {e}")
        raise


@cli.command()
def info():
    """显示配置信息"""
    settings = get_settings()
    click.echo("📋 当前配置:")
    click.echo(f"  - Whisper 模型: {settings.whisper.model_size}")
    click.echo(f"  - 目标语言: {settings.translation.target_language}")
    click.echo(f"  - 输出格式: {settings.output.format}")
    click.echo(f"  - 临时目录: {settings.processing.temp_dir}")
    
    # 段落模式配置
    click.echo("\n📝 段落模式配置:")
    click.echo(f"  - 段落模式: {'启用' if settings.translation.paragraph_mode else '禁用'}")
    if settings.translation.paragraph_mode:
        click.echo(f"  - 段落静音阈值: {settings.translation.paragraph_silence_threshold}秒")
        click.echo(f"  - 段落最大时长: {settings.translation.paragraph_max_duration}秒")
        click.echo(f"  - 段落最小时长: {settings.translation.paragraph_min_duration}秒")
        click.echo(f"  - 时间戳重分配: {'启用' if settings.translation.redistribute_timestamps else '禁用'}")
    
    # 检查 FFmpeg
    extractor = AudioExtractor()
    if extractor.check_ffmpeg():
        click.echo("\n✅ FFmpeg 已安装")
    else:
        click.echo("\n❌ FFmpeg 未安装，请先安装 FFmpeg")


if __name__ == '__main__':
    cli()