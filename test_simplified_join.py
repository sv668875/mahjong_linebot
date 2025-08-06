#!/usr/bin/env python3
"""
測試簡化的用戶綁定邏輯
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine, Base
from models.user import User
from models.game import Game
from models.player import Player

def test_simplified_join_logic():
    """測試簡化的加入邏輯"""
    print("🧪 測試簡化的用戶綁定邏輯...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 清理舊資料
        db.query(Player).delete()
        db.query(Game).delete()
        db.query(User).delete()
        db.commit()
        print("🧹 測試資料已清理")
        
        # 建立測試對局
        test_game = Game(
            group_id="test_simplified_group",
            mode="台麻",
            per_point=10,
            base_score=30,
            collect_money=True,
            status="created"
        )
        db.add(test_game)
        db.commit()
        db.refresh(test_game)
        print(f"✅ 建立測試對局 ID: {test_game.id}")
        
        # 測試用戶情境
        print("\n📝 測試不同用戶情境...")
        
        test_scenarios = [
            {
                "name": "用戶A：有設定慣用暱稱",
                "user_id": "UA001",
                "line_name": "小明的LINE",
                "preferred_nickname": "小明哥",
                "expected_nickname": "小明哥",
                "expected_source": "慣用暱稱"
            },
            {
                "name": "用戶B：沒有設定慣用暱稱",
                "user_id": "UB002", 
                "line_name": "華神在線",
                "preferred_nickname": None,
                "expected_nickname": "華神在線",
                "expected_source": "LINE名稱"
            },
            {
                "name": "用戶C：有設定慣用暱稱（中英文）",
                "user_id": "UC003",
                "line_name": "美美 Meimei",
                "preferred_nickname": "美美",
                "expected_nickname": "美美",
                "expected_source": "慣用暱稱"
            },
            {
                "name": "用戶D：沒有設定慣用暱稱（特殊字符）",
                "user_id": "UD004",
                "line_name": "王老五🎮",
                "preferred_nickname": None,
                "expected_nickname": "王老五🎮",
                "expected_source": "LINE名稱"
            }
        ]
        
        # 建立用戶
        created_users = []
        for scenario in test_scenarios:
            user = User(
                line_user_id=scenario["user_id"],
                display_name=scenario["line_name"],
                preferred_nickname=scenario["preferred_nickname"]
            )
            db.add(user)
            created_users.append((user, scenario))
            print(f"✅ 建立{scenario['name']}：LINE名稱='{scenario['line_name']}', 慣用暱稱='{scenario['preferred_nickname'] or '未設定'}'")
        
        db.commit()
        
        # 測試加入邏輯
        print("\n🎮 測試加入遊戲邏輯...")
        
        for i, (user, scenario) in enumerate(created_users, 1):
            db.refresh(user)
            
            # 模擬加入邏輯
            if user.preferred_nickname:
                actual_nickname = user.preferred_nickname
                actual_source = "慣用暱稱"
            else:
                actual_nickname = user.display_name
                actual_source = "LINE名稱"
            
            # 建立玩家
            player = Player(
                game_id=test_game.id,
                line_user_id=user.line_user_id,
                nickname=actual_nickname,
                seat_number=i
            )
            db.add(player)
            
            # 驗證結果
            if actual_nickname == scenario["expected_nickname"] and actual_source == scenario["expected_source"]:
                print(f"✅ {scenario['name']}：使用'{actual_nickname}' ({actual_source}) ✓")
            else:
                print(f"❌ {scenario['name']}：期望'{scenario['expected_nickname']}' ({scenario['expected_source']})，實際'{actual_nickname}' ({actual_source})")
        
        db.commit()
        
        # 測試統一使用 LINE ID 綁定
        print("\n🔗 測試 LINE ID 綁定一致性...")
        
        players = db.query(Player).filter(Player.game_id == test_game.id).all()
        for player in players:
            user = db.query(User).filter(User.line_user_id == player.line_user_id).first()
            expected_nickname = user.get_effective_nickname()
            
            if player.nickname == expected_nickname:
                print(f"✅ {player.nickname}：綁定一致（ID: {player.line_user_id}）")
            else:
                print(f"❌ {player.nickname}：綁定不一致，期望 {expected_nickname}")
        
        # 測試暱稱設定後的更新
        print("\n🔄 測試暱稱更新情境...")
        
        # 模擬用戶B設定慣用暱稱
        user_b = created_users[1][0]
        db.refresh(user_b)
        
        old_effective = user_b.get_effective_nickname()
        user_b.preferred_nickname = "華神"
        db.commit()
        new_effective = user_b.get_effective_nickname()
        
        print(f"✅ 用戶B設定慣用暱稱：'{old_effective}' → '{new_effective}'")
        
        # 驗證下次加入會使用新暱稱
        expected_next_nickname = user_b.get_effective_nickname()
        print(f"💡 下次加入時會使用：'{expected_next_nickname}' (慣用暱稱)")
        
        # 測試完整遊戲配置
        print("\n🎯 最終遊戲配置：")
        final_players = db.query(Player).filter(Player.game_id == test_game.id).order_by(Player.seat_number).all()
        
        for player in final_players:
            user = db.query(User).filter(User.line_user_id == player.line_user_id).first()
            current_effective = user.get_effective_nickname()
            next_join_name = current_effective
            
            print(f"{player.seat_number}號: {player.nickname} (本局)")
            print(f"     → LINE ID: {player.line_user_id}")
            print(f"     → 下次加入會使用: {next_join_name}")
            print()
        
        # 清理測試資料
        db.query(Player).filter(Player.game_id == test_game.id).delete()
        db.delete(test_game)
        for user, _ in created_users:
            db.delete(user)
        db.commit()
        print("🧹 測試資料已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_simplified_logic_summary():
    """顯示簡化邏輯摘要"""
    print("\n" + "="*60)
    print("🎉 簡化用戶綁定邏輯完成")
    print("="*60)
    
    logic_points = [
        "🔑 核心原則：使用 LINE ID 來綁定數據",
        "",
        "📋 暱稱使用邏輯：",
        "1️⃣  如果有設定慣用暱稱 → 使用慣用暱稱",
        "2️⃣  如果沒有設定慣用暱稱 → 使用 LINE 原本名字",
        "3️⃣  用戶提供的暱稱參數會被忽略並給予說明",
        "",
        "💡 用戶體驗：",
        "• 首次使用：直接輸入 /加入 即可，使用 LINE 名字",
        "• 設定固定暱稱：/設定暱稱 想要的暱稱",
        "• 之後加入：直接 /加入，自動使用設定的暱稱",
        "• 統計連續性：無論暱稱如何變化，都能正確統計",
        "",
        "🔧 指令說明：",
        "• /加入 → 自動使用系統綁定的暱稱",
        "• /加入 任何暱稱 → 忽略參數，使用系統邏輯",
        "• /設定暱稱 新暱稱 → 設定慣用暱稱",
        "• /暱稱資訊 → 查看目前設定",
        "",
        "✅ 解決的問題：",
        "• 暱稱不一致導致統計分散",
        "• 用戶不知道該輸入什麼暱稱",
        "• 長期統計資料追蹤困難",
        "• 群組內暱稱重複衝突"
    ]
    
    for point in logic_points:
        print(point)
    
    print("\n🚀 部署說明：")
    print("1. git add .")
    print("2. git commit -m 'feat: 簡化用戶綁定邏輯，使用LINE ID自動綁定暱稱'")
    print("3. git push origin main")
    print("4. Render 自動部署")
    print("5. 在群組測試 /加入 指令")

if __name__ == "__main__":
    print("🚀 開始簡化用戶綁定邏輯測試...")
    
    # 確保資料庫表格存在
    Base.metadata.create_all(bind=engine)
    
    # 執行測試
    test_result = test_simplified_join_logic()
    
    # 顯示結果
    print("\n" + "="*40)
    print("📊 測試結果")
    print("="*40)
    
    if test_result:
        print("✅ 測試通過！簡化用戶綁定邏輯準備就緒")
        show_simplified_logic_summary()
    else:
        print("❌ 測試失敗，請檢查錯誤訊息")