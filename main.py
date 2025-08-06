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
    
    # TODO: 處理其他指令
    # elif text.startswith('/加入'):
    #     handle_join_command(event, line_bot_api, text, group_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)