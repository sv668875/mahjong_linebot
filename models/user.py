"""
User Model - 用戶身份綁定資料模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String(255), unique=True, nullable=False, index=True)  # LINE 使用者 ID（唯一）
    display_name = Column(String(100), nullable=False)  # 顯示名稱（可重複）
    preferred_nickname = Column(String(100), nullable=True)  # 使用者設定的慣用暱稱
    total_games = Column(Integer, default=0)  # 總對局數
    total_win_amount = Column(Float, default=0.0)  # 總贏取金額
    total_lose_amount = Column(Float, default=0.0)  # 總輸掉金額
    net_amount = Column(Float, default=0.0)  # 淨輸贏金額
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(line_user_id={self.line_user_id}, nickname={self.preferred_nickname})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "line_user_id": self.line_user_id,
            "display_name": self.display_name,
            "preferred_nickname": self.preferred_nickname,
            "total_games": self.total_games,
            "total_win_amount": self.total_win_amount,
            "total_lose_amount": self.total_lose_amount,
            "net_amount": self.net_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_effective_nickname(self):
        """取得有效的暱稱（優先使用慣用暱稱，其次使用顯示名稱）"""
        return self.preferred_nickname or self.display_name
    
    def get_stats_summary(self):
        """取得統計摘要文字"""
        win_rate = 0
        if self.total_games > 0:
            # 這裡簡化計算，實際可能需要更複雜的勝率計算
            if self.net_amount > 0:
                win_rate = min(100, (self.net_amount / (abs(self.total_win_amount) + abs(self.total_lose_amount)) * 100))
        
        status_emoji = "📈" if self.net_amount > 0 else "📉" if self.net_amount < 0 else "📊"
        
        return f"""👤 個人統計：{self.get_effective_nickname()}

🎮 總對局：{self.total_games} 局
💰 總輸贏：{self.net_amount:+.0f} 元 {status_emoji}
📊 贏取：{self.total_win_amount:.0f} 元
📉 輸掉：{self.total_lose_amount:.0f} 元

💡 提醒：統計數據僅包含使用機器人記錄的對局"""
    
    def update_game_result(self, win_amount, lose_amount):
        """更新遊戲結果統計"""
        self.total_games += 1
        self.total_win_amount += win_amount
        self.total_lose_amount += lose_amount
        self.net_amount = self.total_win_amount - self.total_lose_amount