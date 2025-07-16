# 视频字幕生成器

一键生成视频的中文字幕，支持自动语音识别和智能翻译。

## ✨ 功能特点

- 🎥 支持常见视频格式（MP4、AVI、MOV、MKV）
- 🌍 自动检测视频语言，翻译成中文或其他语言
- 📝 生成 SRT 字幕文件和纯文本文件
- 💰 实时显示 API 使用费用
- 📁 支持批量处理整个文件夹
- 🔄 断点续传，中断后可继续
- 🎯 **新增：段落式智能翻译** - 生成更流畅自然的字幕

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

# 使用传统逐句翻译模式（关闭段落模式）
python cli.py process video.mp4 --no-paragraph-mode

# 自定义段落分隔参数
python cli.py process video.mp4 --paragraph-silence 2.0 --paragraph-max-duration 45
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
  
  # 段落模式配置（新功能）
  paragraph_mode: true        # 启用段落模式
  paragraph_silence_threshold: 1.5  # 段落分隔的静音时长（秒）
  paragraph_max_duration: 30.0      # 单个段落最大时长（秒）
  redistribute_timestamps: true     # 智能重分配时间戳

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

### 5. 什么是段落模式？

段落模式是一种新的翻译方式，它会：
- 根据语音停顿识别自然段落
- 将整个段落作为上下文进行翻译
- 智能重新分配时间戳
- 生成更流畅、更符合目标语言表达习惯的字幕

这对于中文等语言特别有用，能避免逐句翻译的生硬感。

## 📝 命令参考

### process 命令

```bash
python cli.py process [视频路径] [选项]

选项：
  --lang, -l                    目标语言 (默认: zh-cn)
  --format, -f                  输出格式 [srt|text|both] (默认: both)
  --output-dir, -o              输出目录 (默认: 视频同目录)
  --recursive, -r               递归处理子目录
  --resume                      从断点继续
  --config, -c                  自定义配置文件
  --no-paragraph-mode           禁用段落模式，使用传统逐句翻译
  --paragraph-silence           段落分隔的静音时长（秒）
  --paragraph-max-duration      单个段落最大时长（秒）
  --no-redistribute-timestamps  禁用时间戳重分配
```

### 其他命令

```bash
# 提取音频
python cli.py extract video.mp4

# 查看配置信息
python cli.py info
```

## 🚀 最近更新

### v1.1.0 - 段落式智能翻译 (2025-01)
- ✅ 新增段落模式：基于语音停顿识别自然段落
- ✅ 智能时间戳重分配：根据译文长度和标点重新分配时间
- ✅ 更流畅的翻译：整体理解段落含义，生成自然的目标语言表达
- ✅ 可配置参数：支持自定义段落检测和时间戳分配策略

## 🎯 未来计划

### 近期目标
1. **并发处理优化**
   - 支持多视频同时处理 (`--workers` 参数)
   - 智能控制并发数，避免 API 限流
   - 预计性能提升 3-5 倍

2. **API 服务模式**
   - RESTful API 接口
   - 支持异步任务处理
   - 便于集成到其他系统

3. **自动化增强**
   - 文件夹监控模式
   - 处理结果自动上传
   - 支持 Webhook 通知

### 长期规划
- **工具平台集成** - 作为个人工具平台的字幕处理模块

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License