"""
Player Model - 玩家資料模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    line_user_id = Column(String(255), nullable=False)  # LINE 使用者 ID
    nickname = Column(String(100), nullable=False)  # 玩家暱稱
    wind_position = Column(String(10), nullable=True)  # 風位：東、南、西、北
    is_dealer = Column(String(10), default="no")  # 是否為莊家：yes, no
    seat_number = Column(Integer, nullable=True)  # 座位號碼 1-4
    score = Column(Integer, default=0)  # 目前分數
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Player(id={self.id}, nickname={self.nickname}, wind_position={self.wind_position})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "line_user_id": self.line_user_id,
            "nickname": self.nickname,
            "wind_position": self.wind_position,
            "is_dealer": self.is_dealer,
            "seat_number": self.seat_number,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }