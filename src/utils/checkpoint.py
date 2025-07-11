"""
断点续传功能

保存处理进度，支持中断后恢复。
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib

from .exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class CheckpointManager:
    """断点管理器"""
    
    def __init__(self, checkpoint_dir: Path = None):
        """
        初始化断点管理器
        
        Args:
            checkpoint_dir: 保存断点的目录，默认为 .checkpoints
        """
        self.checkpoint_dir = checkpoint_dir or Path.cwd() / ".checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def get_checkpoint_path(self, video_path: Path) -> Path:
        """获取视频文件对应的断点文件路径
        
        使用视频文件的路径哈希作为断点文件名，避免路径中的特殊字符问题
        """
        # 生成唯一标识
        path_hash = hashlib.md5(str(video_path.absolute()).encode()).hexdigest()
        checkpoint_name = f"{video_path.stem}_{path_hash[:8]}.json"
        return self.checkpoint_dir / checkpoint_name
    
    def save_checkpoint(
        self, 
        video_path: Path,
        state: Dict[str, Any],
        stage: str,
        progress: float = 0.0
    ) -> None:
        """保存断点
        
        Args:
            video_path: 视频文件路径
            state: 当前状态数据
            stage: 当前处理阶段
            progress: 进度百分比 (0-100)
        """
        checkpoint_data = {
            "video_path": str(video_path.absolute()),
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "progress": progress,
            "state": state
        }
        
        checkpoint_path = self.get_checkpoint_path(video_path)
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存断点到: {checkpoint_path}")
        except Exception as e:
            logger.warning(f"保存断点失败: {e}")
    
    def load_checkpoint(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """加载断点
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            断点数据，如果不存在则返回 None
        """
        checkpoint_path = self.get_checkpoint_path(video_path)
        
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # 验证是否为同一文件
            if checkpoint_data.get("video_path") != str(video_path.absolute()):
                logger.warning("断点文件与视频文件不匹配")
                return None
            
            logger.info(f"加载断点: {checkpoint_path}")
            return checkpoint_data
        except Exception as e:
            logger.warning(f"加载断点失败: {e}")
            return None
    
    def remove_checkpoint(self, video_path: Path) -> None:
        """删除断点文件
        
        处理完成后删除断点
        """
        checkpoint_path = self.get_checkpoint_path(video_path)
        
        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
                logger.debug(f"删除断点: {checkpoint_path}")
            except Exception as e:
                logger.warning(f"删除断点失败: {e}")
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """列出所有断点
        
        Returns:
            断点信息列表
        """
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    "video_path": data.get("video_path"),
                    "timestamp": data.get("timestamp"),
                    "stage": data.get("stage"),
                    "progress": data.get("progress", 0),
                    "checkpoint_file": str(checkpoint_file)
                })
            except Exception as e:
                logger.warning(f"读取断点文件失败 {checkpoint_file}: {e}")
        
        # 按时间戳排序
        checkpoints.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return checkpoints
    
    def clean_old_checkpoints(self, days: int = 7) -> int:
        """清理旧断点文件
        
        Args:
            days: 保留多少天内的断点
            
        Returns:
            删除的文件数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                timestamp_str = data.get("timestamp")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp < cutoff_date:
                        checkpoint_file.unlink()
                        deleted_count += 1
                        logger.debug(f"删除过期断点: {checkpoint_file}")
            except Exception as e:
                logger.warning(f"处理断点文件失败 {checkpoint_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 个过期断点文件")
        
        return deleted_count


# 断点阶段常量
class CheckpointStage:
    """处理阶段常量"""
    AUDIO_EXTRACTION = "audio_extraction"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    FORMATTING = "formatting"
    COMPLETED = "completed"