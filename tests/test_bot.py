import json
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import pytest
from bot import create_bot, load_config, on_message

def test_load_config_with_file(tmp_path):
    config_file = tmp_path / "config.json"
    data = {
        "token": "CUSTOM_TOKEN",
        "prefix": "$",
        "form_port": 8080
    }
    config_file.write_text(json.dumps(data), encoding="utf-8")

    cfg = load_config(str(config_file))
    assert cfg["token"] == "CUSTOM_TOKEN"
    assert cfg["prefix"] == "$"
    assert cfg["form_port"] == 8080

def test_load_config_fallback(tmp_path):
    missing_file = tmp_path / "missing.json"
    cfg = load_config(str(missing_file))
    assert "token" in cfg
    assert "prefix" in cfg

def test_create_bot_custom_config():
    custom_cfg = {
        "token": "TEST_TOKEN",
        "prefix": "?",
        "VAM_ticket_log_channel_id": 9999
    }
    bot_inst = create_bot(custom_cfg)
    assert bot_inst.VAM_TICKET_LOG_CHANNEL_ID == 9999
    assert bot_inst.get_command('help') is None

@pytest.mark.asyncio
async def test_on_message_ignores_bot():
    mock_msg = MagicMock()
    mock_msg.author.bot = True

    with patch("bot.bot.process_commands", new=AsyncMock()) as mock_proc:
        await on_message(mock_msg)
        mock_proc.assert_not_awaited()

@pytest.mark.asyncio
async def test_on_message_processes_user():
    mock_msg = MagicMock()
    mock_msg.author.bot = False

    with patch("bot.bot.process_commands", new=AsyncMock()) as mock_proc:
        await on_message(mock_msg)
        mock_proc.assert_awaited_once_with(mock_msg)


@pytest.mark.asyncio
async def test_on_ready():
    from bot import on_ready, bot
    with patch.object(bot, "load_extension", new=AsyncMock()) as mock_load:
        await on_ready()
        assert mock_load.await_count == 2
