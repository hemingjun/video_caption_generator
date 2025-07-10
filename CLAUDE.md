# Video Caption Generator 项目 AI助手指南

## 🎯 项目概述
**项目名称**：Video Caption Generator  
**项目类型**：命令行工具（CLI）  
**核心功能**：自动提取视频语音并翻译成目标语言字幕  
**技术栈**：Python 3.12+, OpenAI Whisper, FFmpeg, OpenAI/Claude API

## 📋 三阶段工作流程

### 阶段一：分析问题 【分析问题】
**触发时机**：收到新需求或遇到技术问题时

**必须做的事**：
- 理解需求本质，不要被表面现象迷惑
- 搜索相关代码，了解现有实现
- 评估对其他模块的影响
- 发现潜在的架构问题
- 考虑未来扩展性

**关键问题**：
1. 这个功能应该放在哪个模块？
2. 会影响哪些现有代码？
3. 有没有可复用的代码？
4. 是否符合项目的模块化设计？

### 阶段二：制定方案 【制定方案】
**前置条件**：理解清楚需求，获得必要的技术决策

**输出内容**：
- 列出所有需要变更的文件
- 说明每个文件的修改内容
- 评估实施难度和风险

**自动进入执行条件**：
- 变更文件 ≤ 3个
- 总代码行数 < 30行

### 阶段三：执行方案 【执行方案】
**执行要求**：
- 严格按照方案实施
- 代码符合项目规范
- 完成后运行测试
- 及时提交Git

## 🏗️ 项目结构规范

```
video_caption_generator/
├── caption_generator.py    # 主入口，命令行接口
├── config.py              # 配置管理
├── modules/               # 核心功能模块
│   ├── audio_extractor.py    # 音频提取
│   ├── speech_recognizer.py  # 语音识别(Whisper)
│   ├── translator.py         # AI翻译
│   └── output_handler.py     # 输出处理
└── utils/                 # 工具函数
    ├── file_utils.py
    └── logger.py
```

## 💻 编码规范

### Python代码标准
- 使用Python 3.12+特性
- 所有函数添加类型提示
- 模块不超过200行
- 函数不超过30行
- 使用异步处理API调用

### 命名规范
- 类名：PascalCase（如 `AudioExtractor`）
- 函数名：snake_case（如 `extract_audio`）
- 常量：UPPER_CASE（如 `MAX_SEGMENT_LENGTH`）
- 私有方法：前缀下划线（如 `_load_model`）

### 错误处理
```python
# 使用具体的异常类型
try:
    result = await translator.translate(text)
except APIError as e:
    logger.error(f"翻译API错误: {e}")
    # 提供用户友好的错误信息
```

## 🔧 核心模块职责

### audio_extractor.py
- 使用ffmpeg提取视频音频
- 转换为Whisper支持的格式(16kHz WAV)
- 处理各种视频格式

### speech_recognizer.py  
- 加载和管理Whisper模型
- 执行语音识别
- 返回带时间戳的文本段

### translator.py
- 统一的翻译接口(支持OpenAI/Claude)
- 智能文本分段
- 保持时间戳对齐

### output_handler.py
- 生成SRT字幕文件
- 导出纯文本
- 保存JSON格式

## 📚 库文档获取

### 重要原则
**当需要使用任何第三方库时，必须使用 context7 获取最新的库文档和使用方法。**

### 使用方法
在提示中添加 "use context7" 来获取最新文档：
- "如何使用 OpenAI Whisper？use context7"
- "ffmpeg-python 提取音频的方法？use context7"
- "Rich 库如何显示进度条？use context7"

### 项目主要依赖库
- openai-whisper - 语音识别
- ffmpeg-python - 视频处理
- openai - OpenAI API
- anthropic - Claude API
- click - CLI框架
- rich - 终端美化
- pydantic - 数据验证

## 📝 Git提交规范

### 提交时机
- 完成一个功能模块
- 修复一个bug
- 更新文档
- 每个工作阶段结束

### 提交格式
```
<type>(<scope>): <description>

# 类型：
feat     - 新功能
fix      - 修复bug  
docs     - 文档更新
refactor - 代码重构
test     - 测试相关
chore    - 构建/工具

# 示例：
feat(translator): 添加Claude API支持
fix(audio): 修复长视频内存溢出问题
docs: 更新命令行使用说明
```

### 分支策略
- `main` - 稳定版本
- `develop` - 开发分支（日常工作）
- 不直接在main分支工作

## 🚀 开发流程

### 1. 需求分析
- 理解用户真实需求
- 评估技术可行性
- 确定实现方案

### 2. 模块化开发
- 每个功能独立模块
- 明确输入输出接口
- 编写单元测试

### 3. 集成测试
- 测试完整工作流
- 验证各种边界情况
- 性能测试

### 4. 用户体验
- 清晰的进度提示
- 友好的错误信息
- 美观的输出格式(使用Rich库)

## ⚠️ 注意事项

### 必须遵守
1. API密钥只通过环境变量管理
2. 不提交敏感信息到Git
3. 临时文件使用后清理
4. 所有用户输入进行验证
5. **使用库时必须通过 context7 获取最新文档**

### 性能优化
1. 大文件分块处理
2. 使用异步IO
3. 支持GPU加速(如可用)
4. 实现进度显示

### 用户交互
1. 使用Rich库美化输出
2. 显示实时进度
3. 提供有用的错误提示
4. 支持调试模式

## 🔍 常见问题处理

### Whisper模型选择
- tiny/base: 快速测试
- small/medium: 平衡选择  
- large: 最高质量

### 翻译优化
- 分段处理长文本
- 保持上下文连贯
- 处理专业术语

### 错误恢复
- 网络错误自动重试
- 保存中间结果
- 支持断点续传

## 📊 项目状态检查

定期检查：
- [ ] 代码是否符合规范
- [ ] 文档是否同步更新  
- [ ] 测试是否通过
- [ ] Git提交是否规范
- [ ] 依赖是否最新

## 🎯 核心原则

1. **简单优先**：不过度设计，保持代码简洁
2. **模块独立**：各模块职责清晰，接口明确
3. **用户友好**：清晰的提示，优雅的错误处理
4. **持续改进**：发现问题及时重构
5. **安全第一**：保护用户数据和隐私

---

记住：好的代码是为人类编写的，机器只是顺便执行它。