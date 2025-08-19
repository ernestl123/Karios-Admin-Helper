import discord
from discord import ui

class VAMModal(ui.Modal, title="VAM Request Form"):

    # name = ui.TextInput(label="Name", placeholder="Enter your name")
    ministry = ui.TextInput(label="Ministry", placeholder="Enter the ministry you are part of")
    description = ui.TextInput(label="Description", placeholder="Enter a brief description of your request", style=discord.TextStyle.paragraph)
    duedate = ui.TextInput(label="Due Date", placeholder="Enter the due date for your request (YYYY-MM-DD)", required=True)

    def __init__(self, user : discord.User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    async def on_submit(self, interaction):
        # Handle the submission logic here
        await interaction.response.send_message(f"Request submitted successfully with info: {self.user.mention}\n{self.ministry}\n{self.description}", ephemeral=True)