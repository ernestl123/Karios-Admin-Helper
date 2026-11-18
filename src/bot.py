import json
import os
from pathlib import Path
import sys
import threading
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

# Ensure src directory is in sys.path
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from webhook import start_webhook_server
except ImportError:
    from src.webhook import start_webhook_server

DEFAULT_CONFIG: Dict[str, Any] = {
    "token": os.getenv("DISCORD_TOKEN", "MOCK_TOKEN"),
    "prefix": os.getenv("BOT_PREFIX", "!"),
    "form_log_channel_id": int(os.getenv("FORM_LOG_CHANNEL_ID", "0")),
    "VAM_ticket_log_channel_id": int(os.getenv("VAM_TICKET_LOG_CHANNEL_ID", "0")),
    "form_port": int(os.getenv("FORM_PORT", "5000")),
    "pc_client_id": os.getenv("PC_CLIENT_ID", ""),
    "pc_client_secret": os.getenv("PC_CLIENT_SECRET", ""),
    "form_webhook_secret": os.getenv("FORM_WEBHOOK_SECRET", "")
}

def load_config(path: str = "config.json") -> Dict[str, Any]:
    """
    Loads bot configuration from JSON file or falls back to defaults/env vars.
    """
    config_path = Path(path)
    if not config_path.is_absolute():
        # Check relative to cwd first, then relative to project root
        if not config_path.exists():
            root_path = ROOT_DIR / path
            if root_path.exists():
                config_path = root_path

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
    return DEFAULT_CONFIG.copy()

config = load_config("config.json")

TOKEN = config.get("token")
PREFIX = config.get("prefix", "!")
FORM_LOG_CHANNEL_ID = config.get("form_log_channel_id")
VAM_TICKET_LOG_CHANNEL_ID = config.get("VAM_ticket_log_channel_id")
FORM_PORT = config.get("form_port", 5000)
PCO_API_TOKEN = config.get("pc_client_id")
PCO_API_SECRET = config.get("pc_client_secret")

def create_bot(custom_config: Optional[Dict[str, Any]] = None) -> commands.Bot:
    """Factory function to instantiate and configure the bot."""
    cfg = custom_config or config
    prefix = cfg.get("prefix", "!")
    intents = discord.Intents.all()
    bot_instance = commands.Bot(
        command_prefix=commands.when_mentioned_or(prefix),
        intents=intents,
        activity=discord.Game(name="Watching forms...")
    )
    bot_instance.remove_command('help')
    bot_instance.VAM_TICKET_LOG_CHANNEL_ID = cfg.get("VAM_ticket_log_channel_id")
    return bot_instance

bot = create_bot(config)

cogs = [
    "cogs.AdminMacros",
    "cogs.help"
]

@bot.event
async def on_ready():
    print("Online")
    for extension in cogs:
        try:
            await bot.load_extension(extension)
        except commands.ExtensionAlreadyLoaded:
            pass
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot:
        await bot.process_commands(message)

if __name__ == '__main__':
    threading.Thread(target=start_webhook_server, args=(bot, config), daemon=True).start()
    bot.run(TOKEN)
