import json
import sqlite3
import discord
from discord.ext import commands
from database.DBManager import DBManager
import threading
import requests

import utils
from webhook import start_webhook_server

def load_config(path):
    with open(path, "r") as file:
        return json.load(file)

config = load_config("config.json")

TOKEN = config["token"]
PREFIX = config["prefix"]
FORM_LOG_CHANNEL_ID = config["form_log_channel_id"]
VAM_TICKET_LOG_CHANNEL_ID = config["VAM_ticket_log_channel_id"]
FORM_PORT = config["form_port"]
PCO_API_TOKEN = config.get("pc_client_id")
PCO_API_SECRET = config.get("pc_client_secret")

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), intents=discord.Intents.all(), activity=discord.Game(name="Watching forms..."))
bot.remove_command('help')
cogs = [
    "cogs.AdminMacros"
    #"cogs.TicketSystem"
]
bot.VAM_TICKET_LOG_CHANNEL_ID = VAM_TICKET_LOG_CHANNEL_ID
    
@bot.event
async def on_ready():
    # await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "you..."))
    print("Online")
    for extension in cogs:
        await bot.load_extension(f"{extension}")
    # await bot.tree.clear_commands(guild=None)  # Clear all global application commands
    # await bot.tree.sync(guild=discord.Object(id=607977353410379825))  # Sync commands for a specific guild
    # print("Tree synced.")


@bot.event
async def on_message(message):
    
    if not message.author.bot:
        await bot.process_commands(message)

@bot.event
async def setup_hook():
    # sqlite3.connect("database/kairos.db")
    bot.db = DBManager("src/database/kairos.db")
    try:
        await bot.db.connect()
        print("Connected to database.")
    except Exception as e:
        print(f"Error connecting to database: {e}")

@bot.event
async def on_member_join(member):
    # Check if the member exists in the database
    if not await bot.db.check_member_exists(member.id):
        print(f"Member {member.name} not found in database on join. No roles assigned.")
        return
    
    grad_year, school, college = await bot.db.get_member(member.id)
    
    # Assign roles based on the retrieved data
    # await utils.assign_new_member(member, member.name, school, college, grad_year, member.guild)
    print(f"Assigned roles to {member.name} based on database info.")
"""
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(error)       
        return

    print(error)
"""

if __name__ == '__main__':
    threading.Thread(target=start_webhook_server, args=(bot, config), daemon=True).start()
    bot.run(TOKEN)