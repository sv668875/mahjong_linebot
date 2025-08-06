"""
玩家加入指令處理器 - 處理 /加入 指令
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.game import Game
from models.player import Player
from models.user import User
from handlers.user_handler import get_or_create_user
from utils.parser import parse_join_command
from services.line_api import send_text_message, send_message_with_quick_reply, create_wind_position_quick_reply

# 建立資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def handle_join_command(event, line_bot_api, command_text, group_id):
    """
    處理 /加入 指令
    
    Args:
        event: LINE 事件物件
        line_bot_api: LINE Bot API 實例
        command_text: 完整指令文字
        group_id: LINE 群組 ID
    """
    
    # 檢查是否在群組中使用
    if not group_id:
        send_text_message(line_bot_api, event, "❌ 此功能僅限群組使用")
        return
    
    # 取得使用者 ID
    user_id = event.source.user_id
    
    # 取得 LINE 顯示名稱
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = "LINE用戶"
    
    # 取得或建立用戶記錄
    user = get_or_create_user(user_id, display_name)
    
    # 解析指令參數
    try:
        params = parse_join_command(command_text)
        provided_nickname = params.get("nickname")
        
        # 決定要使用的暱稱邏輯：
        # 1. 如果有設定慣用暱稱 → 使用慣用暱稱
        # 2. 如果沒有設定慣用暱稱 → 使用 LINE 原本名字
        # 3. 如果提供了暱稱參數 → 忽略，統一使用上述邏輯
        
        if user.preferred_nickname:
            # 使用已設定的慣用暱稱
            nickname = user.preferred_nickname
            nickname_source = "慣用暱稱"
        else:
            # 使用 LINE 原本的顯示名稱
            nickname = user.display_name
            nickname_source = "LINE名稱"
        
        # 如果用戶有提供暱稱參數，給予說明
        if provided_nickname and provided_nickname != nickname:
            send_text_message(
                line_bot_api, 
                event, 
                f"""💡 系統自動使用你的{nickname_source}：{nickname}

📝 你輸入的暱稱：{provided_nickname}
🎯 實際使用的暱稱：{nickname}

💡 說明：
• 系統使用 LINE ID 來綁定數據
• 如果你有設定慣用暱稱會優先使用
• 沒有設定則使用你的 LINE 原本名字
• 如需設定固定暱稱，請使用：/設定暱稱 新暱稱"""
            )
            
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 指令解析失敗：{str(e)}")
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
                "❌ 目前沒有進行中的對局，請先使用 `/開局` 指令建立對局"
            )
            return
        
        # 檢查玩家是否已經加入
        existing_player = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.line_user_id == user_id
        ).first()
        
        if existing_player:
            send_text_message(
                line_bot_api, 
                event, 
                f"❌ 你已經加入此局遊戲了！\n🎯 你的暱稱：{existing_player.nickname}"
            )
            return
        
        # 檢查是否已滿 4 人
        player_count = db.query(Player).filter(Player.game_id == current_game.id).count()
        
        if player_count >= 4:
            send_text_message(
                line_bot_api, 
                event, 
                "❌ 此局已滿 4 位玩家，無法再加入"
            )
            return
        
        # 檢查暱稱是否重複
        duplicate_nickname = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.nickname == nickname
        ).first()
        
        if duplicate_nickname:
            send_text_message(
                line_bot_api, 
                event, 
                f"❌ 暱稱「{nickname}」已被使用，請選擇其他暱稱"
            )
            return
        
        # 建立新玩家
        new_player = Player(
            game_id=current_game.id,
            line_user_id=user_id,
            nickname=nickname,
            seat_number=player_count + 1
        )
        
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        
        # 重新計算目前玩家數
        updated_player_count = db.query(Player).filter(Player.game_id == current_game.id).count()
        
        # 產生成功訊息
        success_message = f"""✅ 加入成功！

🎯 玩家：{nickname} ({nickname_source})
🎲 座位：{new_player.seat_number} 號
👥 目前人數：{updated_player_count}/4 人

"""
        
        # 如果是使用 LINE 名稱，提醒可以設定慣用暱稱
        if nickname_source == "LINE名稱":
            success_message += "💡 如需設定固定暱稱，可使用 /設定暱稱 新暱稱\n\n"
        
        # 如果滿 4 人，提示可以選擇風位
        if updated_player_count == 4:
            # 取得所有玩家資訊
            all_players = db.query(Player).filter(Player.game_id == current_game.id).order_by(Player.seat_number).all()
            player_list = "\n".join([f"{p.seat_number}號: {p.nickname}" for p in all_players])
            
            success_message += f"""🎉 人數已滿，可以開始遊戲！

👥 玩家名單：
{player_list}

請各位玩家選擇風位："""
            
            # 發送帶有風位選擇按鈕的訊息
            wind_buttons = create_wind_position_quick_reply()
            send_message_with_quick_reply(line_bot_api, event, success_message, wind_buttons)
        else:
            # 顯示目前玩家列表
            current_players = db.query(Player).filter(Player.game_id == current_game.id).order_by(Player.seat_number).all()
            player_list = "\n".join([f"{p.seat_number}號: {p.nickname}" for p in current_players])
            
            success_message += f"""👥 目前玩家：
{player_list}

等待其他玩家加入...（還需 {4 - updated_player_count} 人）"""
            
            send_text_message(line_bot_api, event, success_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 加入失敗：{str(e)}")
    finally:
        db.close()

def handle_wind_selection(event, line_bot_api, wind, group_id):
    """
    處理風位選擇
    
    Args:
        event: LINE 事件物件
        line_bot_api: LINE Bot API 實例
        wind: 選擇的風位（東、南、西、北）
        group_id: LINE 群組 ID
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
        
        # 檢查風位是否已被選擇
        existing_wind = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.wind_position == wind
        ).first()
        
        if existing_wind:
            send_text_message(
                line_bot_api, 
                event, 
                f"❌ {wind}風已被「{existing_wind.nickname}」選擇"
            )
            return
        
        # 更新玩家風位
        player.wind_position = wind
        db.commit()
        
        # 檢查是否所有玩家都已選擇風位
        players_with_wind = db.query(Player).filter(
            Player.game_id == current_game.id,
            Player.wind_position.isnot(None)
        ).count()
        
        total_players = db.query(Player).filter(Player.game_id == current_game.id).count()
        
        success_message = f"✅ {player.nickname} 選擇了 {wind}風！"
        
        if players_with_wind == total_players and total_players == 4:
            # 所有人都選完風位，顯示完整配置
            all_players = db.query(Player).filter(Player.game_id == current_game.id).order_by(Player.seat_number).all()
            wind_assignment = "\n".join([f"{p.wind_position}風: {p.nickname}" for p in all_players if p.wind_position])
            
            success_message += f"""

🎉 風位選擇完成！

🀀🀁🀂🀃 風位配置：
{wind_assignment}

請東風玩家輸入 `/我當莊` 開始第一局，或其他玩家可輸入 `/我當莊` 擔任莊家"""
            
        else:
            remaining = 4 - players_with_wind
            success_message += f"\n還需 {remaining} 位玩家選擇風位"
            
        send_text_message(line_bot_api, event, success_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 風位選擇失敗：{str(e)}")
    finally:
        db.close()