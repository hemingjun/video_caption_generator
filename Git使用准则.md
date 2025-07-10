# Claude Code Git使用准则

## 🎯 核心原则
作为Claude Code，你需要主动管理项目的版本控制。以下是你必须遵循的Git使用规范。

## 📋 自动执行规则

### 1. 项目初始化时
```bash
# 当创建新项目时，自动执行：
git init
git config user.name "Claude Code"
git config user.email "claude@notion-supabase-sync.local"

# 创建.gitignore文件，必须包含：
.env
config/.env
*.log
data/logs/
data/cache/
data/backups/
__pycache__/
*.pyc
.DS_Store
.vscode/
.idea/

# 初始提交
git add .
git commit -m "init: 项目初始化"
```

### 2. 分支管理规则

**默认工作分支**：`develop`

```bash
# 项目开始后立即创建develop分支
git checkout -b develop

# 所有开发工作都在develop分支进行
# 除非用户明确要求，否则不要切换到main分支
```

### 3. 提交时机和规范

#### 必须提交的时机：
1. **完成一个独立功能模块后**
2. **修复一个bug后**
3. **完成一个任务清单项后**
4. **每个工作阶段结束时**
5. **创建或更新重要文档后**

#### 提交信息格式：
```
<类型>(<范围>): <简短描述>

[可选的详细描述]
```

#### 类型标识：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具
- `phase`: 阶段性完成标记

### 4. 具体场景的Git操作

#### 场景1：完成新功能
```bash
# 查看改动
git status

# 添加相关文件
git add [相关文件路径]

# 提交
git commit -m "feat(模块名): 实现XX功能"

# 示例
git add sync/logger.py utils/logger.py
git commit -m "feat(logger): 实现分级日志系统，支持文件输出和日志轮转"
```

#### 场景2：修复问题
```bash
git add [修复的文件]
git commit -m "fix(模块名): 修复XX问题"

# 示例
git add sync/notion_client.py
git commit -m "fix(notion): 修复API请求超时问题，添加重试机制"
```

#### 场景3：更新文档
```bash
git add docs/
git commit -m "docs: 更新XX文档"

# 示例
git add docs/README.md
git commit -m "docs: 更新安装说明，添加环境变量配置步骤"
```

#### 场景4：阶段性提交
```bash
# 开始新阶段时
git add .
git commit -m "phase(N): 开始第N阶段 - [阶段名称]"

# 完成阶段时
git add .
git commit -m "phase(N): 完成第N阶段 - [阶段名称]"

# 添加开发报告
git add docs/dev_report/
git commit -m "docs: 添加第N阶段开发报告"
```

### 5. 提交前检查清单

每次提交前，自动检查：
- [ ] 是否有敏感信息（如API密钥）被包含？
- [ ] 代码是否可以正常运行？
- [ ] 是否只包含相关的文件修改？
- [ ] 提交信息是否清晰描述了改动？

### 6. 状态报告规则

在以下情况下，主动报告Git状态：
1. 每完成3个提交后
2. 每个阶段开始和结束时
3. 遇到Git相关问题时

报告格式：
```
📊 Git状态报告：
- 当前分支：develop
- 最近提交：[显示最近3条]
- 工作区状态：[干净/有未提交的修改]
- 本阶段提交数：X次
```

### 7. 禁止的操作

**永远不要自动执行以下操作**（除非用户明确要求）：
- `git push` - 推送到远程仓库
- `git pull` - 从远程拉取
- `git merge main` - 合并主分支
- `git reset --hard` - 硬重置
- `git push --force` - 强制推送
- 删除任何分支

### 8. 异常处理

遇到以下情况时的处理方式：

#### 合并冲突
```bash
# 立即停止并报告
"遇到合并冲突，需要您的指导：
冲突文件：[列出文件]
建议：[提供解决建议]"
```

#### 提交错误
```bash
# 如果刚提交就发现错误
git commit --amend -m "新的提交信息"
# 但要先询问用户
```

### 9. 分支策略

```
main/master          # 稳定版本（不直接修改）
└── develop         # 日常开发（主要工作分支）
    └── phase/N-*   # 阶段性分支（可选，需用户同意）
```

### 10. 最佳实践

1. **提交粒度**：每个提交只做一件事
2. **提交频率**：完成独立功能就提交，不要积累太多修改
3. **提交信息**：使用中文说明具体做了什么
4. **文件选择**：只添加相关文件，避免提交临时文件

## 📝 工作流程示例

```bash
# 1. 开始工作
git status  # 检查工作区状态

# 2. 完成功能模块
git add sync/engine.py
git commit -m "feat(sync): 实现基础同步引擎"

# 3. 修复发现的问题
git add sync/engine.py
git commit -m "fix(sync): 修复空值处理异常"

# 4. 更新文档
git add README.md
git commit -m "docs: 添加同步引擎使用说明"

# 5. 完成阶段
git add .
git commit -m "phase(3): 完成countries表同步功能"

# 6. 生成报告
git log --oneline -10  # 查看提交历史
```

## 🎯 记住

1. **主动管理版本**：不要等用户提醒才提交
2. **保持提交整洁**：每个提交都应该是完整的、可运行的
3. **详细记录变更**：提交信息要让人理解你做了什么
4. **安全第一**：不确定的操作要先询问
5. **定期汇报**：让用户了解项目的版本控制状态

## 🚨 重要提醒

- 如果不确定是否应该提交，先提交到本地（可以后续修改）
- 遇到任何Git报错，立即停止并寻求指导
- 保护用户数据安全，永不提交敏感信息
- 当用户说"推送到GitHub"时，才执行push操作

---

遵循这些准则，你就能有效地管理项目的版本控制，让代码历史清晰可追溯。