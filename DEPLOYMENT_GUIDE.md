# 🚀 Render 部署完整指南

## 📋 問題解決歷程

### 遇到的問題
1. **Python 3.13 相容性問題**
   - `'PyLongObject' has no member named 'ob_digit'`
   - `_PyLong_AsByteArray 呼叫參數不符`
   - `ma_version_tag is deprecated`

2. **套件相依性衝突**
   - `line-bot-sdk==3.12.0` 與 `aiohttp==3.9.1` 版本衝突
   - pip 無法解析相依性

### 解決方案
✅ **降級到 Python 3.11.9** - 最穩定的生產版本
✅ **使用 line-bot-sdk==3.5.0** - 經過測試的穩定版本
✅ **移除明確 aiohttp 版本** - 讓 line-bot-sdk 自行管理相依性

## 🔧 最終配置

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
line-bot-sdk==3.5.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
python-multipart==0.0.6
psycopg2-binary==2.9.9
gunicorn==21.2.0
```

### runtime.txt
```
python-3.11.9
```

### render.yaml
```yaml
services:
  - type: web
    name: mahjong-linebot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: LINE_CHANNEL_SECRET
        sync: false
      - key: LINE_CHANNEL_ACCESS_TOKEN  
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: mahjong-postgres
          property: connectionString
        
databases:
  - name: mahjong-postgres
    plan: free
    databaseName: mahjong_db
    user: mahjong_user
```

## 🌟 Render 部署步驟

### 1. 推送到 GitHub
```bash
git add .
git commit -m "fix: 解決 Python 3.13 與套件相依性問題"
git push origin main
```

### 2. 建立 Render 服務
1. 前往 [Render](https://render.com) 註冊並登入
2. 點選 "New" → "Web Service"
3. 連接 GitHub 並選擇此專案

### 3. 設定 Web Service
- **Name**: `mahjong-linebot`
- **Region**: Singapore (最接近台灣)
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
- **Plan**: `Free`

### 4. 建立 PostgreSQL 資料庫
1. 在 Render Dashboard 點選 "New" → "PostgreSQL"
2. **Name**: `mahjong-postgres`
3. **Database Name**: `mahjong_db`
4. **User**: `mahjong_user`
5. **Plan**: `Free`

### 5. 設定環境變數
在 Web Service 的 Environment 頁面設定：
```
LINE_CHANNEL_SECRET=你的LINE頻道密鑰
LINE_CHANNEL_ACCESS_TOKEN=你的LINE存取權杖
DATABASE_URL=連結到PostgreSQL服務
```

**連結資料庫**：
- 在 `DATABASE_URL` 設定中
- 選擇 "Connect to a database"
- 選擇剛建立的 `mahjong-postgres`

### 6. 部署並測試
1. Render 會自動開始部署
2. 等待部署完成（約 3-5 分鐘）
3. 訪問提供的 URL 測試：`https://your-app-name.onrender.com/`
4. 應該看到：`{"message": "LINE 麻將記帳機器人運行中", "status": "active"}`

### 7. 設定 LINE Webhook
1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Bot 頻道
3. 在 "Messaging API" 頁面設定：
   - **Webhook URL**: `https://your-app-name.onrender.com/webhook`
   - **Use webhook**: 開啟
   - **Verify** 按鈕測試連接

### 8. 測試機器人
在 LINE 群組中測試：
```
/開局
/開局 每台20
/開局 台麻 每台15 底40 收莊錢
```

## 🔍 故障排除

### 部署失敗
1. **檢查部署日誌**: Render Dashboard → Logs
2. **確認 Python 版本**: 必須是 3.11.9
3. **套件安裝錯誤**: 檢查 requirements.txt 語法

### Webhook 連接失敗
1. **URL 格式**: 確保是 `https://your-app.onrender.com/webhook`
2. **SSL 憑證**: Render 自動提供 HTTPS
3. **防火牆**: Render 無防火牆限制

### 機器人無回應
1. **檢查環境變數**: LINE_CHANNEL_SECRET 和 ACCESS_TOKEN
2. **資料庫連線**: 確認 DATABASE_URL 正確連結
3. **應用程式日誌**: 查看 Render 即時日誌

### 資料庫問題
1. **PostgreSQL 免費限制**: 1GB 儲存空間
2. **連線池**: 已設定適當的連線池參數
3. **SQL 語法**: PostgreSQL 與 SQLite 略有差異

## 💡 生產環境建議

### 安全性
- 使用環境變數儲存敏感資訊
- 定期更新套件版本
- 監控應用程式日誌

### 效能優化
- **Gunicorn workers**: 根據流量調整 worker 數量
- **PostgreSQL 索引**: 為常用查詢欄位建立索引
- **快取**: 考慮 Redis 快取熱門資料

### 監控
- **Render 內建監控**: 查看 CPU、記憶體使用量
- **應用程式日誌**: 定期檢查錯誤日誌
- **LINE Webhook 狀態**: 監控 webhook 成功率

## 📞 支援

### Render 免費方案限制
- **休眠時間**: 閒置 15 分鐘後自動休眠
- **喚醒時間**: 約 30-60 秒
- **使用量**: 每月 750 小時免費

### 常見問題
- **冷啟動慢**: 免費方案正常現象
- **資料庫連線中斷**: 設定了自動重連機制
- **套件更新**: 建議每月檢查更新

---

🎉 **恭喜！你的 LINE 麻將記帳機器人已成功部署到 Render 平台！**