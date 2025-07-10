# Video Caption Generator

A powerful CLI tool that automatically extracts speech from videos, converts it to text using OpenAI Whisper, and translates it to your target language using AI.

## Features

- 🎥 **Multiple Video Format Support**: MP4, AVI, MOV, MKV, and more
- 🎯 **High-Accuracy Speech Recognition**: Powered by OpenAI Whisper
- 🌍 **AI-Powered Translation**: Support for OpenAI and Claude APIs
- 📝 **Multiple Output Formats**: SRT subtitles, plain text, JSON
- 🚀 **Fast Processing**: GPU acceleration support
- 🎨 **Beautiful CLI**: Progress bars and colored output with Rich
- 🔒 **Privacy-First**: All processing done locally

## Quick Start

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/video_caption_generator.git
cd video_caption_generator
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install FFmpeg**
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. **Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```bash
# Simple usage (defaults to Chinese translation)
python caption_generator.py video.mp4

# Specify target language
python caption_generator.py video.mp4 --target-lang ja

# Use different Whisper model
python caption_generator.py video.mp4 --whisper-model large

# Full example
python caption_generator.py video.mp4 \
    --target-lang zh \
    --output-format srt \
    --whisper-model medium \
    --translator claude \
    --output-dir ./output
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--target-lang` | `-t` | Target translation language | `zh` |
| `--output-format` | `-f` | Output format (srt/txt/json) | `srt` |
| `--whisper-model` | `-m` | Whisper model size | `base` |
| `--translator` | `-T` | Translation service | `openai` |
| `--output-dir` | `-o` | Output directory | `./output` |
| `--show-progress` | `-p` | Show progress bar | `True` |
| `--debug` | `-d` | Debug mode | `False` |

## Whisper Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39M | ⚡⚡⚡⚡⚡ | ★★☆☆☆ | Quick testing |
| base | 74M | ⚡⚡⚡⚡ | ★★★☆☆ | Default choice |
| small | 244M | ⚡⚡⚡ | ★★★★☆ | Better accuracy |
| medium | 769M | ⚡⚡ | ★★★★☆ | High quality |
| large | 1550M | ⚡ | ★★★★★ | Best quality |

## Configuration

Create a `.env` file from `.env.example`:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# Default Settings
DEFAULT_TRANSLATOR=openai
DEFAULT_TARGET_LANG=zh
DEFAULT_WHISPER_MODEL=base
```

## Supported Languages

Common language codes:
- `zh` - Chinese
- `en` - English
- `ja` - Japanese
- `ko` - Korean
- `es` - Spanish
- `fr` - French
- `de` - German
- `ru` - Russian

See [ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) for more.

## Development

### Project Structure
```
video_caption_generator/
├── caption_generator.py    # Main CLI entry point
├── config.py              # Configuration management
├── modules/               # Core modules
│   ├── audio_extractor.py
│   ├── speech_recognizer.py
│   ├── translator.py
│   └── output_handler.py
└── utils/                 # Utility functions
```

### Running Tests
```bash
pytest
```

### Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

1. **Whisper model download is slow**
   - Models are cached after first download
   - Use smaller models for testing

2. **Out of memory error**
   - Use a smaller Whisper model
   - Process shorter videos
   - Enable GPU if available

3. **FFmpeg not found**
   - Ensure FFmpeg is installed and in PATH
   - Restart terminal after installation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [FFmpeg](https://ffmpeg.org/) for video processing
- [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output