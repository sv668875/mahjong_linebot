"""
資料庫設定與連線
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 取得資料庫 URL，預設使用 SQLite，生產環境使用 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mahjong.db")

# Render 提供的 PostgreSQL URL 格式轉換
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 建立資料庫引擎
engine_args = {}
if "sqlite" in DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    # PostgreSQL 連線池設定，適用於 Render
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600
    })

engine = create_engine(DATABASE_URL, **engine_args)

# 建立會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別
Base = declarative_base()

def get_db():
    """取得資料庫連線"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()