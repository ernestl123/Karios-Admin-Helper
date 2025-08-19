import json
import discord
from discord.ext import commands
import os
import random
import traceback

def load_config(path):
    with open(path, "r") as file:
        return json.load(file)

config = load_config("config.json")

TOKEN = config["token"]
PREFIX = config["prefix"]


bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), intents=discord.Intents.all())
bot.remove_command('help')
cogs = [
    "cogs.AdminMacros", "cogs.TicketSystem"
]
    
@bot.event
async def on_ready():
    # await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "you..."))
    print("Online")
    for extension in cogs:
        await bot.load_extension(f"{extension}")
    # await bot.tree.clear_commands(guild=None)  # Clear all global application commands
    await bot.tree.sync(guild=discord.Object(id=607977353410379825))  # Sync commands for a specific guild
    print("Tree synced.")


@bot.event
async def on_message(message):
    return
    # if not message.author.bot:
        # await bot.process_commands(message)
"""
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(error)       
        return

    print(error)
"""
if __name__ == '__main__':
    bot.run(TOKEN)