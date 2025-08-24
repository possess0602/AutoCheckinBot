# 自動打卡機器人

智能化自動打卡系統，支援隨機時間打卡、JWT 認證管理和服務化運行。

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置設定檔

首次使用需要配置 `config.json`：

```bash
# 複製範例設定檔
cp config.example.json config.json
```

編輯 `config.json` 並設定：
- `module_session_cookie`: 從瀏覽器複製 `__ModuleSessionCookie` 值
- `work_schedule`: 自訂上下班時間範圍
- `service_settings`: 調整服務參數

### 3. 更新 Cookie（舊方法，仍可使用）

```bash
# 更新 Cookie（互動式指引）
python manual_punch.py update
```

按照指引從瀏覽器複製 `__ModuleSessionCookie` 值。

### 4. 測試打卡

```bash
# 上班打卡
python manual_punch.py checkin

# 下班打卡  
python manual_punch.py checkout

# 檢查 JWT token 狀態
python manual_punch.py analyze
```

### 5. 啟動自動服務

```bash
# 啟動後台服務
./start_service.sh

# 檢查服務狀態
./status_service.sh

# 停止服務
./stop_service.sh
```

## 🏗️ 系統架構

### 核心模組

1. **`attendance_service.py`** - 自動打卡服務
   - 可設定的隨機時間排程
   - JWT token 過期監控
   - 自動重試機制
   - 信號處理（SIGTERM, SIGHUP）

2. **`manual_punch.py`** - 手動打卡工具
   - JWT token 解析和過期檢查
   - Cookie 自動刷新
   - 互動式 Cookie 更新
   - 設定檔支援

3. **設定檔案**
   - `config.json` - 主要設定檔（包含敏感資訊）
   - `config.example.json` - 設定檔範例
   - `cookies.json` - Cookie 儲存檔（自動生成）

4. **服務管理腳本**
   - `start_service.sh` - 啟動服務
   - `stop_service.sh` - 停止服務  
   - `status_service.sh` - 狀態檢查
   - `check_cookies.sh` - Cookie 健康檢查

### API 請求結構

- **URL**: `https://apollo.mayohr.com/backend/pt/api/checkIn/punch/web`
- **方法**: POST
- **認證**: JWT Bearer Token (透過 Cookie)
- **請求體**: 
  ```json
  {
    "AttendanceType": 1,    // 1=上班, 2=下班
    "IsOverride": false
  }
  ```

## ⚙️ 設定檔配置

### 設定檔結構
```json
{
  "authentication": {
    "module_session_cookie": "YOUR_JWT_TOKEN_HERE"
  },
  "work_schedule": {
    "punch_in": {
      "hour": 9,
      "minute_range": {"min": 10, "max": 20}
    },
    "punch_out": {
      "hour": 18,
      "minute_range": {"min": 10, "max": 30}
    },
    "work_duration_hours": 9
  },
  "service_settings": {
    "max_retries": 2,
    "timeout_seconds": 30,
    "check_interval_seconds": 30,
    "workdays": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  }
}
```

### 隨機化策略
- **上班時間**: 可設定時間範圍內隨機（預設 09:10-09:20）
- **下班時間**: 可設定時間範圍內隨機（預設 18:10-18:30）
- **工作日**: 可自訂工作日
- **工作時數**: 可設定每日工作時間

### 重新載入配置
```bash
# 不停機重新載入排程
kill -HUP <PID>
```

## 🔐 認證機制

### JWT Token 管理
系統使用 JWT token 進行認證，自動處理：
- Token 過期檢查
- 自動重試機制
- 失敗計數器
- 異常警報

### Cookie 結構
關鍵 Cookie 參數：
- `__ModuleSessionCookie`: JWT authentication token
- `visid_incap_*`: 安全驗證 cookies
- 其他 session 相關 cookies

## 📊 監控與日誌

### 日誌系統
- **控制台輸出**: 即時狀態顯示
- **檔案日誌**: `logs/attendance_service.log`
- **Cookie 警報**: `logs/cookie_alert.txt`

### 健康檢查
```bash
# Cookie 健康狀態檢查
./check_cookies.sh

# 服務詳細狀態
./status_service.sh
```

## 🛠️ 手動操作

### 命令列用法
```bash
# 打卡操作
python manual_punch.py checkin     # 上班打卡
python manual_punch.py checkout    # 下班打卡
python manual_punch.py 1           # 上班打卡 (數字版)
python manual_punch.py 2           # 下班打卡 (數字版)

# Cookie 管理
python manual_punch.py update      # 更新 Cookie
python manual_punch.py analyze     # 分析 JWT token

# 服務管理
./start_service.sh                 # 啟動服務
./stop_service.sh                  # 停止服務
./status_service.sh                # 檢查狀態
./check_cookies.sh                 # 檢查 Cookie
```

## 🚨 故障排除

### Cookie 過期處理
當出現認證失敗時：

1. **自動檢測**: 系統會自動檢測 JWT token 過期
2. **更新設定檔**: 
   ```bash
   # 方法1: 編輯設定檔
   nano config.json
   
   # 方法2: 使用互動式工具
   python manual_punch.py update
   ```
3. **重啟服務**: 
   ```bash
   ./stop_service.sh && ./start_service.sh
   ```

### 獲取新 Cookie 步驟
1. 開啟瀏覽器登入 `apollo.mayohr.com`
2. 按 F12 開啟開發者工具
3. 前往 Application → Cookies → apollo.mayohr.com
4. 複製 `__ModuleSessionCookie` 的值
5. 更新到 `config.json` 中的 `module_session_cookie` 欄位

### 常見問題

| 錯誤類型 | 解決方案 |
|----------|----------|
| JWT token 過期 | 更新 `config.json` 或執行 `python manual_punch.py update` |
| 設定檔案遺失 | 複製 `config.example.json` 到 `config.json` |
| 網路連線問題 | 檢查網路，系統會自動重試 |
| 服務無回應 | 使用 `./stop_service.sh` 強制停止後重啟 |
| PID 檔案錯誤 | 刪除 `attendance_service.pid` 檔案 |

## 📋 系統需求

- **Python**: 3.6+
- **套件**: requests, schedule
- **平台**: Windows/Linux 相容
- **網路**: 穩定的網際網路連線 