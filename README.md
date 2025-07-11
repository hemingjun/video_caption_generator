# 视频字幕生成器

一键生成视频的中文字幕，支持自动语音识别和智能翻译。

## ✨ 功能特点

- 🎥 支持常见视频格式（MP4、AVI、MOV、MKV）
- 🌍 自动检测视频语言，翻译成中文或其他语言
- 📝 生成 SRT 字幕文件和纯文本文件
- 💰 实时显示 API 使用费用
- 📁 支持批量处理整个文件夹
- 🔄 断点续传，中断后可继续

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/video_caption_generator.git
cd video_caption_generator

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装 FFmpeg

- **Mac**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载并添加到 PATH

### 3. 设置 OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 4. 开始使用

```bash
# 处理单个视频
python cli.py process video.mp4

# 处理文件夹中的所有视频
python cli.py process ./videos/
```

## 📖 使用示例

### 基础用法

```bash
# 生成中文字幕（默认）
python cli.py process movie.mp4

# 翻译成其他语言
python cli.py process movie.mp4 --lang ja  # 日语
python cli.py process movie.mp4 --lang en  # 英语

# 指定输出目录
python cli.py process movie.mp4 --output-dir ./subtitles/
```

### 批量处理

```bash
# 处理文件夹中的所有视频
python cli.py process ./videos/

# 递归处理子文件夹
python cli.py process ./videos/ --recursive
```

### 高级选项

```bash
# 只生成 SRT 文件
python cli.py process video.mp4 --format srt

# 使用自定义配置文件
python cli.py process video.mp4 --config my_config.yaml

# 从上次中断的地方继续
python cli.py process video.mp4 --resume
```

## ⚙️ 配置说明

复制 `config.example.yaml` 为 `config.yaml` 并根据需要修改：

```yaml
# 主要配置项
openai:
  api_key: ${OPENAI_API_KEY}  # API密钥
  model: gpt-4o-mini          # 使用的模型（推荐 gpt-4o-mini）

translation:
  target_language: zh-cn      # 目标语言
  batch_size: 10             # 批量翻译大小

output:
  format: both               # 输出格式：srt/text/both
  include_original: true     # 是否包含原文
```

## 💵 费用说明

处理完成后会显示 API 使用费用：

```
💰 API 使用费用汇总
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Whisper 语音识别: $0.30 (50.0分钟)
  GPT 翻译: $0.25 (输入:50000 输出:45000 tokens)
  总计: $0.55 USD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

当前价格（2025年1月）：
- Whisper: $0.006/分钟
- GPT-4o-mini: 输入 $0.15/百万tokens，输出 $0.60/百万tokens

## 🛠️ 常见问题

### 1. 如何获取 OpenAI API Key？

访问 [platform.openai.com](https://platform.openai.com/api-keys) 创建 API Key。

### 2. 支持哪些语言？

- 源语言：自动检测，支持 90+ 种语言
- 目标语言：任意语言，常用代码：
  - `zh-cn` 简体中文
  - `zh-tw` 繁体中文
  - `en` 英语
  - `ja` 日语
  - `ko` 韩语

### 3. 处理大文件会出错吗？

不会。程序会自动将大文件分段处理，每段 5 分钟。

### 4. 可以修改字幕样式吗？

可以在 `config.yaml` 中调整：
- `srt_max_line_length`: 每行最大字符数
- `include_original`: 是否显示原文

## 📝 命令参考

### process 命令

```bash
python cli.py process [视频路径] [选项]

选项：
  --lang, -l          目标语言 (默认: zh-cn)
  --format, -f        输出格式 [srt|text|both] (默认: both)
  --output-dir, -o    输出目录 (默认: 视频同目录)
  --recursive, -r     递归处理子目录
  --resume           从断点继续
  --config, -c       自定义配置文件
```

### 其他命令

```bash
# 提取音频
python cli.py extract video.mp4

# 查看配置信息
python cli.py info
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License