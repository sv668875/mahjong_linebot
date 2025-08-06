"""
對局狀態查詢和莊家設定處理器
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.game import Game
from models.player import Player
from services.line_api import send_text_message

# 建立資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def handle_status_command(event, line_bot_api, group_id):
    """
    處理 /狀態 指令 - 顯示當前對局狀態
    """
    
    if not group_id:
        send_text_message(line_bot_api, event, "❌ 此功能僅限群組使用")
        return
    
    db = SessionLocal()
    try:
        # 檢查是否有進行中的對局
        current_game = db.query(Game).filter(
            Game.group_id == group_id,
            Game.status.in_(["created", "playing"])
        ).first()
        
        if not current_game:
            send_text_message(
                line_bot_api, 
                event, 
                "❌ 目前沒有進行中的對局\n💡 使用 `/開局` 指令開始新對局"
            )
            return
        
        # 取得所有玩家
        players = db.query(Player).filter(
            Player.game_id == current_game.id
        ).order_by(Player.seat_number).all()
        
        # 生成狀態訊息
        status_message = f"""📊 對局狀態

🀄 遊戲模式：{current_game.mode}
💰 每台：{current_game.per_point} 元
📉 底台：{current_game.base_score} 元
🏯 收莊錢：{'是' if current_game.collect_money else '否'}
👥 人數：{len(players)}/4 人

"""
        
        if players:
            status_message += "📋 玩家列表：\n"
            for player in players:
                wind_info = f" ({player.wind_position}風)" if player.wind_position else ""
                dealer_info = " 👑莊家" if player.is_dealer == "yes" else ""
                status_message += f"{player.seat_number}號: {player.nickname}{wind_info}{dealer_info}\n"
            
            # 檢查遊戲進度
            if len(players) < 4:
                status_message += f"\n⏳ 等待玩家加入（還需 {4 - len(players)} 人）"
            elif not all(p.wind_position for p in players):
                unassigned = [p.nickname for p in players if not p.wind_position]
                status_message += f"\n🎲 等待選擇風位：{', '.join(unassigned)}"
            elif not any(p.is_dealer == "yes" for p in players):
                status_message += "\n👑 等待設定莊家（輸入 `/我當莊`）"
            else:
                status_message += "\n✅ 準備完成，可以開始遊戲！"
        else:
            status_message += "📝 尚無玩家加入\n💡 使用 `/加入 暱稱` 指令加入遊戲"
        
        send_text_message(line_bot_api, event, status_message)
        
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 查詢狀態失敗：{str(e)}")
    finally:
        db.close()

def handle_dealer_command(event, line_bot_api, group_id):
    """
    處理 /我當莊 指令 - 設定莊家
    """
    
    if not group_id:
        send_text_message(line_bot_api, event, "❌ 此功能僅限群組使用")
        return
    
    user_id = event.source.user_id
    
    db = SessionLocal()
    try:
        # 檢查是否有進行中的對局
        current_game = db.query(Game).filter(
            Game.group_id == group_id,
            Game.status.in_(["created", "playing"])
        ).first()
        
        if not current_game:
            send_text_message(line_bot_api, event, "❌ 目前沒有進行中的對局")
            return
        
        # 檢查玩家是否已加入
        player = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.line_user_id == user_id
        ).first()
        
        if not player:
            send_text_message(line_bot_api, event, "❌ 你尚未加入此局遊戲")
            return
        
        # 檢查是否已有莊家
        current_dealer = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.is_dealer == "yes"
        ).first()
        
        if current_dealer:
            if current_dealer.line_user_id == user_id:
                send_text_message(line_bot_api, event, "✅ 你已經是莊家了！")
            else:
                send_text_message(
                    line_bot_api, 
                    event, 
                    f"❌ 「{current_dealer.nickname}」已經是莊家"
                )
            return
        
        # 檢查是否所有玩家都已選擇風位
        total_players = db.query(Player).filter(Player.game_id == current_game.id).count()
        players_with_wind = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.wind_position.isnot(None)
        ).count()
        
        if total_players < 4 or players_with_wind < 4:
            send_text_message(
                line_bot_api, 
                event, 
                "❌ 請等待所有玩家加入並選擇風位後再設定莊家"
            )
            return
        
        # 設定莊家
        player.is_dealer = "yes"
        db.commit()
        
        # 取得完整遊戲配置
        all_players = db.query(Player).filter(
            Player.game_id == current_game.id
        ).order_by(Player.seat_number).all()
        
        # 生成最終配置訊息
        player_info = []
        for p in all_players:
            wind_info = p.wind_position + "風" if p.wind_position else "未選擇"
            dealer_mark = " 👑" if p.is_dealer == "yes" else ""
            player_info.append(f"{p.seat_number}號: {p.nickname} ({wind_info}){dealer_mark}")
        
        final_message = f"""🎉 遊戲設定完成！

👑 莊家：{player.nickname}

🎮 最終配置：
{chr(10).join(player_info)}

🀄 遊戲規則：
• 模式：{current_game.mode}
• 每台：{current_game.per_point} 元
• 底台：{current_game.base_score} 元
• 收莊錢：{'是' if current_game.collect_money else '否'}

✅ 準備開始遊戲！
📝 可以開始記錄每一手的輸贏了"""
        
        # 更新遊戲狀態為進行中
        current_game.status = "playing"
        db.commit()
        
        send_text_message(line_bot_api, event, final_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 設定莊家失敗：{str(e)}")
    finally:
        db.close()

def handle_quit_command(event, line_bot_api, group_id):
    """
    處理 /退出 指令 - 玩家退出對局
    """
    
    if not group_id:
        send_text_message(line_bot_api, event, "❌ 此功能僅限群組使用")
        return
    
    user_id = event.source.user_id
    
    db = SessionLocal()
    try:
        # 檢查是否有進行中的對局
        current_game = db.query(Game).filter(
            Game.group_id == group_id,
            Game.status.in_(["created", "playing"])
        ).first()
        
        if not current_game:
            send_text_message(line_bot_api, event, "❌ 目前沒有進行中的對局")
            return
        
        # 檢查玩家是否已加入
        player = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.line_user_id == user_id
        ).first()
        
        if not player:
            send_text_message(line_bot_api, event, "❌ 你尚未加入此局遊戲")
            return
        
        # 如果遊戲已開始，不允許退出
        if current_game.status == "playing":
            send_text_message(
                line_bot_api, 
                event, 
                "❌ 遊戲已開始，無法退出\n💡 請等待本局結束或聯繫群組管理員"
            )
            return
        
        nickname = player.nickname
        
        # 刪除玩家
        db.delete(player)
        db.commit()
        
        # 重新編號剩餘玩家的座位
        remaining_players = db.query(Player).filter(
            Player.game_id == current_game.id
        ).order_by(Player.seat_number).all()
        
        for i, p in enumerate(remaining_players, 1):
            p.seat_number = i
        
        db.commit()
        
        remaining_count = len(remaining_players)
        
        quit_message = f"""✅ 「{nickname}」已退出遊戲

👥 剩餘玩家：{remaining_count}/4 人"""
        
        if remaining_players:
            player_list = "\n".join([f"{p.seat_number}號: {p.nickname}" for p in remaining_players])
            quit_message += f"\n\n📋 目前玩家：\n{player_list}"
            
            if remaining_count < 4:
                quit_message += f"\n\n⏳ 還需 {4 - remaining_count} 位玩家加入"
        else:
            quit_message += "\n\n📝 目前無玩家，等待新玩家加入..."
        
        send_text_message(line_bot_api, event, quit_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 退出失敗：{str(e)}")
    finally:
        db.close()