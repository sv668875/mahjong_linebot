# 🀄 LINE 麻將記帳機器人

專為 LINE 群組設計的互動式麻將記帳機器人，支援開局、玩家管理、座位設定等功能。

## ✨ 功能特色

### 已完成功能（v1.0）
- ✅ `/開局` - 建立新對局，支援參數自訂
- ✅ 參數解析 - 智能解析遊戲設定
- ✅ 資料庫儲存 - SQLite/PostgreSQL 支援
- ✅ 群組管理 - 防止重複開局

### 計劃功能（v2.0）
- 🔄 `/加入` - 玩家加入對局
- 🔄 風位選擇 - 四風座位分配
- 🔄 莊家設定 - 首局莊家指定
- 🔄 記分系統 - 每手牌結算

## 🚀 快速開始

### 1. 安裝套件

```bash
pip install -r requirements.txt
```

### 2. 環境設定

複製 `.env.example` 為 `.env` 並填入你的 LINE Bot 資訊：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```env
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
DATABASE_URL=sqlite:///./mahjong.db
```

### 3. 啟動服務

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 設定 LINE Webhook

在 LINE Developers Console 設定 Webhook URL：
- 開發環境：`https://your-ngrok-url.com/webhook`
- 部署環境：`https://your-domain.com/webhook`

## 📱 使用方式

### 開局指令

在 LINE 群組中輸入：

```
/開局 台麻 每台10 底30 收莊錢
```

**支援參數：**
- **模式**：台麻、港麻、四川麻將、國標麻將
- **每台**：每台多少錢（預設10元）
- **底台**：底台金額（預設30元）  
- **收莊錢**：是否收莊錢（預設收）

**使用範例：**
```
/開局                    # 使用預設設定
/開局 每台20            # 每台20元
/開局 底50 不收莊錢      # 底台50元，不收莊錢
/開局 台麻 每台15 底40   # 完整設定
```

## 🏗️ 專案架構

```
mahjong_linebot/
├── main.py              # FastAPI 主程式
├── handlers/            # 指令處理器
│   └── game_handler.py  # 開局指令處理
├── models/             # 資料模型
│   ├── database.py     # 資料庫設定
│   ├── game.py         # 對局模型
│   └── player.py       # 玩家模型
├── services/           # 服務層
│   └── line_api.py     # LINE API 封裝
├── utils/              # 工具函數
│   └── parser.py       # 指令解析
└── requirements.txt    # 套件需求
```

## 🔧 部署指南

### 🌟 Render 部署（推薦）

1. **推送程式碼到 GitHub**
   ```bash
   git add .
   git commit -m "準備部署到 Render"
   git push origin main
   ```

2. **建立 Render 服務**
   - 註冊 [Render](https://render.com) 帳號
   - 選擇 "New" → "Web Service"
   - 連結 GitHub 並選擇此專案

3. **設定部署參數**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
   - **Python Version**: `3.9.6`

4. **建立 PostgreSQL 資料庫**
   - 在 Render Dashboard 點選 "New" → "PostgreSQL"
   - 資料庫名稱：`mahjong-postgres`
   - 計劃選擇：Free

5. **設定環境變數**
   ```
   LINE_CHANNEL_SECRET=你的_LINE_CHANNEL_SECRET
   LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_ACCESS_TOKEN
   DATABASE_URL=自動從PostgreSQL服務連結
   ```

6. **部署完成**
   - Render 會提供服務 URL：`https://your-app-name.onrender.com`
   - 將此 URL + `/webhook` 設定到 LINE Developer Console

### 🏠 本地測試

1. **使用 SQLite 本地開發**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **使用 ngrok 建立 webhook 轉發**
   ```bash
   ngrok http 8000
   ```

3. **測試 PostgreSQL 相容性**（可選）
   ```bash
   # 安裝 PostgreSQL 驅動
   pip install psycopg2-binary
   
   # 設定測試資料庫 URL
   export DATABASE_URL="postgresql://user:password@localhost:5432/testdb"
   python test_functionality.py
   ```

## 📊 資料庫結構

### games 表
- `id`: 對局ID
- `group_id`: LINE群組ID
- `mode`: 遊戲模式
- `per_point`: 每台金額
- `base_score`: 底台金額
- `collect_money`: 是否收莊錢
- `status`: 對局狀態

### players 表  
- `id`: 玩家ID
- `game_id`: 對局ID（外鍵）
- `line_user_id`: LINE使用者ID
- `nickname`: 玩家暱稱
- `wind_position`: 風位
- `is_dealer`: 是否為莊家

## 🤝 開發貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License