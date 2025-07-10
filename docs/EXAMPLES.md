# Video Caption Generator - Usage Examples

## Table of Contents
- [Basic Usage](#basic-usage)
- [Language Options](#language-options)
- [Model Selection](#model-selection)
- [Output Formats](#output-formats)
- [Translation Services](#translation-services)
- [Advanced Features](#advanced-features)
- [Batch Processing](#batch-processing)
- [Error Handling](#error-handling)

## Basic Usage

### Simple Video Caption Generation

Generate Chinese subtitles from an English video:

```bash
vcg video.mp4
```

This will:
1. Extract audio from video.mp4
2. Transcribe speech using Whisper
3. Translate to Chinese (default)
4. Save as video.zh.srt and video.zh.txt

### Specify Target Language

Generate Spanish subtitles:

```bash
vcg video.mp4 -t es
```

Generate Japanese subtitles:

```bash
vcg video.mp4 --target-language ja
```

## Language Options

### Supported Languages

Common language codes:
- `zh` - Chinese (Simplified)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `ja` - Japanese
- `ko` - Korean
- `ru` - Russian
- `ar` - Arabic
- `pt` - Portuguese
- `it` - Italian
- `hi` - Hindi

### Auto-detect Source Language

By default, Whisper auto-detects the source language:

```bash
vcg video.mp4 -t fr
```

### Specify Source Language

For better accuracy, specify the source language:

```bash
vcg video.mp4 -s en -t zh
```

## Model Selection

### Whisper Model Sizes

Choose model based on your needs:

#### Tiny Model (Fastest, Lower Quality)
```bash
vcg video.mp4 -m tiny
```
- Size: 39 MB
- Best for: Quick processing, limited resources

#### Base Model (Default, Balanced)
```bash
vcg video.mp4 -m base
```
- Size: 74 MB
- Best for: General use, good balance

#### Small Model (Better Quality)
```bash
vcg video.mp4 -m small
```
- Size: 244 MB
- Best for: Better accuracy, moderate speed

#### Medium Model (High Quality)
```bash
vcg video.mp4 -m medium
```
- Size: 769 MB
- Best for: High accuracy, professional use

#### Large Model (Best Quality)
```bash
vcg video.mp4 -m large
```
- Size: 1550 MB
- Best for: Maximum accuracy, critical projects

## Output Formats

### Single Format

Generate only SRT subtitles:

```bash
vcg video.mp4 -f srt
```

Generate only plain text:

```bash
vcg video.mp4 -f txt
```

### Multiple Formats

Generate all formats:

```bash
vcg video.mp4 -f srt -f txt -f json
```

### Custom Output Directory

Save to specific directory:

```bash
vcg video.mp4 -o ./subtitles
```

## Translation Services

### Using OpenAI (Default)

```bash
vcg video.mp4 --translator openai
```

Required: `OPENAI_API_KEY` environment variable

### Using Claude

```bash
vcg video.mp4 --translator claude
```

Required: `CLAUDE_API_KEY` environment variable

## Advanced Features

### Keep Temporary Files

Retain intermediate files for debugging:

```bash
vcg video.mp4 --keep-temp
```

This preserves:
- Extracted audio file
- Raw transcription data

### Verbose Mode

Enable detailed logging:

```bash
vcg video.mp4 --verbose
```

Shows:
- Detailed progress information
- API calls and responses
- Error stack traces

### Combined Options

Process a long video with maximum quality:

```bash
vcg lecture.mp4 \
  --target-language zh \
  --source-language en \
  --model large \
  --output-dir ./lectures \
  --format srt \
  --format txt \
  --format json \
  --translator claude \
  --verbose
```

## Batch Processing

### Shell Script Example

Process multiple videos:

```bash
#!/bin/bash
for video in *.mp4; do
    echo "Processing $video..."
    vcg "$video" -t zh -o ./output
done
```

### Python Script Example

```python
import subprocess
from pathlib import Path

videos = Path(".").glob("*.mp4")
target_lang = "zh"

for video in videos:
    print(f"Processing {video.name}...")
    subprocess.run([
        "vcg",
        str(video),
        "-t", target_lang,
        "-o", "./output"
    ])
```

## Error Handling

### Common Issues and Solutions

#### No Audio Stream

Error: "No audio stream found in video"

Solution: Verify video has audio:
```bash
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 video.mp4
```

#### API Key Not Set

Error: "OpenAI API key not configured"

Solution:
```bash
export OPENAI_API_KEY="your-api-key"
vcg video.mp4
```

#### Out of Memory

Error: "CUDA out of memory" (GPU) or slow processing (CPU)

Solution: Use smaller model:
```bash
vcg video.mp4 -m tiny
```

#### Network Timeout

Error: "Translation timeout"

Solution: Retry with verbose mode:
```bash
vcg video.mp4 --verbose
```

### Debug Mode

For troubleshooting, combine verbose and keep-temp:

```bash
vcg video.mp4 --verbose --keep-temp
```

## Performance Tips

### For Long Videos

1. Use smaller Whisper model:
   ```bash
   vcg long_video.mp4 -m small
   ```

2. Process in parts (extract specific segments):
   ```bash
   # Extract 10 minutes starting at 30 minutes
   ffmpeg -ss 00:30:00 -t 00:10:00 -i video.mp4 part1.mp4
   vcg part1.mp4
   ```

### For Many Short Videos

Use parallel processing:

```bash
# Using GNU Parallel
parallel -j 4 vcg {} -t zh ::: *.mp4
```

### Cache Optimization

Translation cache is enabled by default. To disable:

```bash
export VCG_CACHE_ENABLED=false
vcg video.mp4
```

## Integration Examples

### With Video Editing Software

Post-process subtitles for video editing:

```bash
# Generate subtitles
vcg video.mp4 -t zh -f srt

# Convert to other subtitle formats using FFmpeg
ffmpeg -i video.zh.srt video.zh.ass
```

### With Translation Review

Generate JSON for manual review:

```bash
vcg video.mp4 -t zh -f json

# Review and edit video.zh.json
# Convert back to SRT using custom script
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Generate Subtitles
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pip install video-caption-generator
    vcg video.mp4 -t zh -o ./subtitles
```