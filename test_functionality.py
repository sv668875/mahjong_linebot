#!/usr/bin/env python3
"""
麻將記帳機器人功能測試腳本
"""

def test_basic_functionality():
    """測試基本功能"""
    print("🧪 開始進行功能測試...")
    
    # 測試 1: 模組匯入
    print("\n1. 測試模組匯入...")
    try:
        from models.database import engine, Base
        from models.game import Game
        from models.player import Player
        from handlers.game_handler import handle_game_command
        from utils.parser import parse_game_command, validate_game_params
        from services.line_api import send_text_message
        print("✅ 所有模組匯入成功")
    except Exception as e:
        print(f"❌ 模組匯入失敗: {e}")
        return False
    
    # 測試 2: 資料庫建立
    print("\n2. 測試資料庫建立...")
    try:
        Base.metadata.create_all(bind=engine)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = ['games', 'players']
        if all(table in tables for table in expected_tables):
            print(f"✅ 資料庫表格建立成功: {tables}")
        else:
            print(f"❌ 缺少必要表格。實際: {tables}, 預期: {expected_tables}")
            return False
    except Exception as e:
        print(f"❌ 資料庫建立失敗: {e}")
        return False
    
    # 測試 3: 指令解析
    print("\n3. 測試指令解析...")
    test_cases = [
        ("/開局", {"mode": "台麻", "per_point": 10, "base_score": 30, "collect_money": True}),
        ("/開局 每台20", {"mode": "台麻", "per_point": 20, "base_score": 30, "collect_money": True}),
        ("/開局 台麻 每台15 底50 不收莊錢", {"mode": "台麻", "per_point": 15, "base_score": 50, "collect_money": False}),
    ]
    
    for cmd, expected in test_cases:
        try:
            result = parse_game_command(cmd)
            errors = validate_game_params(result)
            if errors:
                print(f"❌ 參數驗證失敗: {cmd} -> {errors}")
                return False
            elif result == expected:
                print(f"✅ 解析正確: {cmd}")
            else:
                print(f"❌ 解析結果不符: {cmd}")
                print(f"   預期: {expected}")
                print(f"   實際: {result}")
                return False
        except Exception as e:
            print(f"❌ 指令解析失敗: {cmd} -> {e}")
            return False
    
    # 測試 4: Game 模型功能
    print("\n4. 測試 Game 模型...")
    try:
        game = Game(
            group_id="test_group_123",
            mode="台麻",
            per_point=15,
            base_score=40,
            collect_money=True
        )
        summary = game.get_summary_text()
        if "對局建立完成" in summary and "15 元" in summary and "40 元" in summary:
            print("✅ Game 模型功能正常")
        else:
            print(f"❌ Game 模型摘要文字異常: {summary}")
            return False
    except Exception as e:
        print(f"❌ Game 模型測試失敗: {e}")
        return False
    
    # 測試 5: 資料庫寫入讀取
    print("\n5. 測試資料庫操作...")
    try:
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        # 建立測試對局
        test_game = Game(
            group_id="test_db_group",
            mode="台麻",
            per_point=20,
            base_score=60,
            collect_money=False,
            status="created"
        )
        
        db.add(test_game)
        db.commit()
        db.refresh(test_game)
        
        # 讀取測試
        retrieved_game = db.query(Game).filter(Game.group_id == "test_db_group").first()
        if retrieved_game and retrieved_game.per_point == 20:
            print("✅ 資料庫讀寫操作正常")
            
            # 清理測試資料
            db.delete(retrieved_game)
            db.commit()
        else:
            print("❌ 資料庫讀取失敗")
            return False
            
        db.close()
        
    except Exception as e:
        print(f"❌ 資料庫操作失敗: {e}")
        return False
    
    print("\n🎉 所有測試通過！系統準備就緒")
    return True

def test_error_cases():
    """測試錯誤情況處理"""
    print("\n🛠️  測試錯誤處理...")
    
    # 測試無效參數
    try:
        from utils.parser import parse_game_command, validate_game_params
        
        # 測試無效金額
        invalid_params = {"mode": "台麻", "per_point": -10, "base_score": 30, "collect_money": True}
        errors = validate_game_params(invalid_params)
        if errors:
            print("✅ 無效參數驗證正常")
        else:
            print("❌ 無效參數未被捕捉")
            return False
            
        # 測試超大金額
        invalid_params2 = {"mode": "台麻", "per_point": 10000, "base_score": 30, "collect_money": True}
        errors2 = validate_game_params(invalid_params2)
        if errors2:
            print("✅ 超大金額驗證正常")
        else:
            print("❌ 超大金額未被捕捉")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")
        return False
        
    print("✅ 錯誤處理測試通過")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        success = test_error_cases()
    
    if success:
        print("\n" + "="*50)
        print("🚀 系統測試完成！可以開始使用")
        print("="*50)
        print()
        print("下一步：")
        print("1. 啟動服務：python3 -m uvicorn main:app --reload")
        print("2. 設定 LINE Webhook URL")
        print("3. 在 LINE 群組中測試 /開局 指令")
    else:
        print("\n" + "="*50)
        print("❌ 系統測試失敗，請檢查錯誤訊息")
        print("="*50)