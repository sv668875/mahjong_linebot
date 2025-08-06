"""
用戶管理處理器 - 處理用戶身份綁定和個人統計
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.user import User
from models.game import Game
from models.player import Player
from services.line_api import send_text_message

# 建立資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_or_create_user(line_user_id, display_name):
    """
    取得或建立用戶記錄
    
    Args:
        line_user_id: LINE 使用者 ID
        display_name: LINE 顯示名稱
        
    Returns:
        User: 用戶物件
    """
    db = SessionLocal()
    try:
        # 查找現有用戶
        user = db.query(User).filter(User.line_user_id == line_user_id).first()
        
        if not user:
            # 建立新用戶
            user = User(
                line_user_id=line_user_id,
                display_name=display_name,
                preferred_nickname=None  # 初始沒有設定慣用暱稱
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # 更新顯示名稱（以防用戶在 LINE 上更改了名稱）
            if user.display_name != display_name:
                user.display_name = display_name
                db.commit()
        
        return user
    finally:
        db.close()

def handle_set_nickname_command(event, line_bot_api, command_text):
    """
    處理 /設定暱稱 指令
    
    Args:
        event: LINE 事件物件
        line_bot_api: LINE Bot API 實例
        command_text: 完整指令文字
    """
    
    user_id = event.source.user_id
    
    # 解析暱稱
    nickname = command_text.replace('/設定暱稱', '').strip()
    
    if not nickname:
        send_text_message(
            line_bot_api, 
            event, 
            "❌ 請提供要設定的暱稱\n使用方式：/設定暱稱 你想要的暱稱"
        )
        return
    
    # 驗證暱稱長度
    if len(nickname) > 20:
        send_text_message(line_bot_api, event, "❌ 暱稱長度不能超過 20 個字")
        return
    
    # 清理暱稱（移除特殊字符）
    import re
    clean_nickname = re.sub(r'[^\w\u4e00-\u9fff\s]', '', nickname).strip()
    
    if not clean_nickname:
        send_text_message(line_bot_api, event, "❌ 暱稱不能只包含特殊字符")
        return
    
    db = SessionLocal()
    try:
        # 取得用戶資料
        user = db.query(User).filter(User.line_user_id == user_id).first()
        
        if not user:
            # 如果用戶不存在，需要先取得 LINE 顯示名稱
            try:
                profile = line_bot_api.get_profile(user_id)
                display_name = profile.display_name
            except:
                display_name = "LINE用戶"
            
            user = User(
                line_user_id=user_id,
                display_name=display_name,
                preferred_nickname=clean_nickname
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            success_message = f"""✅ 暱稱設定成功！

👤 你的暱稱：{clean_nickname}
📝 LINE名稱：{display_name}

💡 往後加入遊戲時會自動使用此暱稱"""
            
        else:
            old_nickname = user.get_effective_nickname()
            user.preferred_nickname = clean_nickname
            db.commit()
            
            success_message = f"""✅ 暱稱更新成功！

👤 新暱稱：{clean_nickname}
🔄 舊暱稱：{old_nickname}

💡 往後加入遊戲時會自動使用新暱稱"""
        
        send_text_message(line_bot_api, event, success_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 設定暱稱失敗：{str(e)}")
    finally:
        db.close()

def handle_my_stats_command(event, line_bot_api):
    """
    處理 /我的統計 指令
    """
    
    user_id = event.source.user_id
    
    db = SessionLocal()
    try:
        # 查找用戶
        user = db.query(User).filter(User.line_user_id == user_id).first()
        
        if not user:
            send_text_message(
                line_bot_api, 
                event, 
                """❌ 找不到你的記錄

💡 請先使用以下指令設定暱稱：
/設定暱稱 你的暱稱

設定後參與遊戲，系統就會開始記錄你的統計資料了！"""
            )
            return
        
        # 取得詳細統計
        stats_message = user.get_stats_summary()
        
        # 如果有參與過遊戲，顯示額外資訊
        if user.total_games > 0:
            # 查詢最近的遊戲記錄
            recent_games = db.query(Player).filter(
                Player.line_user_id == user_id
            ).join(Game).order_by(Game.created_at.desc()).limit(3).all()
            
            if recent_games:
                stats_message += "\n\n📅 最近 3 局："
                for i, player in enumerate(recent_games, 1):
                    game = db.query(Game).filter(Game.id == player.game_id).first()
                    if game:
                        date_str = game.created_at.strftime("%m/%d") if game.created_at else "未知"
                        dealer_mark = "👑" if player.is_dealer == "yes" else ""
                        wind_info = f"({player.wind_position}風)" if player.wind_position else ""
                        stats_message += f"\n{i}. {date_str} {game.mode} {wind_info}{dealer_mark}"
        
        send_text_message(line_bot_api, event, stats_message)
        
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 查詢統計失敗：{str(e)}")
    finally:
        db.close()

def handle_nickname_info_command(event, line_bot_api):
    """
    處理 /暱稱資訊 指令 - 顯示目前設定的暱稱
    """
    
    user_id = event.source.user_id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.line_user_id == user_id).first()
        
        if not user:
            # 如果沒有記錄，嘗試取得 LINE 資訊
            try:
                profile = line_bot_api.get_profile(user_id)
                display_name = profile.display_name
                
                info_message = f"""📋 你的暱稱資訊

📝 LINE名稱：{display_name}
👤 設定暱稱：尚未設定

💡 使用 `/設定暱稱 你的暱稱` 來設定固定暱稱
設定後加入遊戲時會自動使用，方便長期統計記錄！"""
                
            except:
                info_message = """❌ 無法取得你的資料

💡 請先使用 `/設定暱稱 你的暱稱` 設定暱稱"""
        else:
            info_message = f"""📋 你的暱稱資訊

📝 LINE名稱：{user.display_name}
👤 設定暱稱：{user.preferred_nickname or '尚未設定'}
🎮 目前使用：{user.get_effective_nickname()}
📊 參與對局：{user.total_games} 局

💡 使用 `/設定暱稱 新暱稱` 可以更新暱稱"""
        
        send_text_message(line_bot_api, event, info_message)
        
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 查詢暱稱資訊失敗：{str(e)}")
    finally:
        db.close()

def handle_top_players_command(event, line_bot_api, group_id):
    """
    處理 /排行榜 指令 - 顯示群組內玩家排行
    """
    
    db = SessionLocal()
    try:
        # 查詢在此群組有記錄的所有用戶
        # 透過 Player 表格找出曾經在此群組遊戲的用戶
        group_players = db.query(User.line_user_id).join(
            Player, User.line_user_id == Player.line_user_id
        ).join(
            Game, Player.game_id == Game.id
        ).filter(
            Game.group_id == group_id
        ).distinct().subquery()
        
        # 取得這些用戶的統計資料，按淨贏取金額排序
        top_users = db.query(User).filter(
            User.line_user_id.in_(group_players)
        ).filter(
            User.total_games > 0
        ).order_by(User.net_amount.desc()).limit(10).all()
        
        if not top_users:
            send_text_message(
                line_bot_api, 
                event, 
                """📊 此群組尚無排行榜記錄

💡 當群組成員設定暱稱並參與遊戲後，
就會開始累積記錄並顯示排行榜了！"""
            )
            return
        
        ranking_message = "🏆 群組排行榜（按淨輸贏）\n\n"
        
        for i, user in enumerate(top_users, 1):
            status_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            amount_emoji = "📈" if user.net_amount > 0 else "📉" if user.net_amount < 0 else "➖"
            
            ranking_message += f"{status_emoji} {i}. {user.get_effective_nickname()}\n"
            ranking_message += f"   💰 {user.net_amount:+.0f}元 {amount_emoji} ({user.total_games}局)\n\n"
        
        ranking_message += "💡 排行榜僅包含使用機器人記錄的對局"
        
        send_text_message(line_bot_api, event, ranking_message)
        
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 查詢排行榜失敗：{str(e)}")
    finally:
        db.close()