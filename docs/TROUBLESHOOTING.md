# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Error: "No module named 'whisper'"

**Problem**: Whisper is not installed properly.

**Solution**:
```bash
pip install openai-whisper
```

#### Error: "ffmpeg not found"

**Problem**: FFmpeg is not installed or not in PATH.

**Solution**:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt update && sudo apt install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

#### CUDA/GPU Issues

**Problem**: "CUDA out of memory" or "No CUDA GPUs are available"

**Solutions**:
1. Force CPU mode:
   ```bash
   export WHISPER_DEVICE=cpu
   vcg video.mp4
   ```

2. Use smaller model:
   ```bash
   vcg video.mp4 -m tiny
   ```

3. Check CUDA installation:
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

### Runtime Errors

#### API Key Errors

**Problem**: "OpenAI API key not configured" or "Claude API key not configured"

**Solution**:
```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Claude
export CLAUDE_API_KEY="sk-ant-..."

# Or create .env file
echo "OPENAI_API_KEY=sk-..." > .env
echo "CLAUDE_API_KEY=sk-ant-..." >> .env
```

#### File Not Found

**Problem**: "Video file not found: path/to/video.mp4"

**Solutions**:
1. Check file path:
   ```bash
   ls -la path/to/video.mp4
   ```

2. Use absolute path:
   ```bash
   vcg /absolute/path/to/video.mp4
   ```

3. Check file permissions:
   ```bash
   chmod 644 video.mp4
   ```

#### No Audio Stream

**Problem**: "No audio stream found in video"

**Solutions**:
1. Verify audio stream exists:
   ```bash
   ffprobe -v error -show_streams video.mp4 | grep codec_type=audio
   ```

2. Extract and check audio:
   ```bash
   ffmpeg -i video.mp4 -vn -acodec copy audio.aac
   ```

### Translation Issues

#### Empty or Incorrect Translations

**Problem**: Translations are empty or incorrect.

**Solutions**:
1. Check API quota/limits
2. Verify source language detection:
   ```bash
   vcg video.mp4 -s en -t zh --verbose
   ```
3. Try different translation service:
   ```bash
   vcg video.mp4 --translator claude
   ```

#### Translation Timeout

**Problem**: "Translation timeout" errors.

**Solutions**:
1. Increase timeout in environment:
   ```bash
   export VCG_TRANSLATION_TIMEOUT=60
   ```

2. Process smaller segments:
   ```bash
   vcg video.mp4 -m tiny  # Faster transcription
   ```

3. Check network connectivity:
   ```bash
   curl -I https://api.openai.com
   ```

### Performance Issues

#### Slow Processing

**Problem**: Processing takes too long.

**Solutions**:
1. Use smaller Whisper model:
   ```bash
   vcg video.mp4 -m tiny  # Fastest
   vcg video.mp4 -m base  # Balanced
   ```

2. Enable GPU acceleration:
   ```bash
   # Check GPU availability
   python -c "import torch; print(torch.cuda.is_available())"
   
   # Force GPU usage
   export WHISPER_DEVICE=cuda
   ```

3. Process shorter segments:
   ```bash
   # Split video first
   ffmpeg -i long_video.mp4 -c copy -ss 00:00:00 -t 00:30:00 part1.mp4
   vcg part1.mp4
   ```

#### High Memory Usage

**Problem**: Process killed due to memory.

**Solutions**:
1. Use smaller model:
   ```bash
   vcg video.mp4 -m tiny
   ```

2. Increase system swap:
   ```bash
   # Linux
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. Process in chunks (see Performance Issues)

### Output Issues

#### Corrupted Output Files

**Problem**: SRT or other output files are corrupted.

**Solutions**:
1. Check encoding:
   ```bash
   file -i output.srt
   iconv -f ISO-8859-1 -t UTF-8 output.srt > output_fixed.srt
   ```

2. Validate SRT format:
   ```python
   import pysrt
   subs = pysrt.open('output.srt')
   print(f"Loaded {len(subs)} subtitles")
   ```

#### Missing Timestamps

**Problem**: Subtitles have incorrect or missing timestamps.

**Solutions**:
1. Use verbose mode to check segment data:
   ```bash
   vcg video.mp4 --verbose
   ```

2. Try different Whisper parameters:
   ```bash
   vcg video.mp4 --no-condition-on-previous-text
   ```

### Environment Issues

#### Permission Denied

**Problem**: "Permission denied" errors.

**Solutions**:
1. Check file permissions:
   ```bash
   ls -la video.mp4
   chmod 644 video.mp4
   ```

2. Check output directory permissions:
   ```bash
   mkdir -p output
   chmod 755 output
   vcg video.mp4 -o ./output
   ```

#### Temp Directory Issues

**Problem**: "No space left on device" in temp directory.

**Solutions**:
1. Clean temp directory:
   ```bash
   rm -rf /tmp/vcg_*
   ```

2. Use custom temp directory:
   ```bash
   export TMPDIR=/path/to/larger/disk
   vcg video.mp4
   ```

3. Keep temp files in current directory:
   ```bash
   vcg video.mp4 --keep-temp
   ```

## Debug Commands

### Enable Full Debugging

```bash
# Maximum verbosity
vcg video.mp4 --verbose --keep-temp

# With environment debugging
VCG_DEBUG=1 vcg video.mp4 --verbose
```

### Check Dependencies

```python
# check_deps.py
import sys

def check_import(module):
    try:
        __import__(module)
        print(f"✓ {module}")
    except ImportError as e:
        print(f"✗ {module}: {e}")

modules = [
    'whisper',
    'openai',
    'anthropic',
    'ffmpeg',
    'rich',
    'click',
    'pydantic'
]

for module in modules:
    check_import(module)

# Check ffmpeg
import subprocess
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    print("✓ ffmpeg")
except:
    print("✗ ffmpeg not found")
```

### Test Basic Functionality

```python
# test_basic.py
import asyncio
from pathlib import Path

async def test_modules():
    # Test audio extraction
    from modules.audio_extractor import AudioExtractor
    extractor = AudioExtractor()
    print("✓ AudioExtractor loaded")
    
    # Test speech recognizer
    from modules.speech_recognizer import SpeechRecognizer
    recognizer = SpeechRecognizer(model_name="tiny")
    print("✓ SpeechRecognizer loaded")
    
    # Test translator
    from modules.translator import TranslatorFactory
    print("✓ TranslatorFactory loaded")
    
    # Test output handler
    from modules.output_handler import OutputHandler
    handler = OutputHandler()
    print("✓ OutputHandler loaded")

asyncio.run(test_modules())
```

## Getting Help

### Gather Debug Information

When reporting issues, include:

1. System information:
   ```bash
   python --version
   pip show video-caption-generator
   ffmpeg -version
   ```

2. Full error output:
   ```bash
   vcg video.mp4 --verbose 2> error.log
   ```

3. Environment:
   ```bash
   env | grep -E "(OPENAI|CLAUDE|WHISPER|VCG)"
   ```

### Community Support

- GitHub Issues: [Report bugs and request features](https://github.com/yourusername/video_caption_generator/issues)
- Discussions: [Ask questions and share tips](https://github.com/yourusername/video_caption_generator/discussions)

### Professional Support

For commercial use or priority support, contact: support@videocaption.dev