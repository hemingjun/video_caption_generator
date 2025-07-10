"""API费用计算模块"""
from typing import Tuple
from datetime import datetime


class CostCalculator:
    """API费用计算器"""
    
    def __init__(self, pricing_config: dict):
        """初始化费用计算器
        
        Args:
            pricing_config: 价格配置字典
        """
        self.pricing = pricing_config
        self.last_updated = pricing_config.get('last_updated', 'Unknown')
    
    def calculate_whisper_cost(self, duration_seconds: float) -> float:
        """计算Whisper API费用
        
        Args:
            duration_seconds: 音频时长（秒）
            
        Returns:
            费用（美元）
        """
        duration_minutes = duration_seconds / 60
        price_per_minute = self.pricing['whisper']['price_per_minute']
        return duration_minutes * price_per_minute
    
    def calculate_gpt_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算GPT API费用
        
        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数
            
        Returns:
            费用（美元）
        """
        gpt_pricing = self.pricing['gpt4o']
        input_cost = (input_tokens / 1_000_000) * gpt_pricing['input_per_million_tokens']
        output_cost = (output_tokens / 1_000_000) * gpt_pricing['output_per_million_tokens']
        return input_cost + output_cost
    
    def format_cost_summary(
        self, 
        whisper_cost: float, 
        gpt_cost: float,
        duration_seconds: float,
        input_tokens: int,
        output_tokens: int
    ) -> str:
        """格式化费用汇总
        
        Args:
            whisper_cost: Whisper费用
            gpt_cost: GPT费用
            duration_seconds: 音频时长（秒）
            input_tokens: 输入token数
            output_tokens: 输出token数
            
        Returns:
            格式化的费用汇总字符串
        """
        total_cost = whisper_cost + gpt_cost
        duration_minutes = duration_seconds / 60
        
        whisper_price = self.pricing['whisper']['price_per_minute']
        gpt_input_price = self.pricing['gpt4o']['input_per_million_tokens']
        gpt_output_price = self.pricing['gpt4o']['output_per_million_tokens']
        
        summary = f"""💰 API使用费用明细（价格基准：{self.last_updated}）：
   📝 Whisper语音识别 ({duration_minutes:.1f}分钟 × ${whisper_price}/分钟): ${whisper_cost:.3f}
   🤖 GPT-4o翻译 ({input_tokens:,}输入 × ${gpt_input_price}/1M + {output_tokens:,}输出 × ${gpt_output_price}/1M): ${gpt_cost:.3f}
   💵 总计: ${total_cost:.3f}
   
   ℹ️  查看最新价格: {self.pricing.get('pricing_url', 'https://openai.com/api/pricing/')}"""
        
        return summary