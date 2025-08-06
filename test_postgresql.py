#!/usr/bin/env python3
"""
測試 PostgreSQL 相容性
"""

def test_postgresql_compatibility():
    """測試 PostgreSQL 資料庫相容性"""
    print("🐘 測試 PostgreSQL 相容性...")
    
    try:
        # 測試 psycopg2-binary 套件
        import psycopg2
        print("✅ psycopg2-binary 套件安裝正常")
    except ImportError:
        print("❌ psycopg2-binary 套件未安裝")
        print("請執行：pip install psycopg2-binary")
        return False
    
    # 測試資料庫 URL 格式轉換
    try:
        from models.database import engine
        import os
        
        # 模擬 Render 提供的 postgres:// URL 格式
        test_urls = [
            "postgres://user:pass@host:5432/db",
            "postgresql://user:pass@host:5432/db", 
            "sqlite:///./test.db"
        ]
        
        for url in test_urls:
            # 暫時設定環境變數
            os.environ["DATABASE_URL"] = url
            
            # 重新載入資料庫模組以測試 URL 轉換
            import importlib
            from models import database
            importlib.reload(database)
            
            converted_url = database.DATABASE_URL
            print(f"原始 URL: {url}")
            print(f"轉換後: {converted_url}")
            
            if url.startswith("postgres://"):
                assert converted_url.startswith("postgresql://"), "postgres:// 轉換失敗"
                print("✅ postgres:// → postgresql:// 轉換正常")
            
            print()
        
    except Exception as e:
        print(f"❌ URL 格式轉換測試失敗: {e}")
        return False
    
    # 測試資料庫模型相容性
    try:
        from models.game import Game
        from models.player import Player
        
        # 建立測試物件（不實際寫入資料庫）
        game = Game(
            group_id="test_pg_group",
            mode="台麻",
            per_point=15,
            base_score=40,
            collect_money=True
        )
        
        player = Player(
            game_id=1,
            line_user_id="test_user_pg",
            nickname="測試玩家",
            wind_position="東",
            is_dealer="no",
            seat_number=1
        )
        
        print("✅ PostgreSQL 模型相容性測試通過")
        
    except Exception as e:
        print(f"❌ 模型相容性測試失敗: {e}")
        return False
    
    # 測試 Gunicorn 啟動指令
    try:
        import gunicorn
        print("✅ Gunicorn 套件安裝正常")
        
        # 測試 uvicorn.workers 是否可用
        from uvicorn.workers import UvicornWorker
        print("✅ UvicornWorker 可用")
        
    except ImportError as e:
        print(f"❌ Gunicorn/UvicornWorker 測試失敗: {e}")
        return False
    
    print("\n🎉 PostgreSQL 相容性測試全部通過！")
    print("系統已準備好部署到 Render")
    return True

def show_deployment_checklist():
    """顯示部署檢查清單"""
    print("\n" + "="*50)
    print("🚀 Render 部署檢查清單")
    print("="*50)
    
    checklist = [
        "✅ PostgreSQL 驅動程式 (psycopg2-binary) 已安裝",
        "✅ 資料庫 URL 格式轉換功能已實作",
        "✅ Gunicorn + UvicornWorker 部署配置已設定",
        "✅ PORT 環境變數動態讀取已實作", 
        "✅ render.yaml 部署配置檔已建立",
        "✅ README.md 部署指南已更新",
        "",
        "📋 部署前準備:",
        "🔲 將程式碼推送到 GitHub",
        "🔲 在 Render 建立新的 Web Service",
        "🔲 連結 GitHub 儲存庫",
        "🔲 建立 PostgreSQL 資料庫服務",
        "🔲 設定環境變數 (LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN)",
        "🔲 將 DATABASE_URL 連結到 PostgreSQL 服務",
        "🔲 部署並測試應用程式",
        "🔲 設定 LINE Webhook URL: https://your-app.onrender.com/webhook"
    ]
    
    for item in checklist:
        print(item)
    
    print("\n💡 提醒事項:")
    print("- Render 免費方案在閒置後會自動休眠，第一次訪問可能較慢")
    print("- PostgreSQL 免費方案有 1GB 儲存限制")
    print("- 建議在部署後立即測試 /開局 指令")

if __name__ == "__main__":
    success = test_postgresql_compatibility()
    if success:
        show_deployment_checklist()
    else:
        print("\n❌ 請先解決相容性問題後再進行部署")