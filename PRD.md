# 视频字幕生成工具 产品需求文档（PRD）

## 1. 产品概述

### 1.1 产品背景
随着视频内容的爆炸式增长，快速提取视频中的语音内容并翻译成其他语言的需求日益增长。传统的字幕制作流程耗时耗力，需要一个自动化工具来提升效率。

### 1.2 产品定位
**产品名称**：Video Caption Generator  
**产品类型**：命令行工具（CLI）  
**核心功能**：自动提取视频中的语音内容，转换为文字并翻译成目标语言

### 1.3 核心价值
- **自动化**：一键完成从视频到翻译字幕的全流程
- **高准确度**：使用先进的语音识别和AI翻译技术
- **本地处理**：保护用户隐私，无需上传视频到云端
- **易维护**：模块化设计，代码简洁清晰

### 1.4 目标用户
- 需要为外语视频制作字幕的内容创作者
- 需要理解外语视频内容的学习者
- 需要处理多语言视频资料的研究人员

## 2. 功能需求

### 2.1 核心功能列表

| 功能模块 | 功能描述 | 优先级 |
|---------|---------|--------|
| 视频输入 | 支持常见视频格式（MP4、AVI、MOV、MKV等） | P0 |
| 音频提取 | 从视频中提取音频轨道 | P0 |
| 语音识别 | 使用OpenAI Whisper将音频转换为文字 | P0 |
| AI翻译 | 支持OpenAI/Claude API进行文本翻译 | P0 |
| 结果输出 | 支持多种格式（SRT字幕、纯文本、JSON） | P0 |
| 进度显示 | 实时显示处理进度 | P1 |
| 模型选择 | 支持选择不同的Whisper模型 | P1 |
| 错误处理 | 友好的错误提示和恢复机制 | P1 |

### 2.2 用户使用流程

```mermaid
graph LR
    A[用户输入视频文件] --> B[提取音频]
    B --> C[语音识别]
    C --> D[获取原文文本]
    D --> E[AI翻译]
    E --> F[生成输出文件]
    F --> G[完成]
```

### 2.3 命令行接口设计

#### 基本用法
```bash
# 最简单的使用方式（默认翻译为中文）
python caption_generator.py video.mp4

# 指定目标语言
python caption_generator.py video.mp4 --target-lang ja

# 指定输出格式
python caption_generator.py video.mp4 --output-format srt

# 完整参数示例
python caption_generator.py video.mp4 \
    --target-lang zh \
    --output-format srt \
    --whisper-model medium \
    --translator claude \
    --output-dir ./output
```

#### 参数说明
| 参数 | 简写 | 描述 | 默认值 |
|-----|------|------|--------|
| input_video | - | 输入视频文件路径 | 必需参数 |
| --target-lang | -t | 目标翻译语言 | zh（中文） |
| --output-format | -f | 输出格式(srt/txt/json) | srt |
| --whisper-model | -m | Whisper模型大小 | base |
| --translator | -T | 翻译服务(openai/claude) | openai |
| --output-dir | -o | 输出目录 | ./output |
| --show-progress | -p | 显示进度条 | True |
| --debug | -d | 调试模式 | False |

## 3. 技术方案

### 3.1 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   CLI Interface                      │
│                  (Click + Rich)                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│                  Core Processor                      │
│              (Orchestration Layer)                   │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────────┐
        │         │         │             │
┌───────┴───┐ ┌───┴───┐ ┌───┴───┐ ┌──────┴──────┐
│  Audio    │ │Speech │ │ Trans │ │   Output    │
│ Extractor │ │Recog  │ │ lator │ │  Handler    │
│(FFmpeg)   │ │(Whisper)│ │(AI API)│ │(File I/O)  │
└───────────┘ └───────┘ └───────┘ └─────────────┘
```

### 3.2 技术栈（最新版本）

```python
# Python版本
Python 3.12+

# 核心依赖
openai-whisper    # 最新版 - 语音识别
ffmpeg-python     # 最新版 - 视频处理
openai           # 最新版 - OpenAI API
anthropic        # 最新版 - Claude API
click            # 最新版 - CLI框架
python-dotenv    # 最新版 - 环境变量管理
rich             # 最新版 - 美化输出
tqdm             # 最新版 - 进度条
pydantic         # 最新版 - 数据验证
aiohttp          # 最新版 - 异步HTTP
```

### 3.3 项目结构

```
video_caption_generator/
├── README.md                 # 项目说明文档
├── PRD.md                   # 产品需求文档（本文件）
├── requirements.txt         # Python依赖列表
├── setup.py                # 安装配置
├── .env.example            # 环境变量示例
├── .gitignore              # Git忽略文件
├── caption_generator.py    # 主程序入口
├── config.py               # 配置管理
├── modules/                # 核心模块目录
│   ├── __init__.py
│   ├── video_processor.py     # 视频处理核心
│   ├── audio_extractor.py     # 音频提取模块
│   ├── speech_recognizer.py   # 语音识别模块
│   ├── translator.py          # 翻译模块
│   └── output_handler.py      # 输出处理模块
├── utils/                  # 工具函数目录
│   ├── __init__.py
│   ├── file_utils.py          # 文件操作工具
│   ├── time_utils.py          # 时间处理工具
│   └── logger.py              # 日志工具
└── tests/                  # 测试目录
    ├── __init__.py
    ├── test_audio_extractor.py
    ├── test_speech_recognizer.py
    └── test_translator.py
```

### 3.4 核心模块设计

#### 3.4.1 音频提取模块（audio_extractor.py）
```python
class AudioExtractor:
    """负责从视频文件中提取音频"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        
    def extract_audio(self, output_path: str) -> str:
        """提取音频并转换为WAV格式"""
        # 使用ffmpeg-python提取音频
        # 转换为16kHz采样率（Whisper要求）
        # 返回音频文件路径
```

#### 3.4.2 语音识别模块（speech_recognizer.py）
```python
class SpeechRecognizer:
    """使用OpenAI Whisper进行语音识别"""
    
    def __init__(self, model_name: str = "base"):
        self.model = self._load_model(model_name)
        
    def recognize(self, audio_path: str) -> dict:
        """识别音频并返回带时间戳的文本"""
        # 加载音频文件
        # 使用Whisper进行识别
        # 返回格式：{"segments": [...], "text": "..."}
```

#### 3.4.3 翻译模块（translator.py）
```python
class Translator(ABC):
    """翻译基类"""
    
    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        pass

class OpenAITranslator(Translator):
    """OpenAI翻译实现"""
    
class ClaudeTranslator(Translator):
    """Claude翻译实现"""
```

#### 3.4.4 输出处理模块（output_handler.py）
```python
class OutputHandler:
    """处理不同格式的输出"""
    
    def save_srt(self, segments: List[Segment], output_path: str):
        """生成SRT字幕文件"""
        
    def save_text(self, text: str, output_path: str):
        """保存纯文本"""
        
    def save_json(self, data: dict, output_path: str):
        """保存JSON格式"""
```

## 4. 非功能需求

### 4.1 性能要求
- 视频处理速度：对于1小时的视频，总处理时间不超过10分钟（取决于硬件）
- 内存占用：最大不超过4GB
- 支持GPU加速（如果可用）

### 4.2 兼容性要求
- 操作系统：Windows 10+、macOS 10.15+、Ubuntu 20.04+
- Python版本：3.12+
- 需要安装FFmpeg

### 4.3 安全性要求
- API密钥通过环境变量管理，不硬编码
- 临时文件使用后自动清理
- 不收集或上传用户数据

### 4.4 用户体验要求
- 清晰的进度提示
- 友好的错误信息
- 支持中断后继续处理
- 彩色输出提升可读性

## 5. 配置管理

### 5.1 环境变量配置（.env）
```bash
# API配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# 默认设置
DEFAULT_TRANSLATOR=openai
DEFAULT_TARGET_LANG=zh
DEFAULT_WHISPER_MODEL=base
DEFAULT_OUTPUT_FORMAT=srt

# 高级设置
WHISPER_DEVICE=cuda  # cuda/cpu
MAX_SEGMENT_LENGTH=5000  # 最大分段长度（字符）
API_TIMEOUT=30  # API超时时间（秒）
```

### 5.2 配置优先级
1. 命令行参数（最高优先级）
2. 环境变量
3. 配置文件
4. 默认值（最低优先级）

## 6. 开发指南

### 6.1 环境搭建
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/video_caption_generator.git
cd video_caption_generator

# 2. 创建虚拟环境（Python 3.12+）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装FFmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: 下载并添加到PATH

# 5. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加API密钥
```

### 6.2 开发流程
1. 创建功能分支：`git checkout -b feature/xxx`
2. 编写代码，遵循PEP 8规范
3. 编写单元测试
4. 运行测试：`pytest`
5. 提交代码：`git commit -m "feat: add xxx"`

### 6.3 代码规范
- 使用类型提示（Type Hints）
- 使用docstring记录函数/类
- 模块长度不超过200行
- 函数长度不超过30行
- 使用异步处理API调用

### 6.4 测试方案
- 单元测试：每个模块独立测试
- 集成测试：测试完整工作流
- 性能测试：测试大文件处理
- 错误测试：测试异常处理

## 7. 版本规划

### v1.0.0（MVP版本）
- [ ] 基本的视频转字幕功能
- [ ] 支持OpenAI Whisper语音识别
- [ ] 支持OpenAI/Claude翻译
- [ ] SRT格式输出
- [ ] 命令行界面

### v1.1.0（计划中）
- [ ] Web界面
- [ ] 实时预览
- [ ] 字幕编辑功能
- [ ] 多语言同时翻译

## 8. 附录

### 8.1 支持的语言代码
- zh: 中文
- en: 英文
- ja: 日文
- ko: 韩文
- es: 西班牙语
- fr: 法语
- de: 德语
- ru: 俄语
- （更多语言参考ISO 639-1标准）

### 8.2 Whisper模型对比
| 模型 | 参数量 | 速度 | 准确度 | 推荐场景 |
|------|--------|------|---------|----------|
| tiny | 39M | 最快 | 一般 | 快速测试 |
| base | 74M | 快 | 良好 | 默认选择 |
| small | 244M | 中等 | 较好 | 平衡选择 |
| medium | 769M | 较慢 | 很好 | 高质量 |
| large | 1550M | 慢 | 最好 | 专业用途 |

### 8.3 常见问题
1. **Q: 为什么识别速度很慢？**  
   A: 可以尝试使用smaller的模型，或启用GPU加速

2. **Q: 翻译结果不理想怎么办？**  
   A: 可以尝试切换翻译服务，或调整翻译提示词

3. **Q: 支持哪些视频格式？**  
   A: 理论上支持FFmpeg支持的所有格式

---

*文档版本：1.0.0*  
*最后更新：2024-01-10*