"""
LINE API 服務封裝
"""
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

def send_text_message(line_bot_api, event, text):
    """發送純文字訊息"""
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )

def send_message_with_quick_reply(line_bot_api, event, text, quick_reply_items):
    """
    發送帶有快速回覆按鈕的訊息
    
    quick_reply_items: [{"label": "按鈕文字", "text": "回傳文字"}, ...]
    """
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=item["label"], text=item["text"]))
        for item in quick_reply_items
    ]
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=text,
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

def create_wind_position_quick_reply():
    """建立風位選擇的快速回覆按鈕"""
    return [
        {"label": "🀀 東", "text": "/選風 東"},
        {"label": "🀁 南", "text": "/選風 南"},
        {"label": "🀂 西", "text": "/選風 西"},
        {"label": "🀃 北", "text": "/選風 北"}
    ]

def create_dealer_quick_reply():
    """建立莊家選擇的快速回覆按鈕"""
    return [
        {"label": "🎯 我當莊", "text": "/我當莊"}
    ]