import asyncio
import io
import discord
from discord.ext import commands
from VAMModal import VAMModal

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.__cog_check__ = self.cog_check
    
    # async def cog_check(self, ctx):
    #     allowed_roles = {"Admin Staff", "Pastor", "Shadow Admin"}
    #     return any(role.name in allowed_roles for role in ctx.author.roles)

    @discord.app_commands.command(name = "create_ticket", description = "Create a new ticket for VAM requests")
    async def create_ticket(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VAMModal(interaction.user))

        try:
            modal_interaction = await self.bot.wait_for("modal_submit", timeout=800.0, check=lambda i: i.custom_id == "vam_modal")
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to fill out the form.", ephemeral=True)
            return
    
    async def cog_load(self):
        await self.bot.tree.sync(guild=discord.Object(id=607977353410379825))

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))