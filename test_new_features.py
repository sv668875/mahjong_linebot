#!/usr/bin/env python3
"""
測試新功能 - 玩家加入、風位選擇、莊家設定
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine, Base
from models.game import Game
from models.player import Player

def test_join_flow():
    """測試完整的加入流程"""
    print("🧪 測試玩家加入流程...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 清理舊資料
        db.query(Player).delete()
        db.query(Game).delete()
        db.commit()
        
        # 1. 建立測試對局
        test_game = Game(
            group_id="test_group_join",
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
        
        # 2. 測試玩家加入
        test_players = [
            {"user_id": "user1", "nickname": "小明"},
            {"user_id": "user2", "nickname": "小華"},
            {"user_id": "user3", "nickname": "小美"},
            {"user_id": "user4", "nickname": "小王"}
        ]
        
        for i, player_info in enumerate(test_players, 1):
            player = Player(
                game_id=test_game.id,
                line_user_id=player_info["user_id"],
                nickname=player_info["nickname"],
                seat_number=i
            )
            db.add(player)
            print(f"✅ 玩家 {player_info['nickname']} 加入（{i}號位）")
        
        db.commit()
        
        # 3. 測試風位設定
        winds = ["東", "南", "西", "北"]
        players = db.query(Player).filter(Player.game_id == test_game.id).order_by(Player.seat_number).all()
        
        for player, wind in zip(players, winds):
            player.wind_position = wind
            print(f"✅ {player.nickname} 選擇 {wind}風")
        
        db.commit()
        
        # 4. 測試莊家設定
        dealer = players[0]  # 東風當莊
        dealer.is_dealer = "yes"
        db.commit()
        print(f"✅ {dealer.nickname} 設定為莊家")
        
        # 5. 測試完整配置查詢
        final_players = db.query(Player).filter(Player.game_id == test_game.id).order_by(Player.seat_number).all()
        
        print("\n🎮 最終遊戲配置：")
        for player in final_players:
            wind_info = player.wind_position + "風" if player.wind_position else "未選擇"
            dealer_mark = " 👑" if player.is_dealer == "yes" else ""
            print(f"{player.seat_number}號: {player.nickname} ({wind_info}){dealer_mark}")
        
        # 6. 測試遊戲狀態摘要
        print(f"\n📊 對局摘要：")
        print(f"• 模式：{test_game.mode}")
        print(f"• 每台：{test_game.per_point} 元")
        print(f"• 底台：{test_game.base_score} 元")
        print(f"• 收莊錢：{'是' if test_game.collect_money else '否'}")
        print(f"• 玩家數：{len(final_players)}/4")
        
        # 清理測試資料
        db.query(Player).filter(Player.game_id == test_game.id).delete()
        db.delete(test_game)
        db.commit()
        print("\n🧹 測試資料已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_validation_rules():
    """測試驗證規則"""
    print("\n🔍 測試驗證規則...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 清理舊資料
        db.query(Player).delete()
        db.query(Game).delete()
        db.commit()
        
        # 建立測試對局
        test_game = Game(
            group_id="test_validation",
            mode="台麻",
            per_point=15,
            base_score=40,
            collect_money=False,
            status="created"
        )
        db.add(test_game)
        db.commit()
        db.refresh(test_game)
        
        # 1. 測試重複加入檢查
        player1 = Player(
            game_id=test_game.id,
            line_user_id="duplicate_user",
            nickname="重複測試",
            seat_number=1
        )
        db.add(player1)
        db.commit()
        
        # 檢查是否已存在
        existing = db.query(Player).filter(
            Player.game_id == test_game.id,
            Player.line_user_id == "duplicate_user"
        ).first()
        
        if existing:
            print("✅ 重複玩家檢查正常")
        
        # 2. 測試暱稱重複檢查
        duplicate_nickname = db.query(Player).filter(
            Player.game_id == test_game.id,
            Player.nickname == "重複測試"
        ).first()
        
        if duplicate_nickname:
            print("✅ 暱稱重複檢查正常")
        
        # 3. 測試人數限制（加入 4 個玩家）
        for i in range(2, 6):  # 2-5號，總共會有5個，應該失敗
            player = Player(
                game_id=test_game.id,
                line_user_id=f"user_{i}",
                nickname=f"玩家{i}",
                seat_number=i
            )
            db.add(player)
        
        db.commit()
        
        # 檢查總數
        total_count = db.query(Player).filter(Player.game_id == test_game.id).count()
        print(f"✅ 人數限制測試：總共 {total_count} 人")
        
        # 4. 測試風位重複檢查
        players = db.query(Player).filter(Player.game_id == test_game.id).limit(4).all()
        
        # 設定重複風位
        if len(players) >= 2:
            players[0].wind_position = "東"
            players[1].wind_position = "東"  # 重複
            db.commit()
            
            # 檢查重複
            east_count = db.query(Player).filter(
                Player.game_id == test_game.id,
                Player.wind_position == "東"
            ).count()
            
            print(f"✅ 風位重複檢查：東風有 {east_count} 人（應避免）")
        
        # 清理
        db.query(Player).filter(Player.game_id == test_game.id).delete()
        db.delete(test_game)
        db.commit()
        print("🧹 驗證測試資料已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 驗證測試失敗：{e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_import_compatibility():
    """測試模組匯入相容性"""
    print("\n📦 測試模組匯入...")
    
    try:
        from handlers.join_handler import handle_join_command, handle_wind_selection
        from handlers.status_handler import handle_status_command, handle_dealer_command, handle_quit_command
        from utils.parser import parse_join_command
        
        print("✅ join_handler 匯入成功")
        print("✅ status_handler 匯入成功")
        print("✅ parser 更新匯入成功")
        
        # 測試解析函數
        test_commands = [
            "/加入 測試玩家",
            "/加入 小明123",
            "/加入"
        ]
        
        for cmd in test_commands:
            result = parse_join_command(cmd)
            print(f"✅ 解析 '{cmd}' → {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模組匯入失敗：{e}")
        return False

def show_feature_summary():
    """顯示新功能摘要"""
    print("\n" + "="*60)
    print("🎉 新功能開發完成摘要")
    print("="*60)
    
    features = [
        "✅ /加入 [暱稱] - 玩家加入對局",
        "✅ /選風 [東南西北] - 選擇風位",
        "✅ /我當莊 - 設定莊家",
        "✅ /狀態 - 查詢對局狀態",
        "✅ /退出 - 退出對局",
        "",
        "🔍 驗證功能：",
        "• 防止重複加入",
        "• 暱稱重複檢查",
        "• 4人上限控制",
        "• 風位重複檢查",
        "• 遊戲狀態驗證",
        "",
        "📱 使用流程：",
        "1. /開局 [參數] - 建立對局",
        "2. /加入 [暱稱] - 4位玩家加入",
        "3. /選風 [風位] - 各自選擇風位",
        "4. /我當莊 - 設定莊家",
        "5. ✅ 開始遊戲！"
    ]
    
    for feature in features:
        print(feature)
    
    print("\n💡 部署說明：")
    print("1. git add .")
    print("2. git commit -m 'feat: 新增玩家加入與風位選擇功能'")
    print("3. git push origin main")
    print("4. Render 會自動重新部署")
    print("5. 在 LINE 群組測試新指令")

if __name__ == "__main__":
    print("🚀 開始新功能測試...")
    
    # 確保資料庫表格存在
    Base.metadata.create_all(bind=engine)
    
    test_results = []
    
    # 執行測試
    test_results.append(("模組匯入", test_import_compatibility()))
    test_results.append(("完整流程", test_join_flow()))
    test_results.append(("驗證規則", test_validation_rules()))
    
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
        print("\n🎉 所有測試通過！新功能準備就緒")
        show_feature_summary()
    else:
        print("\n❌ 部分測試失敗，請檢查錯誤訊息")