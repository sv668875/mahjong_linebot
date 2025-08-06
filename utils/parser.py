"""
指令參數解析工具
"""
import re

def parse_game_command(command_text):
    """
    解析 /開局 指令參數
    
    輸入範例: "/開局 台麻 每台10 底30 收莊錢"
    輸出: {
        "mode": "台麻",
        "per_point": 10,
        "base_score": 30,
        "collect_money": True
    }
    """
    # 預設值
    params = {
        "mode": "台麻",
        "per_point": 10,
        "base_score": 30,
        "collect_money": True
    }
    
    # 移除 /開局 前綴並清理空白
    text = command_text.replace("/開局", "").strip()
    
    if not text:
        return params
    
    # 解析模式（台麻、港麻等）
    mode_match = re.search(r'(台麻|港麻|四川麻將|國標麻將)', text)
    if mode_match:
        params["mode"] = mode_match.group(1)
    
    # 解析每台金額
    per_point_match = re.search(r'每台(\d+)', text)
    if per_point_match:
        params["per_point"] = int(per_point_match.group(1))
    
    # 解析底台金額
    base_score_match = re.search(r'底(\d+)', text)
    if base_score_match:
        params["base_score"] = int(base_score_match.group(1))
    
    # 解析是否收莊錢
    if "不收莊錢" in text:
        params["collect_money"] = False
    elif "收莊錢" in text:
        params["collect_money"] = True
    
    return params

def validate_game_params(params):
    """
    驗證遊戲參數是否合理
    """
    errors = []
    
    # 檢查每台金額
    if params["per_point"] <= 0 or params["per_point"] > 1000:
        errors.append("每台金額必須在 1-1000 元之間")
    
    # 檢查底台金額
    if params["base_score"] <= 0 or params["base_score"] > 10000:
        errors.append("底台金額必須在 1-10000 元之間")
    
    # 檢查模式
    valid_modes = ["台麻", "港麻", "四川麻將", "國標麻將"]
    if params["mode"] not in valid_modes:
        errors.append(f"模式必須是以下之一：{', '.join(valid_modes)}")
    
    return errors

def parse_join_command(command_text):
    """
    解析 /加入 指令參數
    
    Args:
        command_text: 完整指令文字，例如 '/加入 小明' 或 '/加入'
        
    Returns:
        dict: 包含解析結果的字典
        {
            "nickname": str or None  # 暱稱（可選，系統會自動使用 LINE ID 綁定的名稱）
        }
        
    Examples:
        "/加入 小明" -> {"nickname": "小明"}
        "/加入" -> {"nickname": None}
        
    Note:
        系統使用 LINE ID 來綁定數據，暱稱參數是可選的：
        - 如果有設定慣用暱稱 → 自動使用慣用暱稱
        - 如果沒有設定慣用暱稱 → 自動使用 LINE 原本名字
        - 提供的暱稱參數會被系統邏輯覆蓋，並給予說明
    """
    text = command_text.replace("/加入", "").strip()
    
    if not text:
        return {"nickname": None}
    
    # 移除可能的特殊字符，只保留中文、英文、數字
    nickname = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    
    if len(nickname) > 20:
        nickname = nickname[:20]
    
    return {"nickname": nickname if nickname else None}