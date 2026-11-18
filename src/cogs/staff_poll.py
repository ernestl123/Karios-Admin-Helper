import datetime
from typing import Optional
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands, tasks
import utils.poll_utils as poll_utils

PST_TZ = ZoneInfo("America/Los_Angeles")
POLL_TIME = datetime.time(hour=10, minute=0, tzinfo=PST_TZ)

class StaffPoll(commands.Cog):
    def __init__(self, bot, config: Optional[dict] = None):
        self.bot = bot
        self.config = config or getattr(bot, "config", {})
        for cmd in self.__cog_commands__:
            cmd.cog = self

    async def cog_load(self):
        """Called automatically when the cog is loaded into the bot."""
        if not self.weekly_poll_task.is_running():
            self.weekly_poll_task.start()

    def cog_unload(self):
        if self.weekly_poll_task.is_running():
            self.weekly_poll_task.cancel()

    def get_poll_channel(self) -> Optional[discord.TextChannel]:
        """Resolves the designated poll channel from config or bot attributes."""
        channel_id = (
            self.config.get("staff_availability_channel_id")
            or self.config.get("staff_poll_channel_id")
            or getattr(self.bot, "STAFF_AVAILABILITY_CHANNEL_ID", None)
        )
        if not channel_id:
            return None
        try:
            return self.bot.get_channel(int(channel_id))
        except (ValueError, TypeError):
            return None

    async def send_poll(self, target_channel: Optional[discord.TextChannel] = None) -> Optional[discord.Message]:
        """
        Generates and sends the weekly Staff Availability poll to the target channel.

        Args:
            target_channel: Optional TextChannel to send to. Defaults to configured channel.

        Returns:
            discord.Message: The sent message if successful, or None.
        """
        channel = target_channel or self.get_poll_channel()
        if not channel:
            print("StaffPoll: Poll channel not configured or not found.")
            return None

        poll = poll_utils.create_staff_availability_poll()
        try:
            message = await channel.send(poll=poll)
            print(f"StaffPoll: Sent weekly availability poll to #{channel.name}.")
            return message
        except Exception as e:
            print(f"StaffPoll: Failed to send weekly poll: {e}")
            return None

    @tasks.loop(time=POLL_TIME)
    async def weekly_poll_task(self):
        """Runs every day at 10:00am PST; triggers the poll if today is Monday."""
        now = datetime.datetime.now(PST_TZ)
        if now.weekday() == 0:  # 0 is Monday
            await self.send_poll()

    @weekly_poll_task.before_loop
    async def before_weekly_poll_task(self):
        """Waits for bot to be ready before scheduling task executions."""
        await self.bot.wait_until_ready()

    @commands.command(name="sendStaffPoll", pass_context=True, hidden=True)
    async def send_staff_poll_command(self, ctx, channel: Optional[discord.TextChannel] = None):
        """
        Manually triggers sending the Staff Availability poll for testing or admin dispatch.
        Usage: sendStaffPoll [#channel]
        """
        target = channel or ctx.channel
        msg = await self.send_poll(target_channel=target)
        if msg:
            await ctx.send(f"Staff availability poll successfully sent to {target.mention}.")
        else:
            await ctx.send(f"Failed to send staff availability poll to {target.mention}. Check bot permissions.")

async def setup(bot):
    await bot.add_cog(StaffPoll(bot))
