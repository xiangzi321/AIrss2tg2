#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS订阅抓取与Telegram推送机器人
定时抓取RSS订阅源内容并推送至Telegram频道
"""

import os
import json
import logging
import asyncio
import hashlib
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 常量配置
UTC_PLUS_8 = timezone(timedelta(hours=8))
STATE_FILE = "rss_state.json"
CONFIG_FILE = "rss_config.json"

@dataclass
class RSSItem:
    """RSS项目数据结构"""
    title: str
    link: str
    published: datetime
    summary: str
    source: str
    
    def to_hash(self) -> str:
        """生成项目哈希值用于重复检测"""
        content = f"{self.title}{self.link}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

class TelegramBot:
    """Telegram机器人类"""
    
    def __init__(self, token: str, chat_id: str, proxy_url: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id
        # self.proxy_url = proxy_url  # 注释掉代理设置
        self.proxy_url = None  # 强制不使用代理
        self.api_url = f"https://api.telegram.org/bot{token}"
        
    async def send_message(self, text: str, parse_mode: str = "Markdown", max_retries: int = 5) -> bool:
        """发送消息到Telegram频道，支持重试机制"""
        import urllib.request
        import urllib.error
        import json
        import time
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        
        for attempt in range(max_retries):
            try:
                # 配置代理 - 已注释掉代理功能
                # if self.proxy_url:
                #     proxy_handler = urllib.request.ProxyHandler({'http': self.proxy_url, 'https': self.proxy_url})
                #     opener = urllib.request.build_opener(proxy_handler)
                #     if attempt == 0:
                #         logger.info(f"使用代理: {self.proxy_url}")
                # else:
                opener = urllib.request.build_opener()
                if attempt == 0:
                    logger.info("无代理设置，直接连接")
                
                # 发送消息
                send_message_url = f"{self.api_url}/sendMessage"
                data = json.dumps(payload).encode('utf-8')
                request = urllib.request.Request(send_message_url, data=data)
                request.add_header('Content-Type', 'application/json')
                
                with opener.open(request, timeout=30) as response:
                    if response.status == 200:
                        result = json.loads(response.read().decode('utf-8'))
                        if result.get("ok"):
                            logger.info("消息发送成功")
                            return True
                        else:
                            logger.error(f"Telegram API错误: {result}")
                            if attempt < max_retries - 1:
                                wait_time = 2 ** attempt  # 指数退避：2^0, 2^1, 2^2, 2^3, 2^4
                                logger.info(f"第{attempt + 1}次发送失败，{wait_time}秒后重试...")
                                time.sleep(wait_time)
                                continue
                            return False
                    else:
                        logger.error(f"HTTP请求失败，状态码: {response.status}")
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.info(f"第{attempt + 1}次发送失败，{wait_time}秒后重试...")
                            time.sleep(wait_time)
                            continue
                        return False
                        
            except Exception as e:
                logger.error(f"发送Telegram消息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"发送消息失败，已达到最大重试次数 ({max_retries})")
                    return False
        
        return False

class RSSManager:
    """RSS管理器"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.state_file = STATE_FILE
        self.feeds_config = self._load_config()
        self.processed_items = self._load_state()
        
    def _load_config(self) -> Dict:
        """加载RSS配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 默认配置
                default_config = {
                    "feeds": [
                        {
                            "name": "示例RSS源",
                            "url": "https://example.com/rss",
                            "enabled": True
                        }
                    ],
                    "check_interval": 300  # 5分钟
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {"feeds": [], "check_interval": 300}
    
    def _save_config(self, config: Dict):
        """保存RSS配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def _load_state(self) -> Dict:
        """加载处理状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
            return {}
    
    def _save_state(self):
        """保存处理状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def _is_item_within_time_limit(self, published_time: datetime) -> bool:
        """检查项目是否在时间限制范围内"""
        time_limit_config = self.feeds_config.get('content_time_limit', {})
        if not time_limit_config.get('enabled', False):
            return True
        
        hours = time_limit_config.get('hours', 24)
        time_limit = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return published_time >= time_limit
    
    def _parse_feed(self, feed_url: str, feed_name: str = None) -> List[RSSItem]:
        """解析RSS订阅源"""
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning(f"解析RSS源可能存在格式问题: {feed_url}")
            
            items = []
            for entry in feed.entries:
                try:
                    # 解析发布时间
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        published = datetime.now(timezone.utc)
                    
                    # 转换为UTC+8时间
                    published_utc8 = published.astimezone(UTC_PLUS_8)
                    
                    # 获取摘要
                    summary = getattr(entry, 'summary', '')
                    if len(summary) > 500:
                        summary = summary[:500] + '...'
                    
                    # 构建来源字段：RSS订阅源名称 + 文章作者（如果存在）
                    source_parts = []
                    if feed_name:
                        source_parts.append(feed_name)
                    if hasattr(entry, 'author') and entry.author:
                        source_parts.append(entry.author)
                    
                    source = '  '.join(source_parts) if source_parts else '未知来源'
                    
                    item = RSSItem(
                        title=entry.title,
                        link=entry.link,
                        published=published_utc8,
                        summary=summary,
                        source=source
                    )
                    items.append(item)
                    
                except Exception as e:
                    logger.error(f"解析RSS条目失败: {e}")
                    continue
            
            logger.info(f"成功解析RSS源 {feed_url}: {len(items)} 个条目")
            return items
            
        except Exception as e:
            logger.error(f"解析RSS源失败 {feed_url}: {e}")
            return []
    
    def _is_item_processed(self, item: RSSItem) -> bool:
        """检查项目是否已处理"""
        item_hash = item.to_hash()
        return item_hash in self.processed_items
    
    def _mark_item_processed(self, item: RSSItem):
        """标记项目为已处理"""
        item_hash = item.to_hash()
        self.processed_items[item_hash] = {
            'title': item.title,
            'link': item.link,
            'processed_time': datetime.now(timezone.utc).isoformat()
        }
        
        # 限制状态文件大小，保留最近1000条记录
        if len(self.processed_items) > 1000:
            # 按处理时间排序，删除最旧的记录
            sorted_items = sorted(
                self.processed_items.items(),
                key=lambda x: x[1].get('processed_time', ''),
                reverse=True
            )
            self.processed_items = dict(sorted_items[:1000])
    
    def get_new_items(self) -> List[RSSItem]:
        """获取新的RSS项目"""
        new_items = []
        
        for feed_config in self.feeds_config.get('feeds', []):
            if not feed_config.get('enabled', True):
                continue
                
            feed_url = feed_config['url']
            feed_name = feed_config['name']
            
            logger.info(f"正在检查RSS源: {feed_name} ({feed_url})")
            
            items = self._parse_feed(feed_url, feed_name)
            for item in items:
                # 检查项目是否在时间限制范围内
                if not self._is_item_within_time_limit(item.published):
                    logger.debug(f"跳过过期项目: {item.title} (发布时间: {item.published})")
                    continue
                
                if not self._is_item_processed(item):
                    new_items.append(item)
                    self._mark_item_processed(item)
            
            # 添加小延迟避免对RSS服务器造成过大压力
            asyncio.sleep(1)
        
        # 按发布时间排序
        new_items.sort(key=lambda x: x.published, reverse=True)
        
        # 保存状态
        self._save_state()
        
        return new_items
    
    def format_telegram_message(self, item: RSSItem) -> str:
        """格式化Telegram消息"""
        # 转义Markdown特殊字符
        def escape_markdown(text: str) -> str:
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        title = item.title  # 标题不需要转义，保持原样
        summary = item.summary if item.summary else ""
        source = item.source  # 来源不需要转义
        
        # 格式化时间
        time_str = item.published.strftime('%Y-%m-%d %H:%M:%S')
        
        # 新的格式：标题 + 摘要 + 链接（纯文本） + 来源 + 发布时间
        message = f"{title}\n\n"
        
        if summary:
            message += f"{summary}\n\n"
        
        message += f"{item.link}\n\n"
        message += f"来源: {source}\n"
        message += f"发布时间: {time_str} (UTC+8)"
        
        return message

class RSSBot:
    """RSS机器人主类"""
    
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        # self.http_proxy = os.getenv('HTTP_PROXY')  # 注释掉代理环境变量
        self.http_proxy = None  # 强制不使用代理
        
        if not self.telegram_token or not self.telegram_chat_id:
            raise ValueError("请在.env文件中设置TELEGRAM_BOT_TOKEN和TELEGRAM_CHAT_ID")
        
        self.telegram_bot = TelegramBot(self.telegram_token, self.telegram_chat_id, self.http_proxy)
        self.rss_manager = RSSManager()
        
    async def run_once(self):
        """运行一次RSS检查"""
        logger.info("开始RSS订阅检查...")
        
        try:
            new_items = self.rss_manager.get_new_items()
            
            if not new_items:
                logger.info("没有发现新的RSS项目")
                return
            
            logger.info(f"发现 {len(new_items)} 个新的RSS项目")
            
            # 发送消息到Telegram
            for item in new_items:
                message = self.rss_manager.format_telegram_message(item)
                success = await self.telegram_bot.send_message(message)
                
                if success:
                    logger.info(f"成功发送消息: {item.title}")
                else:
                    logger.error(f"发送消息失败: {item.title}")
                
                # 添加延迟避免Telegram API限制
                await asyncio.sleep(1)
            
            logger.info("RSS订阅检查完成")
            
        except Exception as e:
            logger.error(f"RSS检查过程出错: {e}")
    
    async def run_continuously(self):
        """持续运行RSS检查"""
        check_interval = self.rss_manager.feeds_config.get('check_interval', 300)
        
        logger.info(f"开始持续运行模式，检查间隔: {check_interval}秒")
        
        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"运行过程中出错: {e}")
            
            logger.info(f"等待 {check_interval} 秒后进行下次检查...")
            await asyncio.sleep(check_interval)

async def main():
    """主函数"""
    try:
        bot = RSSBot()
        
        # 检查命令行参数
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == 'once':
            await bot.run_once()
        else:
            await bot.run_continuously()
            
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())