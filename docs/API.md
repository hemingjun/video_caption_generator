# Video Caption Generator API Documentation

## Core Modules

### AudioExtractor

Extracts audio from video files using FFmpeg.

```python
from modules.audio_extractor import AudioExtractor

extractor = AudioExtractor(temp_dir=None)
```

#### Methods

##### `extract_audio(video_path, output_path=None, sample_rate=16000, channels=1, show_progress=True, start_time=None, duration=None) -> Path`

Extract audio from video and convert to WAV format.

**Parameters:**
- `video_path` (str/Path): Path to input video file
- `output_path` (str/Path, optional): Path for output audio file
- `sample_rate` (int): Audio sample rate (default: 16000 Hz for Whisper)
- `channels` (int): Number of audio channels (default: 1 for mono)
- `show_progress` (bool): Show extraction progress
- `start_time` (float, optional): Start time in seconds
- `duration` (float, optional): Duration in seconds

**Returns:**
- `Path`: Path to extracted audio file

**Raises:**
- `FileNotFoundError`: If video file doesn't exist
- `ValueError`: If video format is not supported
- `RuntimeError`: If audio extraction fails

### SpeechRecognizer

Performs speech recognition using OpenAI Whisper.

```python
from modules.speech_recognizer import SpeechRecognizer

recognizer = SpeechRecognizer(
    model_name="base",
    device="auto",
    download_root=None
)
```

#### Methods

##### `transcribe(audio_path, language=None, task="transcribe", show_progress=True, **kwargs) -> dict`

Transcribe audio file to text.

**Parameters:**
- `audio_path` (str/Path): Path to audio file
- `language` (str, optional): Language code (e.g., 'en', 'zh')
- `task` (str): Task type ('transcribe' or 'translate')
- `show_progress` (bool): Show transcription progress
- `**kwargs`: Additional Whisper parameters

**Returns:**
- `dict`: Transcription results with keys:
  - `text` (str): Full transcribed text
  - `segments` (list): List of segments with timing
  - `language` (str): Detected/specified language

### Translator

Abstract base class for translation services.

#### OpenAITranslator

```python
from modules.translator import OpenAITranslator

translator = OpenAITranslator(
    api_key="your-api-key",
    target_language="zh",
    model="gpt-4",
    max_retries=3,
    timeout=30,
    use_cache=True
)
```

#### ClaudeTranslator

```python
from modules.translator import ClaudeTranslator

translator = ClaudeTranslator(
    api_key="your-api-key",
    target_language="zh",
    model="claude-3-opus-20240229",
    max_retries=3,
    timeout=30,
    use_cache=True
)
```

#### Methods

##### `translate_single(text, source_lang=None) -> str`

Translate a single text string.

##### `translate_batch(segments, source_lang=None, progress=None, task_id=None) -> List[TranslationSegment]`

Translate multiple segments with optimized batching.

**Parameters:**
- `segments` (List[TranslationSegment]): Segments to translate
- `source_lang` (str, optional): Source language code
- `progress` (Progress, optional): Rich progress object
- `task_id` (TaskID, optional): Progress task ID

**Returns:**
- `List[TranslationSegment]`: Translated segments

### OutputHandler

Handles saving transcription results in various formats.

```python
from modules.output_handler import OutputHandler

handler = OutputHandler(output_dir="./output")
```

#### Methods

##### `save_srt(transcription_result, video_path, target_language) -> Path`

Save transcription as SRT subtitle file.

##### `save_txt(transcription_result, video_path, target_language) -> Path`

Save transcription as plain text file.

##### `save_json(transcription_result, video_path, target_language) -> Path`

Save transcription as JSON file.

##### `save_all_formats(transcription_result, video_path, formats, target_language) -> dict`

Save transcription in multiple formats.

**Parameters:**
- `transcription_result` (dict): Transcription data
- `video_path` (Path): Original video path
- `formats` (list): List of formats ('srt', 'txt', 'json')
- `target_language` (str): Target language code

**Returns:**
- `dict`: Dictionary mapping format to file path

## Configuration

### Settings

Configuration is managed through Pydantic models in `config.py`.

```python
from config import get_settings

settings = get_settings()
```

**Environment Variables:**
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_API_KEY`: Anthropic Claude API key
- `WHISPER_MODEL`: Default Whisper model (default: 'base')
- `WHISPER_DEVICE`: Device for Whisper ('auto', 'cpu', 'cuda')
- `TRANSLATION_SERVICE`: Default service ('openai', 'claude')
- `OUTPUT_DIR`: Default output directory
- `CACHE_ENABLED`: Enable translation cache (default: true)

### Performance Configuration

Performance optimizations in `performance_config.py`.

```python
from performance_config import PerformanceConfig

# Get optimal batch size
batch_size = PerformanceConfig.get_optimal_batch_size(total_segments)

# Get Whisper compute type
compute_type = PerformanceConfig.get_whisper_compute_type(model_size, has_gpu)
```

## CLI Usage

### Basic Command

```bash
vcg video.mp4 -t zh
```

### Advanced Options

```bash
vcg video.mp4 \
  --target-language es \
  --source-language en \
  --model large \
  --output-dir ./subtitles \
  --format srt \
  --format txt \
  --translator claude \
  --keep-temp \
  --verbose
```

### CLI Options

- `-t, --target-language`: Target language code (default: zh)
- `-s, --source-language`: Source language code (auto-detect if not specified)
- `-m, --model`: Whisper model size (tiny/base/small/medium/large)
- `-o, --output-dir`: Output directory
- `-f, --format`: Output formats (can specify multiple)
- `--translator`: Translation service (openai/claude)
- `--keep-temp`: Keep temporary files
- `-v, --verbose`: Enable verbose logging
- `--version`: Show version
- `--help`: Show help message

## Error Handling

All modules implement comprehensive error handling:

- **FileNotFoundError**: When input files don't exist
- **ValueError**: For invalid parameters or unsupported formats
- **RuntimeError**: For processing failures
- **asyncio.TimeoutError**: For API timeouts

## Examples

### Complete Workflow

```python
import asyncio
from pathlib import Path
from caption_generator import VideoCaptionGenerator

async def process_video():
    generator = VideoCaptionGenerator()
    
    result = await generator.process_video(
        video_path=Path("video.mp4"),
        target_language="zh",
        source_language=None,  # Auto-detect
        whisper_model="base",
        output_dir=Path("./output"),
        output_formats=["srt", "txt"],
        translation_service="openai",
        keep_temp=False
    )
    
    print(f"Processed: {result['video_path']}")
    print(f"Detected language: {result['detected_language']}")
    print(f"Output files: {result['output_files']}")

asyncio.run(process_video())
```

### Custom Translation

```python
from modules.translator import TranslatorFactory, TranslationSegment

# Create translator
translator = TranslatorFactory.create_translator(
    service="openai",
    api_key="your-key",
    target_language="zh"
)

# Create segments
segments = [
    TranslationSegment(0, "Hello world", 0.0, 2.5),
    TranslationSegment(1, "This is a test", 2.5, 5.0)
]

# Translate
translated = await translator.translate_batch(segments, "en")

for seg in translated:
    print(f"{seg.text} -> {seg.translated_text}")
```