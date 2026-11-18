import pytest
from unittest.mock import AsyncMock
from utils.channel_utils import (
    retire_channel,
    duplicate_channel,
    transition_channel,
    delete_channel
)
import discord

@pytest.mark.asyncio
async def test_retire_channel_with_year(mock_guild):
    channel = mock_guild.channels[0]
    res = await retire_channel(channel, 26)
    assert res is True
    channel.edit.assert_awaited_once()
    call_kwargs = channel.edit.await_args[1]
    assert call_kwargs["name"] == "staff-26"
    assert call_kwargs["category"].name == "Archived"

@pytest.mark.asyncio
async def test_retire_channel_default_year(mock_guild):
    channel = mock_guild.channels[0]
    res = await retire_channel(channel, -1)
    assert res is True
    call_kwargs = channel.edit.await_args[1]
    assert call_kwargs["name"] == "staff-archived"

@pytest.mark.asyncio
async def test_duplicate_channel(mock_guild):
    channel = mock_guild.channels[0]
    mock_guild.create_text_channel = AsyncMock(return_value="duplicated_channel")
    res = await duplicate_channel(channel)
    assert res == "duplicated_channel"
    mock_guild.create_text_channel.assert_awaited_once_with(
        name=channel.name,
        category=channel.category,
        overwrites=None
    )

@pytest.mark.asyncio
async def test_transition_channel_with_channel_obj(mock_guild):
    channel = mock_guild.channels[0]
    mock_guild.create_text_channel = AsyncMock(return_value="new_channel")
    res = await transition_channel(channel, 26)
    assert res == "new_channel"
    channel.edit.assert_awaited_once()

@pytest.mark.asyncio
async def test_transition_channel_with_ctx(mock_ctx, mock_guild):
    mock_guild.create_text_channel = AsyncMock(return_value="new_channel")
    res = await transition_channel(mock_ctx, "staff", 26)
    assert res == "new_channel"

@pytest.mark.asyncio
async def test_delete_channel_success(mock_guild):
    channel = mock_guild.channels[0]
    res = await delete_channel(channel)
    assert res is True
    channel.delete.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_channel_forbidden(mock_guild):
    channel = mock_guild.channels[0]
    channel.delete = AsyncMock(side_effect=discord.Forbidden(AsyncMock(), "Forbidden"))
    with pytest.raises(ValueError, match="Bot does not have permission to delete channel"):
        await delete_channel(channel)


@pytest.mark.asyncio
async def test_retire_channel_exception(mock_guild):
    channel = mock_guild.channels[0]
    channel.edit = AsyncMock(side_effect=Exception("Edit channel failed"))
    with pytest.raises(ValueError, match="Failed to retire channel"):
        await retire_channel(channel, 26)

@pytest.mark.asyncio
async def test_duplicate_channel_generic_exception(mock_guild):
    channel = mock_guild.channels[0]
    mock_guild.create_text_channel = AsyncMock(side_effect=Exception("Create chan failed"))
    with pytest.raises(ValueError, match="Failed to duplicate channel"):
        await duplicate_channel(channel)

@pytest.mark.asyncio
async def test_transition_channel_invalid_target():
    with pytest.raises(ValueError, match="Invalid target provided"):
        await transition_channel(12345, "invalid")
