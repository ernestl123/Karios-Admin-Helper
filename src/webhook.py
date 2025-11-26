import json
from flask import Flask, request
import requests
import discord
from utils import assign_role
import utils
CURRENT_YEAR = 25

YEAR_DICT ={
    str(CURRENT_YEAR) : ["2025", "senior", "seniors", "fourth", "4th"],
    str(CURRENT_YEAR + 1) : ["2026", "junior", "juniors", "third", "3rd"],
    str(CURRENT_YEAR + 2) : ["2027", "sophomore", "sophomores", "second", "2nd"],
    str(CURRENT_YEAR + 3) : ["2028", "freshman", "freshmen", "first", "1st"]
}

def start_webhook_server(bot, config):
    app = Flask(__name__)

    PCO_API_TOKEN = config.get("pc_client_id")
    PCO_API_SECRET = config.get("pc_client_secret")
    FORM_PORT = config.get("form_port", 5000)

    FORM_LOG_CHANNEL_ID = config.get("form_log_channel_id")
    GUILD_ID = config.get("guild_id")
    GS_SECRET = str(config.get("form_webhook_secret", "")) # for Google Forms or similar
    
    def send_request(url):
        api_response = requests.get(url, auth=(PCO_API_TOKEN, PCO_API_SECRET))
        api_response.raise_for_status() # Raises an exception for HTTP errors

        form_data = api_response.json()
        print("Successfully retrieved form data:", form_data)

        data = form_data.get('data', [])
        return data
    
    @app.route('/planning-center', methods=['POST'])
    def planning_center_webhook():
        """Receives the initial webhook and makes two API call for name and form data."""
        try:
            #Parse the incoming webhook payload
            payload = request.get_json()
            if not payload:
                print("Received an empty or invalid JSON payload.")
                return "Bad Request", 400

            #print("Webhook received. Payload:")
            # print(json.dumps(payload, indent=2))

            # Extract the URL for the new form submission
            # The payload contains links, not the form data itself.
            # payload['data'] is a list of event deliveries; take the first event
            events = payload.get('data') or []
            if not events:
                print("No events found in payload.")
                return "Malformed Payload", 400

            event0 = events[0]
            attributes = event0.get('attributes', {})
            # attributes['payload'] is a JSON string — parse it
            payload_str = attributes.get('payload')
            if not payload_str:
                print("No nested payload string found in attributes.")
                return "Malformed Payload", 400

            try:
                nested = json.loads(payload_str)
            except json.JSONDecodeError as je:
                print("Failed to parse nested payload JSON:", je)
                return "Malformed Nested Payload", 400

            #print("Parsed nested payload:")
            # print(json.dumps(nested, indent=2))

            form_submission_url = nested.get('data', {}).get('links', {}).get('form_submission_values')

            if not form_submission_url:
                print("Webhook payload did not contain a valid form submission URL.")
                return "Malformed Payload", 400
            
            #Make first API call to get person's name
            people_url = form_submission_url.split("/form_submissions/")[0]
            print("Sending request on to Planning Center API.: " + people_url)
            data = send_request(people_url)
            if data:
                first_name = data.get('attributes', {}).get('first_name', {})
                last_name = data.get('attributes', {}).get('last_name', {})

                name = first_name + " " + last_name

            #Make second API call to get Discord handle
            print(f"Fetching form data from: {form_submission_url}")
            data = send_request(form_submission_url)
            #rint(json.dumps(data, indent=2))
            if data:
                for item in data:
                    print(item.get('attributes', {}).get('display_value', {}))
                school = data[-1].get('attributes', {}).get('display_value', {})
                college = data[-8].get('attributes', {}).get('display_value', {})
                year = data[-11].get('attributes', {}).get('display_value', {}).lower()
                
                grad_year = None
                for key, values in YEAR_DICT.items():
                    if year in values:
                        grad_year = f"Class of '{key}"
                        break

                discord_handle = data[-3].get('attributes', {}).get('display_value', {})
                
            
            # Store member info in the database
            guild = bot.get_guild(GUILD_ID)
            discord_member = discord.utils.get(guild.members, name=discord_handle)
            if discord_member:
                bot.loop.create_task(bot.db.add_member(name, discord_member.id, grad_year, school, college))
                bot.loop.create_task(utils.assign_new_member(discord_member, name, school, college, grad_year, guild))
                print(f"Stored member info in database for Discord handle: {discord_handle} with name : {name}, grad year: {grad_year}, school: {school}, college: {college}")
            else:
                print(f"Could not find Discord ID for handle: {name}. Member info not stored.")

            return "Webhook processed successfully!", 200

        except requests.exceptions.RequestException as e:
            print(f"Error making API request to Planning Center: {e}")
            return "API Error", 500
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Internal Server Error", 500

    @app.route('/webhook', methods=['POST'])
    def form_webhook():
        data = request.json
        #print("Received webhook data:", data)
        if request.headers.get('Webhook-Secret') != config.get('form_webhook_secret'):
            print("Unauthorized webhook attempt.")
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
                            if x.strip():
                                description += f"▫️`{x.strip()}`\n "

                    elif isinstance(item, list):
                        description += f"**{key}**:"
                        for x in item:
                            description += f"`{x}` "
                        description += "\n"
            
            form_title = data.get("title", "No Form Title")
            embed = discord.Embed(title= form_title, description=description)
            embed.set_footer(text="Submitted at: " + "{}".format(
                data['data'].get('Timestamp', 'No Time Provided')
            ))
            embed.color
            if form_title == "Late Rides Form":
                embed.color = discord.Colour.red()
            elif form_title == "Rides Form":
                embed.color = discord.Colour.blue()
            elif "driver" in form_title.lower():
                embed.color = discord.Colour.green()

            bot.loop.create_task(channel.send(embed=embed))
        return "OK", 200

    app.run(host="0.0.0.0", port=int(config.get("form_port", FORM_PORT)))