# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.error
import asyncio
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("dotenv loaded successfully")
except ImportError:
    print("dotenv not available")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取环境变量
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HTTP_PROXY = os.getenv('HTTP_PROXY')

print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
print(f"HTTP_PROXY: {HTTP_PROXY}")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.error("错误：环境变量未正确设置")
    exit(1)

async def test_telegram_connection():
    """测试 Telegram Bot 连接"""
    try:
        # Telegram Bot API URL
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        
        # 代理配置
        proxy_url = HTTP_PROXY or "http://127.0.0.1:7890"
        
        # 创建代理处理器
        if HTTP_PROXY:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            logger.info(f"使用代理: {proxy_url}")
        else:
            opener = urllib.request.build_opener()
            logger.info("无代理设置，直接连接")
        
        # 测试获取 Bot 信息
        logger.info("=== 测试1: 获取Bot信息 ===")
        get_me_url = f"{api_url}/getMe"
        request = urllib.request.Request(get_me_url)
        
        with opener.open(request, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("ok"):
                    logger.info("✅ Bot连接成功!")
                    logger.info("Bot用户名: @{}".format(data["result"]["username"]))
                    logger.info("Bot名称: {}".format(data["result"]["first_name"]))
                else:
                    logger.error("❌ Bot API返回错误: {}".format(data))
                    return False
            else:
                logger.error("❌ HTTP请求失败，状态码: {}".format(response.status))
                return False
        
        # 测试发送消息到频道
        logger.info("\n=== 测试2: 发送测试消息 ===")
        test_message = f"🧪 RSS Bot测试消息\n\n"
        test_message += f"✅ 环境变量配置正确\n"
        test_message += f"📍 Chat ID: {TELEGRAM_CHAT_ID}\n"
        test_message += f"🤖 Bot Token已配置\n\n"
        test_message += "如果看到此消息，说明配置成功！"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": test_message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        send_message_url = f"{api_url}/sendMessage"
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(send_message_url, data=data)
        request.add_header('Content-Type', 'application/json')
        
        with opener.open(request, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("ok"):
                    logger.info("✅ 消息发送成功!")
                    message_id = result.get("result", {}).get("message_id")
                    logger.info("消息ID: {}".format(message_id))
                    return True
                else:
                    logger.error("❌ 发送消息失败: {}".format(result))
                    return False
            else:
                logger.error("❌ HTTP请求失败，状态码: {}".format(response.status))
                return False
                    
    except Exception as e:
        logger.error("❌ Telegram连接失败: {}".format(e))
        return False

async def main():
    """主测试函数"""
    logger.info("=== Telegram Bot测试工具 ===")
    logger.info("Token长度: {}".format(len(TELEGRAM_BOT_TOKEN)))
    logger.info("Chat ID: {}".format(TELEGRAM_CHAT_ID))
    logger.info("HTTP代理: {}".format(HTTP_PROXY if HTTP_PROXY else '无代理'))
    
    success = await test_telegram_connection()
    
    if success:
        logger.info("\n✅ Telegram连接测试完成!")
    else:
        logger.error("\n❌ Telegram连接测试失败!")

if __name__ == "__main__":
    asyncio.run(main())