# API价格更新指南

## 概述
本项目会在处理完视频后显示API使用费用。价格信息存储在配置文件中，便于更新。

## 更新价格

### 1. 查看最新价格
访问 OpenAI 官方价格页面：https://openai.com/api/pricing/

### 2. 更新配置文件
编辑 `config.yaml` 文件中的 `api_pricing` 部分：

```yaml
# API 价格配置（最后更新：2025-01-10）
api_pricing:
  whisper:
    price_per_minute: 0.006  # 美元/分钟
    currency: USD
  gpt4o:
    input_per_million_tokens: 5.0  # 美元/百万token
    output_per_million_tokens: 20.0  # 美元/百万token
    currency: USD
  pricing_url: https://openai.com/api/pricing/
  last_updated: "2025-01-10"  # 记得更新这个日期
```

### 3. 价格说明
- **Whisper**: 按分钟计费，当前价格为 $0.006/分钟
- **GPT-4o**: 按token计费
  - 输入: $5/百万token
  - 输出: $20/百万token

### 4. 费用显示示例
处理完成后会显示如下信息：
```
💰 API使用费用明细（价格基准：2025-01-10）：
   📝 Whisper语音识别 (5.0分钟 × $0.006/分钟): $0.030
   🤖 GPT-4o翻译 (1,500输入 × $5.0/1M + 4,500输出 × $20.0/1M): $0.098
   💵 总计: $0.128
   
   ℹ️  查看最新价格: https://openai.com/api/pricing/
```

## 注意事项
1. 价格可能会随时变化，建议定期检查更新
2. 费用计算基于API返回的实际token使用量，准确可靠
3. 显示的费用为预估值，实际账单以OpenAI官方为准