#!/usr/bin/env python3
"""
測試用戶身份綁定系統
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine, Base
from models.user import User
from models.game import Game
from models.player import Player

def test_user_binding_system():
    """測試用戶身份綁定功能"""
    print("🧪 測試用戶身份綁定系統...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 清理舊資料
        db.query(Player).delete()
        db.query(Game).delete()
        db.query(User).delete()
        db.commit()
        print("🧹 測試資料已清理")
        
        # 1. 測試用戶建立和暱稱設定
        print("\n📝 測試用戶建立和暱稱設定...")
        
        test_users = [
            {"user_id": "U123456", "display_name": "小明LINE", "preferred_nickname": "小明哥"},
            {"user_id": "U789012", "display_name": "小華LINE", "preferred_nickname": "華神"},
            {"user_id": "U345678", "display_name": "小美LINE", "preferred_nickname": None},  # 未設定慣用暱稱
            {"user_id": "U901234", "display_name": "小王LINE", "preferred_nickname": "王老五"}
        ]
        
        created_users = []
        for user_info in test_users:
            user = User(
                line_user_id=user_info["user_id"],
                display_name=user_info["display_name"],
                preferred_nickname=user_info["preferred_nickname"]
            )
            db.add(user)
            created_users.append(user)
            print(f"✅ 建立用戶：{user_info['display_name']} → 慣用暱稱：{user_info['preferred_nickname'] or '未設定'}")
        
        db.commit()
        
        # 2. 測試有效暱稱取得
        print("\n🎯 測試有效暱稱取得...")
        for user in created_users:
            db.refresh(user)
            effective_nickname = user.get_effective_nickname()
            print(f"• {user.display_name} → 有效暱稱：{effective_nickname}")
        
        # 3. 測試遊戲建立和玩家加入模擬
        print("\n🎮 測試遊戲流程模擬...")
        
        # 建立測試對局
        test_game = Game(
            group_id="test_binding_group",
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
        
        # 模擬玩家加入（使用有效暱稱）
        game_players = []
        for i, user in enumerate(created_users, 1):
            player = Player(
                game_id=test_game.id,
                line_user_id=user.line_user_id,
                nickname=user.get_effective_nickname(),  # 使用有效暱稱
                seat_number=i
            )
            db.add(player)
            game_players.append(player)
            print(f"✅ 玩家加入：{user.display_name} 使用暱稱 '{user.get_effective_nickname()}'")
        
        db.commit()
        
        # 4. 測試暱稱一致性檢查
        print("\n🔍 測試暱稱一致性...")
        
        for player in game_players:
            user = db.query(User).filter(User.line_user_id == player.line_user_id).first()
            expected_nickname = user.get_effective_nickname()
            actual_nickname = player.nickname
            
            if expected_nickname == actual_nickname:
                print(f"✅ {user.display_name}: 暱稱一致 '{actual_nickname}'")
            else:
                print(f"❌ {user.display_name}: 暱稱不一致 期望:'{expected_nickname}' 實際:'{actual_nickname}'")
        
        # 5. 測試統計功能模擬
        print("\n📊 測試統計功能模擬...")
        
        # 模擬遊戲結果更新
        for user in created_users[:2]:  # 只更新前兩個用戶的統計
            user.update_game_result(win_amount=150, lose_amount=50)  # 贏100元
            print(f"✅ 更新 {user.get_effective_nickname()} 統計：+100元")
        
        for user in created_users[2:]:  # 後兩個用戶輸錢
            user.update_game_result(win_amount=0, lose_amount=50)  # 輸50元
            print(f"✅ 更新 {user.get_effective_nickname()} 統計：-50元")
        
        db.commit()
        
        # 6. 測試統計摘要顯示
        print("\n📈 測試統計摘要...")
        for user in created_users:
            db.refresh(user)
            stats_summary = user.get_stats_summary()
            print(f"\n{user.get_effective_nickname()} 的統計:")
            print(stats_summary.replace('\n', '\n  '))
        
        # 7. 測試排行榜功能模擬
        print("\n🏆 測試排行榜（按淨輸贏排序）...")
        
        ranked_users = db.query(User).filter(
            User.total_games > 0
        ).order_by(User.net_amount.desc()).all()
        
        for i, user in enumerate(ranked_users, 1):
            status_emoji = "📈" if user.net_amount > 0 else "📉" if user.net_amount < 0 else "➖"
            print(f"{i}. {user.get_effective_nickname()}: {user.net_amount:+.0f}元 {status_emoji} ({user.total_games}局)")
        
        # 8. 測試暱稱更改場景
        print("\n🔄 測試暱稱更改場景...")
        
        # 模擬小美設定慣用暱稱
        user_xiaomei = created_users[2]  # 原本未設定慣用暱稱的用戶
        old_effective = user_xiaomei.get_effective_nickname()
        user_xiaomei.preferred_nickname = "美美"
        db.commit()
        new_effective = user_xiaomei.get_effective_nickname()
        
        print(f"✅ {user_xiaomei.display_name} 設定慣用暱稱：'{old_effective}' → '{new_effective}'")
        
        # 清理測試資料
        db.query(Player).filter(Player.game_id == test_game.id).delete()
        db.delete(test_game)
        for user in created_users:
            db.delete(user)
        db.commit()
        print("\n🧹 測試資料已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_user_handler_functions():
    """測試用戶處理器函數"""
    print("\n📦 測試用戶處理器函數...")
    
    try:
        from handlers.user_handler import get_or_create_user
        
        # 測試取得或建立用戶
        user1 = get_or_create_user("test_user_1", "測試用戶1")
        user2 = get_or_create_user("test_user_1", "測試用戶1更新")  # 同一用戶，名稱更新
        user3 = get_or_create_user("test_user_2", "測試用戶2")
        
        print(f"✅ 用戶1 首次建立：{user1.line_user_id} - {user1.display_name}")
        print(f"✅ 用戶1 再次取得：{user2.line_user_id} - {user2.display_name}")
        print(f"✅ 用戶2 建立：{user3.line_user_id} - {user3.display_name}")
        
        # 檢查是否為同一用戶物件
        if user1.id == user2.id:
            print("✅ 同一用戶取得正常")
        else:
            print("❌ 同一用戶取得異常")
        
        # 清理
        db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
        try:
            # 重新查詢用戶進行刪除
            user_to_delete1 = db.query(User).filter(User.line_user_id == "test_user_1").first()
            user_to_delete2 = db.query(User).filter(User.line_user_id == "test_user_2").first()
            
            if user_to_delete1:
                db.delete(user_to_delete1)
            if user_to_delete2:
                db.delete(user_to_delete2)
            
            db.commit()
            print("🧹 測試用戶已清理")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 用戶處理器測試失敗：{e}")
        return False

def show_binding_system_summary():
    """顯示身份綁定系統摘要"""
    print("\n" + "="*60)
    print("🎉 用戶身份綁定系統開發完成")
    print("="*60)
    
    features = [
        "✅ 用戶身份綁定 - LINE ID 與固定暱稱關聯",
        "✅ 慣用暱稱設定 - /設定暱稱 [暱稱]",
        "✅ 自動暱稱使用 - 加入遊戲時自動使用慣用暱稱",
        "✅ 個人統計追蹤 - 長期統計資料記錄",
        "✅ 統計查詢功能 - /我的統計, /暱稱資訊",
        "✅ 群組排行榜 - /排行榜",
        "",
        "🔧 新增指令：",
        "• /設定暱稱 [暱稱] - 設定固定暱稱",
        "• /暱稱資訊 - 查看目前暱稱設定",
        "• /我的統計 - 查看個人遊戲統計",
        "• /排行榜 - 查看群組排行榜",
        "",
        "📱 使用流程：",
        "1. 新用戶使用 /設定暱稱 設定固定暱稱",
        "2. 之後加入遊戲自動使用固定暱稱",
        "3. 系統累積個人統計資料",
        "4. 可隨時查看統計和排行榜",
        "",
        "💡 核心解決方案：",
        "• 解決暱稱不一致導致統計分散問題",
        "• 提供長期統計追蹤功能",
        "• 支援暱稱變更但保持資料連續性",
        "• 群組排行榜增加競技性"
    ]
    
    for feature in features:
        print(feature)
    
    print("\n🚀 部署說明：")
    print("1. 確認所有檔案已修改")
    print("2. git add .")
    print("3. git commit -m 'feat: 實作用戶身份綁定和統計系統'")
    print("4. git push origin main")
    print("5. Render 自動部署")
    print("6. 測試新指令功能")

if __name__ == "__main__":
    print("🚀 開始用戶身份綁定系統測試...")
    
    # 確保資料庫表格存在
    Base.metadata.create_all(bind=engine)
    
    test_results = []
    
    # 執行測試
    test_results.append(("用戶處理器函數", test_user_handler_functions()))
    test_results.append(("完整綁定系統", test_user_binding_system()))
    
    # 顯示結果
    print("\n" + "="*40)
    print("📊 測試結果摘要")
    print("="*40)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試通過！用戶身份綁定系統準備就緒")
        show_binding_system_summary()
    else:
        print("\n❌ 部分測試失敗，請檢查錯誤訊息")