"""
LINE 麻將記帳機器人 - FastAPI 主程式
"""
import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from dotenv import load_dotenv

from models.database import engine, Base
from handlers.game_handler import handle_game_command
from handlers.join_handler import handle_join_command, handle_wind_selection
from handlers.status_handler import handle_status_command, handle_dealer_command, handle_quit_command
from handlers.user_handler import handle_set_nickname_command, handle_my_stats_command, handle_nickname_info_command, handle_top_players_command

# 載入環境變數
load_dotenv()

app = FastAPI(title="LINE 麻將記帳機器人", version="1.0.0")

# LINE Bot 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 建立資料庫表格
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "LINE 麻將記帳機器人運行中", "status": "active"}

@app.post("/webhook")
async def webhook_callback(request: Request):
    """LINE Webhook 回調端點"""
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理 LINE 訊息事件"""
    text = event.message.text.strip()
    group_id = event.source.group_id if hasattr(event.source, 'group_id') else None
    
    # 處理開局指令
    if text.startswith('/開局'):
        handle_game_command(event, line_bot_api, text, group_id)
    
    # 處理加入指令
    elif text.startswith('/加入'):
        handle_join_command(event, line_bot_api, text, group_id)
    
    # 處理風位選擇指令
    elif text.startswith('/選風'):
        wind = text.replace('/選風', '').strip()
        if wind in ['東', '南', '西', '北']:
            handle_wind_selection(event, line_bot_api, wind, group_id)
        else:
            from services.line_api import send_text_message
            send_text_message(line_bot_api, event, "❌ 請選擇正確的風位：東、南、西、北")
    
    # 處理狀態查詢指令
    elif text in ['/狀態', '/status', '/查詢']:
        handle_status_command(event, line_bot_api, group_id)
    
    # 處理莊家設定指令
    elif text in ['/我當莊', '/當莊']:
        handle_dealer_command(event, line_bot_api, group_id)
    
    # 處理退出指令
    elif text in ['/退出', '/離開']:
        handle_quit_command(event, line_bot_api, group_id)
    
    # 處理用戶身份綁定指令
    elif text.startswith('/設定暱稱'):
        handle_set_nickname_command(event, line_bot_api, text)
    
    # 處理個人統計查詢指令
    elif text in ['/我的統計', '/統計', '/個人記錄']:
        handle_my_stats_command(event, line_bot_api)
    
    # 處理暱稱資訊查詢指令
    elif text in ['/暱稱資訊', '/我的暱稱']:
        handle_nickname_info_command(event, line_bot_api)
    
    # 處理群組排行榜指令
    elif text in ['/排行榜', '/排行']:
        handle_top_players_command(event, line_bot_api, group_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)