# RSS订阅推送机器人

一个Python脚本，用于定时抓取RSS订阅源内容，并将更新推送至Telegram频道。

## 功能特性

- ✅ 支持多个RSS订阅源管理
- ✅ 自动检测重复内容，避免重复推送
- ✅ 时区转换（UTC+8）
- ✅ 完善的错误处理和日志记录
- ✅ 可配置抓取时间间隔
- ✅ 支持Markdown格式消息推送
- ✅ 状态持久化存储

## 安装

1. 克隆或下载本项目
2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 复制环境变量模板：
```bash
cp .env.example .env
```

4. 编辑 `.env` 文件，填入你的Telegram Bot信息：
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## 配置

编辑 `rss_config.json` 文件来管理RSS订阅源：

```json
{
  "feeds": [
    {
      "name": "知乎每日精选",
      "url": "https://www.zhihu.com/rss",
      "enabled": true
    },
    {
      "name": "V2EX",
      "url": "https://www.v2ex.com/index.xml",
      "enabled": true
    }
  ],
  "check_interval": 300
}
```

### 配置说明

- `feeds`: RSS订阅源列表
  - `name`: 订阅源名称
  - `url`: RSS订阅地址
  - `enabled`: 是否启用该订阅源
- `check_interval`: 检查间隔时间（秒），默认300秒（5分钟）

## 使用方法

### Windows

- **持续运行模式**: 双击 `run.bat`
- **单次检查模式**: 双击 `run_once.bat`

### 命令行

```bash
# 持续运行模式
python rss_bot.py

# 单次检查模式
python rss_bot.py once
```

## 文件说明

- `rss_bot.py`: 主程序文件
- `rss_config.json`: RSS订阅源配置文件
- `.env`: 环境变量文件（包含Telegram Bot信息）
- `.env.example`: 环境变量模板
- `rss_state.json`: 状态文件（自动生成，记录已处理的项目）
- `rss_bot.log`: 日志文件（自动生成）
- `requirements.txt`: Python依赖包列表

## 获取Telegram Bot信息

1. **获取Bot Token**: 
   - 在Telegram中搜索 @BotFather
   - 使用 `/newbot` 命令创建新机器人
   - 复制生成的Token

2. **获取Chat ID**:
   - 将机器人添加到目标频道并设为管理员
   - 或者向机器人发送消息，访问: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

## 消息格式

推送到Telegram的消息格式如下：

```
📰 文章标题

文章摘要内容...

🔗 [阅读原文](文章链接)
📍 来源: RSS源名称
🕐 发布时间: 2024-01-01 12:00:00 (UTC+8)
```

## 高级配置

### 代理设置

如果需要使用代理访问Telegram API，在 `.env` 文件中添加：
```
HTTP_PROXY=http://127.0.0.1:7890
```

**注意**: 程序使用Python标准库`urllib`进行HTTP请求，代理配置更稳定可靠。

### 日志级别

修改 `.env` 文件中的日志级别：
```
LOG_LEVEL=DEBUG  # 可选: DEBUG, INFO, WARNING, ERROR
```

## 注意事项

1. **API限制**: 为避免触发Telegram API限制，消息发送间隔为1秒
2. **状态管理**: 程序会自动管理已处理的项目，最多保留1000条记录
3. **错误处理**: 网络错误会自动重试，RSS解析错误会记录但不会中断程序
4. **时区处理**: 所有时间都会转换为UTC+8时区显示
5. **连接方式**: 使用Python标准库`urllib`进行HTTP请求，无需额外依赖，代理配置更稳定

## 故障排除

### 常见问题

1. **无法连接到Telegram API**
   - 检查网络连接
   - 确认Bot Token是否正确
   - 检查是否需要设置代理
   - 程序使用`urllib`标准库，代理配置更稳定

2. **RSS源解析失败**
   - 检查RSS链接是否有效
   - 确认RSS格式是否正确
   - 查看日志文件获取详细信息

3. **消息发送失败**
   - 检查Chat ID是否正确
   - 确认机器人是否有发送消息权限
   - 检查是否被Telegram限制

## 更新日志

- v1.0.1: 优化连接方式，使用Python标准库`urllib`替代`aiohttp`，提升代理稳定性
- v1.0.0: 初始版本，支持基本RSS抓取和推送功能

## 许可证

MIT License