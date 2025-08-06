"""
Game Model - 麻將對局資料模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(255), nullable=False, index=True)  # LINE 群組 ID
    mode = Column(String(50), default="台麻")  # 遊戲模式
    per_point = Column(Integer, default=10)  # 每台多少錢
    base_score = Column(Integer, default=30)  # 底台
    collect_money = Column(Boolean, default=True)  # 是否收莊錢
    status = Column(String(20), default="created")  # 狀態：created, playing, finished
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Game(id={self.id}, group_id={self.group_id}, mode={self.mode})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "mode": self.mode,
            "per_point": self.per_point,
            "base_score": self.base_score,
            "collect_money": self.collect_money,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_summary_text(self):
        """取得設定摘要文字"""
        collect_text = "是" if self.collect_money else "否"
        return f"""✅ 對局建立完成！

🀄 模式：{self.mode}
💰 每台：{self.per_point} 元
📉 底台：{self.base_score} 元
🏯 收莊錢：{collect_text}

請輸入 `/加入 暱稱` 加入此場遊戲（共 4 位）"""