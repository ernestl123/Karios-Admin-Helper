import json
import discord
from discord import ui

class VAMModal(ui.Modal, title="VAM Request Form"):

    # name = ui.TextInput(label="Name", placeholder="Enter your name")
    request_name = ui.TextInput(label="Title", placeholder="Enter a title for your request")
    ministry = ui.TextInput(label="Ministry", placeholder="Enter the ministry you are part of")
    description = ui.TextInput(label="Description", placeholder="Enter a brief description of your request", style=discord.TextStyle.paragraph)
    duedate = ui.TextInput(label="Due Date", placeholder="Enter the due date for your request (YYYY-MM-DD)", required=True)

    def __init__(self, user : discord.User, *args, **kwargs):
        super().__init__(custom_id="vam_modal", timeout=15, *args, **kwargs)
        self.user = user
        self.title = f"VAM Request Form - By {user.name}"

        with open("config.json", "r") as file:
            VAM_ticket_channel_id = json.load(file)["VAM_ticket_log_channel_id"]
    

    async def on_submit(self, interaction):
        # Handle the submission logic here
        log_channel = interaction.guild.get_channel(1407516953027023000)
        print(f"{interaction.guild}, Log channel: {log_channel}")
        if not log_channel:
            await interaction.response.send_message("Log channel not found.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title = self.request_name.value + " - " + self.ministry.value,
            description = f"Due Date: {self.duedate.value}\n\nDescription: {self.description.value}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {self.user.name}", icon_url=self.user.avatar.url if self.user.avatar else None)
        await log_channel.send(
            embed=embed
        )
        await interaction.response.send_message("Your request has been submitted successfully!", ephemeral=True)

    async def on_timeout(self):
        print("Modal timed out.")
        return await super().on_timeout()