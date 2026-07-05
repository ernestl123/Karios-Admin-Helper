import io
import discord
from discord.ext import commands
from discord.ext.commands import has_role
import asyncio
import os
import random
import json
import csv

from flask import ctx

# from cogs.utils import *  # Removed because 'cogs.utils' could not be resolved and is not used in this file
import role_utils
import channel_utils

YEARS = {
    "Class of '26": ["26", "2026", "senior", "seniors", "fourth", "4th", "4th year", '4'],
    "Class of '27": ["27", "2027", "junior", "juniors", "third", "3rd", "3rd year", '3'],
    "Class of '28": ["28", "2028", "sophomore", "sophomores", "second", "2nd", "2nd year", '2'],
    "Class of '29": ["29", "2029", "freshman", "freshmen", "first", "1st", "1st year", '1']
}

class AdminMacros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.__cog_check__ = self.cog_check
    
    async def cog_check(self, ctx):
        allowed_roles = {"Admin Staff", "Pastor", "Shadow Admin"}
        return any(role.name in allowed_roles for role in ctx.author.roles)

    @commands.command(pass_context = True)
    async def importCSV(self, ctx):
        """
        Imports member data from a CSV file attached to the command message.
        The CSV file should have the following columns: name, discord_handle, grad_year, school, college.

        Args:
            ctx: The context of the command.
        """
        if not ctx.message.attachments:
            return await ctx.send("Please attach a CSV file to the message.")

        # Get the attachment (we assume only one for this example)
        attachment = ctx.message.attachments[0]

        # Validate the file type
        if not attachment.filename.endswith(".csv"):
            return await ctx.send("Please attach a valid CSV file.")

        try:
            # Download the attachment content as bytes
            csv_data_bytes = await attachment.read()
            csv_data_str = csv_data_bytes.decode('utf-8')  # Decode to string

            # Use io.StringIO to treat the string as a file for the csv reader
            csv_file = io.StringIO(csv_data_str)

            # Process the CSV data
            reader = csv.reader(csv_file)
            next(reader)  # Skip the header row

            rows_processed = 0
            total_rows = len(list(reader))
            csv_file.seek(0)
            next(reader)  # Skip header again after seek

            for row in reader:
                name = row[1].strip() + " " + row[2].strip()
                discord_handle = row[-1].strip().split("#")[0].replace('@', '')  # Remove discriminator and '@' if present
                grad_year = row[15].strip()
                school = row[13].strip()
                college = row[14].strip()
                
                found = False
                for year, keywords in YEARS.items():
                    if grad_year.lower() in keywords:
                        grad_year = year
                        found = True
                        break
                if not found:
                    print(f"Could not determine graduation year for entry: {name} with grad_year value: {grad_year}. Skipping.")
                    continue

                guild = ctx.guild
                discord_member = discord.utils.get(guild.members, name=discord_handle)
                await self.bot.db.add_member(name, discord_handle, discord_member.id if discord_member else None, grad_year, school, college)
                rows_processed += 1
                
                if discord_member:
                    await role_utils.assign_new_member(discord_member, name, school, college, grad_year, guild)
                    print(f"Stored member info in database for Discord handle: {discord_handle} with name : {name}, grad year: {grad_year}, school: {school}, college: {college}")
                    
                else:
                    print(f"ERROR: Could not find Discord ID for handle: {discord_handle} for: {name}. Manual assignment may be required.")
                    await ctx.send(f"ERROR: Could not find Discord ID for handle: {discord_handle} for: {name}. Manual assignment may be required.")

            await ctx.send(f"Successfully processed {rows_processed}/{total_rows} rows from the CSV file.")

        except Exception as e:
            await ctx.send(f"An error occurred while processing: " + e)

    @commands.command(pass_context = True)
    async def assignLeadership(self, ctx):
        """
        Assigns roles to members based on a CSV file attached to the command message.
        The CSV file should have two columns: role name and member name.

        Args:
            ctx: The context of the command.
        """
        if not ctx.message.attachments:
            return await ctx.send("Please attach a CSV file to the message.")

        # Get the attachment (we assume only one for this example)
        attachment = ctx.message.attachments[0]

        # Validate the file type
        if not attachment.filename.endswith(".csv"):
            return await ctx.send("Please attach a valid CSV file.")

        try:
            # Download the attachment content as bytes
            csv_data_bytes = await attachment.read()
            csv_data_str = csv_data_bytes.decode('utf-8')  # Decode to string

            # Use io.StringIO to treat the string as a file for the csv reader
            csv_file = io.StringIO(csv_data_str)

            # Process the CSV data
            reader = csv.reader(csv_file)
            next(reader)  # Skip the header row

            rows_processed = 0
            total_rows = len(list(reader))

            role_names = []
            leadership_role = discord.utils.get(ctx.guild.roles, name="Leadership")

            error_str = ""
            for row in reader:
                print(f"Row: {row}")
                role_name = row[0].strip()
                member_name = row[1].strip()

                role_obj = self.get_role_by_name(ctx, role_name)
                if role_obj:
                    member = self.get_user_case_insensitive(ctx, member_name)

                    if member:
                        await member.add_roles(role_obj)
                        print(f"Assigned role **{role_name}** to **{member_name}**.")
                        rows_processed += 1
                    else:
                        error_str += f"ERROR: Member '{member_name}' not found when for role assignment: {role_name}\n"
                else:
                    error_str += f"ERROR: Role '{role_name}' not found when assigning to '{member_name}'\n"

            if error_str:
                await ctx.send(embed = discord.Embed(description=error_str, color=discord.Color.red()))

            await ctx.send(f"Successfully processed {rows_processed}/{total_rows} rows from the CSV file.")

        except Exception as e:
            await ctx.send(f"An error occurred while processing the CSV file: {e.with_traceback()}")

    def get_role_by_name(self, ctx, role_name : str):
        """Helper function to get a role by its name."""
        return discord.utils.get(ctx.guild.roles, name=role_name)
        
    def get_user_case_insensitive(self, ctx, search_name: str):
        """
        Retrieves a user by their name (or display name) case-insensitively.
        """
        guild = ctx.guild  # Get the Guild object from the context
        search_name_lower = search_name.lower() # Convert search name to lowercase for comparison

        member = next(
            (m for m in guild.members if m.name.lower() == search_name_lower or m.display_name.lower() == search_name_lower),
        )
        return member

    @commands.command(pass_context=True)
    async def transitionChannel(self, ctx, channel_name : str, grad_year : int,):
        if await channel_utils.transition_channel(ctx, channel_name, grad_year):
            await ctx.send(f"Old channel '{channel_name}' retired to Archived category and new copy created.")
        else:
            await ctx.send(f"Failed to process channel '{channel_name}'. Please check the logs for more details.")

    @commands.command(pass_context=True)
    async def retireChannel(self, ctx, channel: discord.TextChannel = None, grad_year : int = -1):
        if not channel:     
            return await ctx.send(f"Channel '{channel}' not found in the server.")
        await channel_utils.retire_channel(channel, grad_year)
        await ctx.send(f"Channel '{channel.name}' retired to Archived category.")

    @commands.command(pass_context=True)
    async def deleteChannel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            return await ctx.send(f"Channel '{channel}' not found in the server.")
        #Ask for confirmation before deleting the channel
        await ctx.send(f"Are you sure you want to delete the channel '{channel.name}'? Type 'yes' to confirm or 'no' to cancel.")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']
        
        try:
            event = await self.bot.wait_for('message', check=check, timeout = 30.0)
            if event.content.lower() == 'no':
                await ctx.send(f"Channel deletion cancelled.")
                return
            await channel_utils.delete_channel(channel)
            await ctx.send(f"Channel '{channel.name}' deleted.")
        except discord.Forbidden:
            await ctx.send(f"Bot does not have permission to delete channel '{channel.name}'.")
            return
        except asyncio.TimeoutError:
            await ctx.send(f"Channel deletion timed out.")
            return

    @commands.command(pass_context=True)
    async def getYears(self, ctx):
        """
        Displays the current graduation years for each class in the server.
        """
        try:
            with open('current_years.json', 'r') as file:
                current_years = json.load(file)
            
            years_info = "\n".join([f"**{class_name}**: {year}" for class_name, year in current_years.items()])
            await ctx.send(embed=discord.Embed(title="Current Graduation Years", description=years_info, color=discord.Color.blue()))
        except Exception as e:
            await ctx.send(f"An error occurred while retrieving graduation years: {e}")

    @commands.command(pass_context=True)
    async def setYears(self, ctx, year_name: str, year_number: int):
        """
        Updates the graduation year for a specific class in the server.

        Args:
            ctx: The context of the command.
            year_name (str): The name of the class (e.g., "Freshman", "Sophomore", "Junior", "Senior").
            year_number (int): The new graduation year to set for the specified class.
        """
        try:
            with open('current_years.json', 'r') as file:
                current_years = json.load(file)

            year_name = year_name.capitalize()  # Ensure the year name is capitalized to match the keys in the JSON file
            if year_name not in current_years:
                await ctx.send(f"Invalid class name '{year_name}'. Valid options are: {', '.join(current_years.keys())}.")
                return
            
            current_years[year_name] = year_number
            
            with open('current_years.json', 'w') as file:
                json.dump(current_years, file, indent=4)
            
            await ctx.send(f"Updated graduation year for **{year_name}** to **{year_number}**.")
        except Exception as e:
            await ctx.send(f"An error occurred while updating graduation years: {e}")  

    @commands.command(pass_context=True)
    async def transition(self, ctx, grad_year : int):
        """
        A mass script to transition all roles and channels for a given graduation year.
        
        Args:
            ctx: The context of the command.
            grad_year (int): The last two digits of the graduation year to transition.
        
        Returns:
            None    
        """
        if len(str(abs(grad_year))) != 2:
            await ctx.send(f"Invalid graduation year '{grad_year}'. Please provide the last two digits of the year (e.g., 26 for 2026).")
            return
        
        try:
            #Update all the leadership roles
            with open('roles.json', 'r') as file:
                roles_data = json.load(file)
            
            log_output = "---TRANSITIONING ROLES---\n"

            roles = roles_data['roles']
            for role_name in roles:
                role_obj = self.get_role_by_name(ctx, role_name)

                try:
                    if role_obj:
                        #rename role
                        replaced_role = await role_utils.transition_role(role_obj, grad_year)
                    else:
                        log_output += f"ERROR: Role not found: {role_name}\n"

                    #move channel to archive category
                    if role_name == "Prayer":
                        channel_name = "prayer-team"
                    else:
                        channel_name = role_name.replace(" ", "-").lower()  # Replace spaces with hyphens for channel name

                    old_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                    if not old_channel:
                        log_output += f"ERROR: Channel '{channel_name}' not found in the server. Cannot archive.\n"
                        continue
                    
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        replaced_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                    await channel_utils.transition_channel(old_channel, grad_year, overwrites)
                    log_output += f"SUCCESS: Moved channel '{role_name}' to archive category\n"

                except discord.Forbidden:
                    log_output += f"ERROR: Failed to edit role '{role_name}'. Check permissions.\n"
                    continue
            
            log_output += "\n---DELETING SPECIAL EVENTS & SOCIAL CHANNELS---\n"
            #Archive all channels in the special events category
            special_events_category = discord.utils.get(ctx.guild.categories, name="Special Events & Socials")
            for channel in special_events_category.channels:
                await channel_utils.delete_channel(channel)
                log_output += f"SUCCESS: Deleted channel '{channel.name}' from the server.\n"

            # Update the current years in the JSON file
            with open('current_years.json', 'r') as file:
                current_years = json.load(file)
            
            # Update the current years in the JSON file
            current_years["Freshman"] = int("20" + str(grad_year + 4))
            current_years["Sophomore"] = int("20" + str(grad_year + 3))
            current_years["Junior"] = int("20" + str(grad_year + 2))
            current_years["Senior"] = int("20" + str(grad_year + 1))

            log_output += "\n---ARCHIVING GRADUATING CLASS CHANNEL---\n"

            #Archive the grad_year chat
            grad_year_channel = discord.utils.get(ctx.guild.channels, name=f"co-20{grad_year}")
            if grad_year_channel:
                await channel_utils.retire_channel(grad_year_channel, grad_year)
                log_output += f"SUCCESS: Moved channel '{grad_year_channel.name}' to archive category. Byeeee\n"

            log_output += "\n---CREATING NEW CLASS ROLES AND CHANNELS---\n"
            for year_int in current_years.values():
                #Create a Class of '{year_int}' role if it doesn't exist
                class_role_name = f"Class of '{str(year_int)[-2:]}"
                class_role = discord.utils.get(ctx.guild.roles, name=class_role_name)
                if not class_role:
                    class_role = await ctx.guild.create_role(name=class_role_name, color=discord.Color.default(), reason=f"Creating new class role for graduation year '{year_int}")
                    print(f"Created new role '{class_role_name}' for graduation year '{year_int}'.")
                    log_output += f"SUCCESS: Created new role '{class_role_name}' for graduation year '{year_int}'.\n"
                else:
                    log_output += f"INFO: Role '{class_role_name}' already exists. Skipping creation.\n"

                #Make a co-{year_int} channel if it doesn't exist
                co_channel_name = f"co-{str(year_int)}"
                co_channel = discord.utils.get(ctx.guild.channels, name=co_channel_name)

                if not co_channel:
                    #Define permissions for the new channel
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        class_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }

                    # Create the channel in the same category as the Leadership channels
                    class_chat_category = discord.utils.get(ctx.guild.categories, name="Class Chat")
                    if class_chat_category:
                        await ctx.guild.create_text_channel(name=co_channel_name, category=class_chat_category, overwrites=overwrites)
                        log_output += f"SUCCESS: Created new channel '{co_channel_name}' in Class Chat category.\n"
                    else:
                        log_output += "ERROR: Class Chat category not found. Cannot create college class channel. Please create the category first.\n"
                else:
                    log_output += f"INFO: Channel '{co_channel_name}' already exists. Skipping creation. We gucci\n"

            with open('current_years.json', 'w') as file:
                json.dump(current_years, file, indent=4)
            
            await ctx.send(f"Transition process for graduation year {grad_year-1}'-{grad_year}' completed successfully. Please check log for details.")
            await ctx.send(embed = discord.Embed(title="Transition Logs", description=log_output))
        except Exception as e:
            await ctx.send(f"An error occurred during the transition process: {e}")

    
async def setup(bot):
    await bot.add_cog(AdminMacros(bot))