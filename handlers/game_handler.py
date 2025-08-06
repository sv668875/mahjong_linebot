"""
遊戲指令處理器 - 處理 /開局 指令
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.game import Game
from utils.parser import parse_game_command, validate_game_params
from services.line_api import send_text_message

# 建立資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def handle_game_command(event, line_bot_api, command_text, group_id):
    """
    處理 /開局 指令
    
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
    
    # 解析指令參數
    try:
        params = parse_game_command(command_text)
        
        # 驗證參數
        errors = validate_game_params(params)
        if errors:
            error_message = "❌ 參數錯誤：\n" + "\n".join(f"• {error}" for error in errors)
            send_text_message(line_bot_api, event, error_message)
            return
            
    except Exception as e:
        send_text_message(line_bot_api, event, f"❌ 指令解析失敗：{str(e)}")
        return
    
    # 檢查群組是否已有進行中的對局
    db = SessionLocal()
    try:
        existing_game = db.query(Game).filter(
            Game.group_id == group_id,
            Game.status.in_(["created", "playing"])
        ).first()
        
        if existing_game:
            send_text_message(
                line_bot_api, 
                event, 
                f"❌ 此群組已有進行中的對局（ID: {existing_game.id}）\n請先完成當前對局或使用 /結束對局 指令"
            )
            return
        
        # 建立新對局
        new_game = Game(
            group_id=group_id,
            mode=params["mode"],
            per_point=params["per_point"],
            base_score=params["base_score"],
            collect_money=params["collect_money"],
            status="created"
        )
        
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        
        # 發送成功訊息
        success_message = new_game.get_summary_text()
        send_text_message(line_bot_api, event, success_message)
        
    except Exception as e:
        db.rollback()
        send_text_message(line_bot_api, event, f"❌ 建立對局失敗：{str(e)}")
    finally:
        db.close()