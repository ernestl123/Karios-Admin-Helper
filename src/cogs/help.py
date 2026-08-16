import discord
from discord.ext import commands
import json

with open("roles.json", "r") as file:
    role_file = json.load(file)
    BOT_ADMIN_PERM = role_file["role_info"]["Admin_Access_Roles"]

class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.__cog_check__ = self.cog_check

    async def cog_check(self, ctx):
            allowed_roles = set(BOT_ADMIN_PERM)
            return any(role.name in allowed_roles for role in ctx.author.roles)

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