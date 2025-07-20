import io
import discord
from discord.ext import commands
import asyncio
import os
import random
import json
import csv


class Macros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        
    @commands.command(pass_context = True)
    async def assign(self, ctx):
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
            next(reader)  # Assuming the first row is the header

            rows_processed = 0
            for row in reader:
                await ctx.send(f"Row: {row}")
                role_name = row[0].strip()
                member_name = row[1].strip()

                role_obj = self.get_role_by_name(ctx, role_name)
                if role_obj:
                    member = self.get_user_case_insensitive(self, ctx, member_name)

                    if member:
                        await member.add_roles(role_obj)
                        await ctx.send(f"Assigned role **{role_name}** to **{member_name}**.")
                        rows_processed += 1
                    else:
                        await ctx.send(f"Member '{member_name}' not found.")

            await ctx.send(f"Successfully processed {rows_processed} rows from the CSV file.")

        except Exception as e:
            await ctx.send(f"An error occurred while processing the CSV file: {e.with_traceback()}")

    def get_role_by_name(self, ctx, role_name : str):
        """Helper function to get a role by its name."""
        guild = ctx.guild  # Get the Guild object from the context
        return discord.utils.get(guild.roles, name=role_name)
        
    def get_user_case_insensitive(self, ctx, search_name: str):
        """
        Retrieves a user by their name (or display name) case-insensitively.
        """
        guild = ctx.guild  # Get the Guild object from the context
        search_name_lower = search_name.lower() # Convert search name to lowercase for comparison

        for member in guild.members:
            # Compare both the regular name and display name (nickname)
            if member.name.lower() == search_name_lower or (member.display_name and member.display_name.lower() == search_name_lower):
                return member
        
        return None

    @commands.command(pass_context=True)
    async def transition(self, ctx, grad_year : int):
        with open('roles.json', 'r') as file:
            roles_data = json.load(file)
        
        archive_category = discord.utils.get(ctx.guild.categories, name="Archived")

        roles = roles_data['test_roles']
        for role_name in roles:
            role_obj = self.get_role_by_name(ctx, role_name)
            if not role_obj:
                await ctx.send(f"Role '{role_name}' not found in the server.")
                continue

            try:
                #rename role
                new_role_name = role_name +  f" \'{grad_year}"
                await role_obj.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year \'{grad_year}")
                await ctx.send(f"Edited role '{role_name}' to '{new_role_name}'.")

                #move channel to archive category
                channel_name = role_name.replace(" ", "-").lower()  # Replace spaces with hyphens for channel name
                old_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                new_channel_name = role_name + f"-{grad_year}"
                if not old_channel:
                    await ctx.send(f"Channel '{role_name}' not found in the server.")
                    continue
                
                await old_channel.edit(sync_permissions = True, category=archive_category, name = new_channel_name, reason=f"Moving channel '{role_name}' to archive for graduation year {grad_year}")
                await ctx.send(f"Moved channel '{role_name}' to archive category and renamed it to '{new_channel_name}'.")

            except discord.Forbidden:
                await ctx.send(f"Failed to edit role '{role_name}'. Check permissions.")
                continue
    
    
async def setup(bot):
    await bot.add_cog(Macros(bot))