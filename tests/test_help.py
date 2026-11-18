from unittest.mock import MagicMock
import pytest
from cogs.help import help as HelpCog

@pytest.fixture
def help_cog(mock_bot):
    cmd1 = MagicMock()
    cmd1.name = "giveRole"
    cmd1.hidden = False
    cmd1.help = "Assigns role"

    cmd2 = MagicMock()
    cmd2.name = "secretCmd"
    cmd2.hidden = True
    cmd2.help = "Hidden"

    mock_bot.commands = [cmd1, cmd2]
    return HelpCog(mock_bot)

@pytest.mark.asyncio
async def test_help_command(help_cog, mock_ctx):
    await help_cog.help(mock_ctx)
    mock_ctx.send.assert_awaited_once()
    call_kwargs = mock_ctx.send.await_args[1]
    embed = call_kwargs["embed"]

    assert embed.title == "Help - Available Commands"
    field_names = [f.name for f in embed.fields]
    assert "▫️giveRole" in field_names
    assert "▫️secretCmd" not in field_names

@pytest.mark.asyncio
async def test_help_cog_check(help_cog, mock_ctx, mock_guild):
    assert await help_cog.cog_check(mock_ctx) is True

    unauth_member = mock_guild.members[1]
    mock_ctx.author = unauth_member
    assert await help_cog.cog_check(mock_ctx) is False
