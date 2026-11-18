import asyncio
from unittest.mock import AsyncMock, MagicMock
import discord
import pytest

class MockRole:
    def __init__(self, name: str, role_id: int = 1, color: discord.Color = discord.Color.default(), guild=None):
        self.id = role_id
        self.name = name
        self.color = color
        self.guild = guild
        self.mention = f"<@&{self.id}>"
        self.edit = AsyncMock()

    def __repr__(self):
        return f"<MockRole id={self.id} name='{self.name}'>"

class MockCategory:
    def __init__(self, name: str, category_id: int = 10):
        self.id = category_id
        self.name = name
        self.channels = []

    def __repr__(self):
        return f"<MockCategory id={self.id} name='{self.name}'>"

class MockChannel:
    def __init__(self, name: str, channel_id: int = 100, guild=None, category=None):
        self.id = channel_id
        self.name = name
        self.guild = guild
        self.category = category
        self.send = AsyncMock()
        self.edit = AsyncMock()
        self.delete = AsyncMock()

    def __repr__(self):
        return f"<MockChannel id={self.id} name='{self.name}'>"

class MockMember:
    def __init__(self, name: str, member_id: int = 1000, nick: str = None, roles=None, guild=None):
        self.id = member_id
        self.name = name
        self.display_name = nick or name
        self.nick = nick
        self.roles = roles or []
        self.guild = guild
        self.mention = f"<@{self.id}>"
        self.avatar = MagicMock()
        self.avatar.url = f"https://cdn.discordapp.com/avatars/{self.id}/avatar.png"
        self.default_avatar = MagicMock()
        self.default_avatar.url = "https://cdn.discordapp.com/embed/avatars/0.png"
        self.add_roles = AsyncMock()
        self.remove_roles = AsyncMock()

    def __repr__(self):
        return f"<MockMember id={self.id} name='{self.name}'>"

class MockGuild:
    def __init__(self, name: str = "TestGuild", guild_id: int = 12345):
        self.id = guild_id
        self.name = name
        self.roles = []
        self.members = []
        self.channels = []
        self.categories = []
        self.text_channels = []
        self.default_role = MockRole("@everyone", role_id=0, guild=self)
        self.roles.append(self.default_role)

    async def create_role(self, name: str, color: discord.Color = discord.Color.default(), reason: str = None):
        new_role = MockRole(name=name, role_id=len(self.roles) + 1, color=color, guild=self)
        self.roles.append(new_role)
        return new_role

    async def create_text_channel(self, name: str, category=None, overwrites=None):
        new_channel = MockChannel(name=name, channel_id=len(self.channels) + 1, guild=self, category=category)
        self.channels.append(new_channel)
        self.text_channels.append(new_channel)
        if category and hasattr(category, "channels"):
            category.channels.append(new_channel)
        return new_channel

    def get_role(self, role_id: int):
        for r in self.roles:
            if r.id == role_id:
                return r
        return None

class MockAttachment:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content

class MockMessage:
    def __init__(self, author, channel, content: str = "", attachments=None):
        self.author = author
        self.channel = channel
        self.content = content
        self.attachments = attachments or []

class MockContext:
    def __init__(self, bot, guild, channel, author, message=None):
        self.bot = bot
        self.guild = guild
        self.channel = channel
        self.author = author
        self.message = message or MockMessage(author=author, channel=channel)
        self.send = AsyncMock()

@pytest.fixture
def mock_guild():
    guild = MockGuild()
    archived_cat = MockCategory(name="Archived", category_id=200)
    special_cat = MockCategory(name="Special Events & Socials", category_id=201)
    class_cat = MockCategory(name="Class Chat", category_id=202)
    guild.categories.extend([archived_cat, special_cat, class_cat])

    staff_role = MockRole("Staff", 10, guild=guild)
    admin_role = MockRole("Admin Staff", 11, guild=guild)
    leadership_role = MockRole("Leadership", 12, guild=guild)
    prayer_role = MockRole("Prayer", 13, guild=guild)
    vam_role = MockRole("VAM", 14, guild=guild)
    guild.roles.extend([staff_role, admin_role, leadership_role, prayer_role, vam_role])

    admin_member = MockMember("AdminUser", 1001, nick="AdminNick", roles=[admin_role], guild=guild)
    normal_member = MockMember("NormalUser", 1002, nick="NormalNick", roles=[], guild=guild)
    guild.members.extend([admin_member, normal_member])

    staff_channel = MockChannel("staff", 301, guild=guild)
    notification_channel = MockChannel("new-leaders-notifications", 302, guild=guild)
    prayer_channel = MockChannel("prayer-team", 303, guild=guild)
    events_channel = MockChannel("game-night", 304, guild=guild, category=special_cat)
    special_cat.channels.append(events_channel)

    guild.channels.extend([staff_channel, notification_channel, prayer_channel, events_channel])
    guild.text_channels.extend([staff_channel, notification_channel, prayer_channel, events_channel])

    return guild

@pytest.fixture
def mock_bot(mock_guild):
    bot = MagicMock()
    bot.guilds = [mock_guild]
    bot.commands = []
    bot.wait_for = AsyncMock()

    loop = MagicMock()
    loop.create_task = MagicMock(side_effect=lambda coro: None)
    bot.loop = loop

    bot.get_channel = MagicMock(side_effect=lambda cid: next((c for c in mock_guild.channels if c.id == cid), None))
    bot.get_guild = MagicMock(side_effect=lambda gid: mock_guild if mock_guild.id == gid else None)
    return bot

@pytest.fixture
def mock_ctx(mock_bot, mock_guild):
    author = mock_guild.members[0] # AdminUser
    channel = mock_guild.channels[0] # staff
    return MockContext(bot=mock_bot, guild=mock_guild, channel=channel, author=author)
