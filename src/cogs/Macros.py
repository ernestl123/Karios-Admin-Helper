import io
import discord
from discord.ext import commands
from discord.ext.commands import has_role
import asyncio
import os
import random
import json
import csv


class Macros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
    
    @commands.command(pass_context = True)
    @commands.has_any_role("Admin Staff", "Pastor", "Shadow Admin")
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
            # next(reader)  # Assuming the first row is the header
            print(next(reader))

            rows_processed = 0
            total_rows = 53

            role_names = []
            # total_rows = sum(1 for _ in csv_file)  # Count total rows for progress tracking
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
                        await ctx.send(f"ERROR: Member '{member_name}' not found when for role assignment: " + role_name)
                else:
                    print(f"Role '{role_name}' not found.")

            await ctx.send(f"Successfully processed {rows_processed}/{total_rows} rows from the CSV file.")

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
            if search_name_lower in member.name.lower() or (member.display_name and  search_name_lower in member.display_name.lower()):
                return member
        
        return None

    @commands.command(pass_context=True)
    @commands.has_any_role("Admin Staff", "Pastor", "Shadow Admin")
    async def transition_channel(self, ctx, grad_year : int, channel_name : str):
        archive_category = discord.utils.get(ctx.guild.categories, name="Archived")
        if not archive_category:
            return await ctx.send("Archive category not found.")

        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if not channel:
            return await ctx.send(f"Channel '{channel_name}' not found in the server.")

        new_channel_name = f"{channel_name}-{grad_year}"
        try:
            await channel.edit(sync_permissions=True, category=archive_category, name=new_channel_name, reason=f"Moving channel to archive for graduation year {grad_year}")
            await ctx.send(f"Moved channel '{channel_name}' to archive category and renamed it to '{new_channel_name}'.")
        except discord.Forbidden:
            await ctx.send(f"Failed to move channel '{channel_name}'. Check permissions.")

    @commands.command(pass_context=True)
    @commands.has_any_role("Admin Staff", "Pastor", "Shadow Admin")
    async def transition(self, ctx, grad_year : int):
        with open('roles.json', 'r') as file:
            roles_data = json.load(file)
        
        archive_category = discord.utils.get(ctx.guild.categories, name="Archived")

        roles = roles_data['roles']
        for role_name in roles:
            role_obj = self.get_role_by_name(ctx, role_name)

            try:
                if role_obj:
                    #rename role
                    new_role_name = role_name +  f" \'{grad_year}"
                    await role_obj.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year \'{grad_year}")
                    print(f"Edited role '{role_name}' to '{new_role_name}'.")
                else:
                    print(f"Role not found: {role_name}")

                #move channel to archive category
                if role_name == "Prayer":
                    channel_name = "prayer-team"
                else:
                    channel_name = role_name.replace(" ", "-").lower()  # Replace spaces with hyphens for channel name

                old_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                new_channel_name = channel_name + f"-{grad_year}"
                if not old_channel:
                    await ctx.send(f"Channel '{channel_name}' not found in the server.")
                    continue
                
                await old_channel.edit(sync_permissions = True, category=archive_category, name = new_channel_name, reason=f"Moving channel '{role_name}' to archive for graduation year {grad_year}")
                print(f"Moved channel '{role_name}' to archive category and renamed it to '{new_channel_name}'.")

            except discord.Forbidden:
                print(f"Failed to edit role '{role_name}'. Check permissions.")
                continue

        grad_class_role = self.get_role_by_name(ctx, f"Class of '{grad_year}")
        fellowship_role = self.get_role_by_name(ctx, "Fellowship")
        if not grad_class_role:
            await ctx.send(f"Role 'Class of {grad_year}' not found in the server.")
            return
        
        
        members_with_role = [member for member in ctx.guild.members if grad_class_role in member.roles]
        for member in members_with_role:
            try:
                await member.remove_roles(fellowship_role, reason=f"Graduating year '{grad_year} removed from fellowship role.")
                print(f"Removed role '{fellowship_role.name}' from member '{member.display_name}'.")
            except discord.Forbidden:
                await ctx.send(f"Failed to remove role '{fellowship_role.name}' from members. Check permissions.")
                
        await ctx.send(f"Transition process for graduation year '{grad_year}' completed successfully.")

async def setup(bot):
    await bot.add_cog(Macros(bot))