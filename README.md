[README.md](https://github.com/user-attachments/files/30035397/README.md)
# Messenger - Android即时通讯应用

一个类似QQ的Android即时通讯应用，支持两部设备间实时通讯。

## 功能特性

- ✅ 文字消息实时收发
- ✅ 用户注册/登录
- ✅ 好友搜索与添加
- ✅ 在线状态显示
- ✅ 离线消息（上线后自动接收）
- ✅ 消息已读状态

## 项目结构

```
Messenger/
├── app/                          # Android客户端
│   └── src/main/java/com/example/messenger/
│       ├── data/
│       │   ├── model/            # 数据模型 (User, Message)
│       │   ├── database/         # Room数据库
│       │   ├── repository/       # 数据仓库
│       │   └── remote/           # WebSocket客户端
│       ├── ui/
│       │   ├── login/            # 登录/注册界面
│       │   ├── chat/             # 聊天界面
│       │   ├── contacts/         # 通讯录界面
│       │   ├── message/          # 消息列表
│       │   ├── profile/          # 个人中心
│       │   ├── navigation/       # 导航配置
│       │   └── theme/            # 主题样式
│       ├── di/                   # 依赖注入
│       ├── MainActivity.kt
│       └── MessengerApp.kt
├── server/                       # Python服务器
│   ├── server.py                 # WebSocket服务器
│   ├── requirements.txt          # Python依赖
│   ├── Dockerfile                # Docker配置
│   └── render.yaml               # Render部署配置
└── README.md
```

## 技术栈

### Android客户端
- **语言**: Kotlin
- **UI框架**: Jetpack Compose
- **架构**: MVVM + Repository
- **本地存储**: Room Database
- **依赖注入**: Hilt
- **网络通信**: OkHttp WebSocket

### 服务器
- **语言**: Python 3.11+
- **WebSocket**: websockets库
- **数据库**: SQLite (aiosqlite)

## 快速开始

### 1. 启动服务器（本地测试）

```bash
cd server
pip install -r requirements.txt
python server.py
```

服务器启动后监听 `ws://0.0.0.0:8765`

### 2. 构建Android应用

```bash
# 使用Gradle构建
./gradlew assembleDebug

# APK输出位置
app/build/outputs/apk/debug/app-debug.apk
```

### 3. 安装并运行

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 部署到公网

### 方案A: Railway部署（推荐）

1. **创建GitHub仓库**
   - 将 `server/` 目录上传到GitHub

2. **部署到Railway**
   - 访问 https://railway.com
   - 用GitHub账号登录
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择你的仓库

3. **获取公网地址**
   - 在Railway项目中点击服务
   - Settings → Networking → Generate Domain
   - 得到类似 `xxx.up.railway.app` 的地址

4. **在App中使用**
   - 输入 `wss://xxx.up.railway.app`
   - 点击"连接服务器"

### 方案B: Docker部署

```bash
cd server
docker build -t messenger-server .
docker run -p 8765:8765 messenger-server
```

### 方案C: 本地局域网

1. 确保设备在同一WiFi网络
2. 查看电脑IP: `ipconfig`
3. 在App中输入 `ws://你的IP:8765`

## 使用说明

### 注册账号
1. 打开App
2. 点击"没有账号？去注册"
3. 输入用户名、昵称、密码
4. 点击"注册"
5. 注册成功后自动跳转登录

### 登录
1. 输入用户名和密码
2. 点击"登录"

### 添加好友
1. 进入"通讯录"页面
2. 点击右上角搜索图标
3. 输入好友用户名
4. 点击搜索结果添加

### 发送消息
1. 在消息列表或通讯录中点击好友
2. 输入消息内容
3. 点击发送按钮

## API协议

### 消息格式 (JSON)

**注册**
```json
{
  "type": "register",
  "username": "user1",
  "nickname": "User One",
  "password": "123456"
}
```

**登录**
```json
{
  "type": "login",
  "username": "user1",
  "password": "123456"
}
```

**发送消息**
```json
{
  "type": "send_message",
  "sender_id": "user1_id",
  "receiver_id": "user2_id",
  "content": "Hello!"
}
```

**搜索用户**
```json
{
  "type": "search_users",
  "query": "user",
  "user_id": "current_user_id"
}
```

### 服务器响应

**登录成功**
```json
{
  "type": "login_result",
  "success": true,
  "user_id": "abc123",
  "username": "user1",
  "nickname": "User One"
}
```

**新消息**
```json
{
  "type": "new_message",
  "message": {
    "id": "msg123",
    "sender_id": "user1_id",
    "receiver_id": "user2_id",
    "content": "Hello!",
    "timestamp": 1689420000000
  }
}
```

**在线用户列表**
```json
{
  "type": "online_users",
  "user_ids": ["user1_id", "user2_id"]
}
```

## 常见问题

### Q: 连接服务器失败？
- 检查服务器是否运行
- 检查网络连接
- 确认服务器地址格式正确（`ws://` 或 `wss://`）

### Q: 注册后无法登录？
- 确认用户名和密码正确
- 检查服务器日志

### Q: 消息发送后对方收不到？
- 确认双方都已登录
- 检查对方是否在线
- 检查服务器日志

### Q: 如何查看服务器日志？
服务器会输出所有WebSocket连接和消息的详细日志。

## 开发说明

### 添加新功能

1. 在 `data/model/` 添加数据模型
2. 在 `data/database/` 添加DAO
3. 在 `data/repository/` 添加仓库方法
4. 在 `ui/` 添加界面和ViewModel
5. 在 `server/server.py` 添加服务器处理逻辑

### 修改服务器地址

编辑 `app/src/main/java/com/example/messenger/ui/login/LoginViewModel.kt`:
```kotlin
val serverIp = "你的服务器地址"
webSocketClient.connect("ws://$serverIp:8765")
```

## License

MIT License
