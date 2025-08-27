import json
import discord
from discord.ext import commands
from flask import Flask, request
import threading

def load_config(path):
    with open(path, "r") as file:
        return json.load(file)

config = load_config("config.json")

TOKEN = config["token"]
PREFIX = config["prefix"]
FORM_LOG_CHANNEL_ID = config["form_log_channel_id"]
VAM_TICKET_LOG_CHANNEL_ID = config["VAM_ticket_log_channel_id"]
FORM_PORT = config["form_port"]

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
"""
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(error)       
        return

    print(error)
"""

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook data:", data)
    if request.headers.get('Webhook-Secret') != config.get('form_webhook_secret'):
        return "Unauthorized", 401
    
    channel_id = FORM_LOG_CHANNEL_ID
    channel = bot.get_channel(channel_id)
    if channel:
        print("Sending message to channel:", channel.name, "with data:", data)
        description = ""
        for key, item in data['data'].items():
            if key != 'Timestamp':
                if isinstance(item, str):
                    item = item.split(',')
                    description += f"**{key}**:\n"

                    for x in item:
                        description += f"▫️`{x.strip()}`\n "

                elif isinstance(item, list):
                    description += f"**{key}**:"
                    for x in item:
                        description += f"`{x}` "
                    description += "\n"
        
        embed = discord.Embed(title= data.get('title', 'No Form Title'), description=description, color=discord.Color.blue())
        embed.set_footer(text="Submitted at: " + "{}".format(
            data['data'].get('Timestamp', 'No Time Provided')
        ))
        bot.loop.create_task(channel.send(embed=embed))
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=FORM_PORT)
    
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)