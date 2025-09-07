import subprocess
import sys
import os

def install_package(package):
    """安装单个包"""
    try:
        print(f"📦 正在安装 {package}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package,
            "--proxy", "http://127.0.0.1:7897",
            "--trusted-host", "pypi.org",
            "--trusted-host", "pypi.python.org",
            "--trusted-host", "files.pythonhosted.org"
        ])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安装失败: {e}")
        return False

def install_requirements():
    """安装 requirements.txt 中的所有依赖"""
    print("🚀 开始安装依赖包...")
    print("使用代理: http://127.0.0.1:7897")
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ {requirements_file} 文件不存在")
        return False
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"📋 需要安装的包: {len(packages)} 个")
        
        success_count = 0
        for package in packages:
            if install_package(package):
                success_count += 1
            else:
                # 如果失败，尝试单独安装
                package_name = package.split('>=')[0].split('==')[0].split('<')[0]
                print(f"🔄 尝试单独安装 {package_name}...")
                if install_package(package_name):
                    success_count += 1
        
        print(f"\n🎉 安装完成! 成功: {success_count}/{len(packages)} 个包")
        
        # 检查 discord.py
        try:
            import discord
            print(f"✅ discord.py 版本: {discord.__version__}")
        except ImportError:
            print("❌ discord.py 未正确安装")
        
        # 检查 python-telegram-bot
        try:
            import telegram
            print(f"✅ python-telegram-bot 已安装")
        except ImportError:
            print("❌ python-telegram-bot 未正确安装")
            
        return success_count == len(packages)
        
    except Exception as e:
        print(f"❌ 读取 requirements.txt 失败: {e}")
        return False

def upgrade_pip():
    """升级 pip"""
    print("📈 正在升级 pip...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip",
            "--proxy", "http://127.0.0.1:7897",
            "--trusted-host", "pypi.org",
            "--trusted-host", "pypi.python.org",
            "--trusted-host", "files.pythonhosted.org"
        ])
        print("✅ pip 升级成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ pip 升级失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Discord/Telegram Bot 依赖安装工具")
    print("=" * 50)
    
    # 升级 pip
    upgrade_pip()
    
    # 安装依赖
    success = install_requirements()
    
    if success:
        print("\n🎉 所有依赖安装完成!")
        print("现在可以运行:")
        print("- python test_telegram.py  # 测试 Telegram 连接")
        print("- python test_discord.py   # 测试 Discord 连接")
        print("- python discord_to_telegram_bot.py  # 启动完整 Bot")
    else:
        print("\n💥 部分依赖安装失败，请检查网络连接")
        print("可以手动尝试: pip install discord.py python-telegram-bot")
    
    input("\n按任意键退出...")