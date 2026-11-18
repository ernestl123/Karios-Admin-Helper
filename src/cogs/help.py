import json
from pathlib import Path
import discord
from discord.ext import commands
import utils.year_utils as year_utils

def _load_admin_roles():
    p = year_utils.get_project_root() / "roles.json"
    if not p.exists():
        p = Path("roles.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as file:
            role_file = json.load(file)
            return role_file.get("role_info", {}).get("Admin_Access_Roles", [])
    return ["Admin Staff", "Pastor", "Shadow Admin"]

BOT_ADMIN_PERM = _load_admin_roles()

class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_check__ = self.cog_check
        for cmd in self.__cog_commands__:
            cmd.cog = self

    async def cog_check(self, ctx):
        allowed_roles = set(BOT_ADMIN_PERM)
        author_roles = getattr(ctx.author, "roles", [])
        return any(role.name in allowed_roles for role in author_roles)

    @commands.command(pass_context=True, hidden=True)
    async def help(self, ctx):
        """
        Displays a list of available commands and their descriptions.
        """
        embed = discord.Embed(
            title="Help - Available Commands",
            description="Here are the commands you can use:",
            color=discord.Color.blue()
        )

        for command in self.bot.commands:
            if command.hidden:
                continue
            embed.add_field(
                name=f"▫️{command.name}",
                value=command.help or "No description provided.",
                inline=False
            )
        embed.set_footer(text="Use the commands as shown with the following mention: @Kairos Admin Bot. Ex. @Kairos Admin Bot giveRole \"role_name\" \"member_name\"")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(help(bot))
