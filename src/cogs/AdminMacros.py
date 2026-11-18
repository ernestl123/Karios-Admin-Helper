import asyncio
import csv
import io
import json
import os
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

import utils.channel_utils as channel_utils
import utils.csv_utils as csv_utils
import utils.role_utils as role_utils
import utils.year_utils as year_utils

def _get_roles_path() -> Path:
    root = year_utils.get_project_root()
    p = root / "roles.json"
    if p.exists():
        return p
    return Path("roles.json")

def load_role_file() -> dict:
    with open(_get_roles_path(), "r", encoding="utf-8") as f:
        return json.load(f)

role_file = load_role_file()
ROLE_DATA = role_file.get("roles", [])
BOT_ADMIN_PERM = role_file.get("role_info", {}).get("Admin_Access_Roles", [])
STAFF_ROLE_NAME = role_file.get("role_info", {}).get("Staff_Role_Name", "Staff")
VAM_ROLE_NAME = role_file.get("role_info", {}).get("Visual_Arts_and_Media_Role_Name", "VAM")

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
        self.roles_data = ROLE_DATA
        for cmd in self.__cog_commands__:
            cmd.cog = self

    async def cog_check(self, ctx):
        allowed_roles = set(BOT_ADMIN_PERM)
        author_roles = getattr(ctx.author, "roles", [])
        return any(role.name in allowed_roles for role in author_roles)

    async def _prompt_yes_no(self, ctx, prompt_text: str, timeout: float = 30.0) -> Optional[bool]:
        """Prompts the user with a yes/no question and returns True for yes, False for no, None on timeout."""
        await ctx.send(prompt_text)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            event = await self.bot.wait_for('message', check=check, timeout=timeout)
            return event.content.lower() == 'yes'
        except asyncio.TimeoutError:
            return None

    @commands.command(pass_context=True, help="Assigns a role to a member in the server.\nUsage: giveRole \"role_name\" \"member_name\"")
    async def giveRole(self, ctx, role_name: str, member_name: str):
        """
        Assigns a role to a member in the server.

        Args:
            ctx: The context of the command.
            role_name (str): The name of the role to assign.
            member_name (str): The name of the member to whom the role will be assigned.
        """
        try:
            await role_utils.give_role(ctx, role_name, member_name)
            await ctx.send(f"Role '{role_name}' successfully assigned to '{member_name}'.")
        except ValueError as e:
            await ctx.send(f"Error: {e}")

    @commands.command(pass_context=True, hidden=True)
    async def giveStaff(self, ctx, member: discord.Member):
        """
        Assigns the 'Staff' role to a member in the server.

        Args:
            ctx: The context of the command.
            member (discord.Member): The member to whom the 'Staff' role will be assigned.
        """
        try:
            await role_utils.give_role(ctx, member, STAFF_ROLE_NAME)
            await ctx.send(f"Successfully assigned the '{STAFF_ROLE_NAME}' role to {member.mention}.")
        except ValueError as e:
            await ctx.send(f"Error: {e}")

    @commands.command(pass_context=True, help="Onboards a new staff member by assigning the 'Staff' role and any additional specified roles.\nUsage: onboardStaff @member role1 role2 ...")
    async def onboardStaff(self, ctx, member: discord.Member, *roles: str):
        """
        Onboards a new staff member by assigning the 'Staff' role and sending them a welcome message.

        Args:
            ctx: The context of the command.
            member (discord.Member): The member to onboard.
            *roles (str): The roles to assign to the member separated by spaces.
        """
        try:
            await role_utils.give_role(ctx, member, STAFF_ROLE_NAME)
        except ValueError as e:
            await ctx.send(f"Error assigning '{STAFF_ROLE_NAME}' role: {e}. Manual assignment required.")

        all_assigned = []
        for role in roles:
            norm_role = "VAM" if role.lower() == "vam" else role
            # Assign the ministry role itself
            try:
                await role_utils.give_role(ctx, member, norm_role)
                all_assigned.append(norm_role)
            except ValueError as e:
                await ctx.send(f"Error assigning role '{norm_role}': {e}. Manual assignment required.")

            # Assign the additional '{Ministry name} Staff' role
            staff_role_name = norm_role if norm_role.endswith(" Staff") else f"{norm_role} Staff"
            if staff_role_name != norm_role:
                try:
                    await role_utils.give_role(ctx, member, staff_role_name)
                    all_assigned.append(staff_role_name)
                except ValueError as e:
                    await ctx.send(f"Error assigning role '{staff_role_name}': {e}. Manual assignment required.")

        assigned_str = ", ".join(all_assigned) if all_assigned else "none"
        await ctx.send(f"User {member.mention} has been onboarded with the '{STAFF_ROLE_NAME}' role and the following additional roles: {assigned_str}.")

    @commands.command(pass_context=True, help="Offboards a staff member by removing the 'Staff' role and any additional specified roles.\nUsage: offboardStaff @member")
    async def offboardStaff(self, ctx, member: discord.Member, notify_staff_channel: bool = True):
        """
        Offboards a staff member by removing the 'Staff' role and sending them a farewell message.

        Args:
            ctx: The context of the command.
            member (discord.Member): The member to offboard.
            notify_staff_channel (bool): Whether to notify the staff channel.
        """
        try:
            await role_utils.remove_role(ctx, member, STAFF_ROLE_NAME)
            await ctx.send(f"User {member.mention} has been offboarded and the '{STAFF_ROLE_NAME}' role has been removed.")
        except ValueError as e:
            await ctx.send(f"Error removing '{STAFF_ROLE_NAME}' role: {e}")

        removed_roles = [STAFF_ROLE_NAME]
        for role in list(member.roles):
            is_ministry = role.name in self.roles_data
            is_ministry_staff = role.name.endswith(" Staff") and role.name[:-6] in self.roles_data
            if is_ministry or is_ministry_staff:
                try:
                    await role_utils.remove_role(ctx, member, role.name)
                    removed_roles.append(role.name)
                except ValueError as e:
                    await ctx.send(f"Error removing role '{role.name}': {e}")

        if notify_staff_channel:
            staff_channel = discord.utils.get(ctx.guild.text_channels, name="staff")
            if staff_channel:
                await staff_channel.send(f"Goodbye forever {member.mention}. Thank you for your service 🫡. Hopefully most of us will miss you!")
            else:
                await ctx.send("Staff channel not found. Please create a channel named 'staff' to receive notifications about offboarding.")

        await ctx.send(f"User {member.mention} has been offboarded and the following roles have been removed: {', '.join(removed_roles)}.")

    @commands.command(pass_context=True, help="Updates the leadership information based on a CSV file.\nUsage: updateLeadership")
    async def updateLeadership(self, ctx):
        """
        Imports member data from a CSV file attached to the command message.
        The CSV file should have the following columns: Name, Teams.

        Args:
            ctx: The context of the command.
        """
        if not ctx.message.attachments:
            return await ctx.send("Please attach a CSV file to the message.")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".csv"):
            return await ctx.send("Please attach a valid CSV file.")

        await ctx.send("Processing the CSV file. This may take a moment...")
        try:
            file_bytes = await attachment.read()
            csv_text = file_bytes.decode('utf-8')
            rows = list(csv.DictReader(io.StringIO(csv_text)))
            error_out, success_out = await csv_utils.mass_migrate_csv(rows, ctx.guild)

            for output in [error_out, success_out]:
                if not output:
                    continue
                if len(output) > 4000:
                    with open("migration_output.txt", "w", encoding="utf-8") as f:
                        f.write(output)
                    await ctx.send("The output was too long, so it has been sent as a file.", file=discord.File("migration_output.txt"))
                    if os.path.exists("migration_output.txt"):
                        os.remove("migration_output.txt")
                else:
                    await ctx.send(embed=discord.Embed(description=output))

            with open('current_leadership.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Name', 'Teams']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        except Exception as e:
            await ctx.send(f"An error occurred while processing the CSV file: {e}")

    @commands.command(pass_context=True, help="Assigns leadership roles to members based on a CSV file.\nUsage: assignLeadership")
    async def assignLeadership(self, ctx):
        """
        Assigns roles to members based on a CSV file attached to the command message.
        The CSV file should have two columns: role name and member name.

        Args:
            ctx: The context of the command.
        """
        if not ctx.message.attachments:
            return await ctx.send("Please attach a CSV file to the message.")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".csv"):
            return await ctx.send("Please attach a valid CSV file.")

        try:
            csv_data_bytes = await attachment.read()
            csv_data_str = csv_data_bytes.decode('utf-8')
            csv_file = io.StringIO(csv_data_str)
            raw_reader = list(csv.reader(csv_file))

            if not raw_reader:
                return await ctx.send("The attached CSV file is empty.")

            # Skip header row
            rows = raw_reader[1:]
            total_rows = len(rows)
            rows_processed = 0
            error_str = ""

            for row in rows:
                if not row or len(row) < 2:
                    continue
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
                        error_str += f"ERROR: Member '{member_name}' not found for role assignment: {role_name}\n"
                else:
                    error_str += f"ERROR: Role '{role_name}' not found when assigning to '{member_name}'\n"

            if error_str:
                await ctx.send(embed=discord.Embed(description=error_str, color=discord.Color.red()))

            await ctx.send(f"Successfully processed {rows_processed}/{total_rows} rows from the CSV file.")

        except Exception as e:
            await ctx.send(f"An error occurred while processing the CSV file: {e}")

    def get_role_by_name(self, ctx, role_name: str):
        """Helper function to get a role by its name."""
        return discord.utils.get(ctx.guild.roles, name=role_name)

    def get_user_case_insensitive(self, ctx, search_name: str):
        """
        Retrieves a user by their name, display name, or nickname case-insensitively.
        Returns None if no matching user is found.
        """
        guild = ctx.guild
        search_lower = search_name.strip().lower()
        for m in guild.members:
            if m.name and m.name.lower() == search_lower:
                return m
            if m.display_name and m.display_name.lower() == search_lower:
                return m
            if m.nick and m.nick.lower() == search_lower:
                return m
        return None

    @commands.command(pass_context=True, help="Transitions a channel to the archived category.\nUsage: transitionChannel \"channel_name\" grad_year")
    async def transitionChannel(self, ctx, channel_name: str, grad_year: int):
        try:
            await channel_utils.transition_channel(ctx, channel_name, grad_year)
            await ctx.send(f"Old channel '{channel_name}' retired to Archived category and new copy created.")
        except Exception as e:
            await ctx.send(f"Failed to process channel '{channel_name}': {e}")

    @commands.command(pass_context=True, help="Retires a channel to the archived category.\nUsage: retireChannel \"channel_name\" grad_year")
    async def retireChannel(self, ctx, channel: discord.TextChannel = None, grad_year: int = -1):
        if not channel:
            return await ctx.send(f"Channel '{channel}' not found in the server.")
        try:
            await channel_utils.retire_channel(channel, grad_year)
            await ctx.send(f"Channel '{channel.name}' retired to Archived category.")
        except Exception as e:
            await ctx.send(f"Failed to retire channel '{channel.name}': {e}")

    @commands.command(pass_context=True, help="Deletes a channel from the server.\nUsage: deleteChannel \"channel_name\"")
    async def deleteChannel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            return await ctx.send(f"Channel '{channel}' not found in the server.")

        prompt = f"Are you sure you want to delete the channel '{channel.name}'? Type 'yes' to confirm or 'no' to cancel."
        confirmed = await self._prompt_yes_no(ctx, prompt, timeout=30.0)

        if confirmed is None:
            await ctx.send("Channel deletion timed out.")
        elif not confirmed:
            await ctx.send("Channel deletion cancelled.")
        else:
            try:
                await channel_utils.delete_channel(channel)
                await ctx.send(f"Channel '{channel.name}' deleted.")
            except discord.Forbidden:
                await ctx.send(f"Bot does not have permission to delete channel '{channel.name}'.")
            except Exception as e:
                await ctx.send(f"Failed to delete channel '{channel.name}': {e}")

    @commands.command(pass_context=True, hidden=True)
    async def getYears(self, ctx):
        """Displays the current graduation years for each class in the server."""
        try:
            current_years = year_utils.load_current_years()
            years_info = "\n".join([f"**{class_name}**: {year}" for class_name, year in current_years.items()])
            await ctx.send(embed=discord.Embed(title="Current Graduation Years", description=years_info, color=discord.Color.blue()))
        except Exception as e:
            await ctx.send(f"An error occurred while retrieving graduation years: {e}")

    @commands.command(pass_context=True, hidden=True)
    async def setYears(self, ctx, year_name: str, year_number: int):
        """
        Updates the graduation year for a specific class in the server.

        Args:
            ctx: The context of the command.
            year_name (str): The name of the class (Freshman, Sophomore, Junior, Senior).
            year_number (int): The new graduation year to set for the specified class.
        """
        try:
            normalized_name = year_name.capitalize()
            current_years = year_utils.update_class_year(normalized_name, year_number)
            await ctx.send(f"Updated graduation year for **{normalized_name}** to **{year_number}**.")
        except ValueError as ve:
            await ctx.send(str(ve))
        except Exception as e:
            await ctx.send(f"An error occurred while updating graduation years: {e}")

    @commands.command(pass_context=True, hidden=True)
    async def transitionMinistry(self, ctx, ministry: str, grad_year: int):
        """
        Transitions a ministry role and its associated channel to a new graduation year.

        Args:
            ctx: The context of the command.
            ministry (str): The name of the ministry role to transition.
            grad_year (int): The last two digits of the graduation year to transition to.
        """
        try:
            role_obj = self.get_role_by_name(ctx, ministry)
            if not role_obj:
                await ctx.send(f"Role '{ministry}' not found in the server.")
                return

            replaced_role = await role_utils.transition_role(role_obj, grad_year)

            if ministry.upper() == "VAM":
                channel_name = "visual-arts-and-media"
            elif ministry.lower() == "prayer":
                channel_name = "prayer-team"
            else:
                channel_name = ministry.replace(" ", "-").lower()

            old_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if not old_channel:
                old_channel = discord.utils.get(ctx.guild.channels, name=f"{channel_name}-team")
            if not old_channel:
                await ctx.send(f"Channel '{channel_name}' not found in the server. Cannot archive.")
                return

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                replaced_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            await channel_utils.transition_channel(old_channel, grad_year, overwrites)

            await ctx.send(f"Successfully transitioned ministry '{ministry}' and its associated channel to graduation year '{grad_year}'.")
        except Exception as e:
            await ctx.send(f"An error occurred during the transition process for ministry '{ministry}': {e}")

    @commands.command(pass_context=True, hidden=True)
    async def transition(self, ctx, grad_year: int):
        """
        A mass script to transition all roles and channels for a given graduation year.

        Args:
            ctx: The context of the command.
            grad_year (int): The last two digits of the graduation year to transition.
        """
        if len(str(abs(grad_year))) != 2:
            await ctx.send(f"Invalid graduation year '{grad_year}'. Please provide the last two digits of the year (e.g., 26 for 2026).")
            return

        channel_count = ctx.guild.text_channels
        if len(channel_count) > 40:
            await ctx.send(f"Warning: The server has {len(channel_count)} channels. Please delete some channels before running the transition to avoid hitting Discord's channel limit.")
            return

        try:
            log_output = "---TRANSITIONING ROLES---\n"

            for role_name in ROLE_DATA:
                lookup_name = "VAM" if role_name == "Visual Arts and Media" else role_name
                role_obj = self.get_role_by_name(ctx, lookup_name)

                try:
                    if role_obj:
                        replaced_role = await role_utils.transition_role(role_obj, grad_year)
                    else:
                        log_output += f"ERROR: Role not found: {lookup_name}\n"
                        continue

                    if lookup_name == "Prayer":
                        channel_name = "prayer-team"
                    else:
                        channel_name = lookup_name.replace(" ", "-").lower()

                    old_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                    if not old_channel:
                        log_output += f"ERROR: Channel '{channel_name}' not found in the server. Cannot archive.\n"
                        continue

                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        replaced_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                    await channel_utils.transition_channel(old_channel, grad_year, overwrites)
                    log_output += f"SUCCESS: Moved channel '{lookup_name}' to archive category\n"

                except discord.Forbidden:
                    log_output += f"ERROR: Failed to edit role '{lookup_name}'. Check permissions.\n"
                    continue

            log_output += "\n---DELETING SPECIAL EVENTS & SOCIAL CHANNELS---\n"
            special_events_category = discord.utils.get(ctx.guild.categories, name="Special Events & Socials")
            if special_events_category:
                for channel in list(special_events_category.channels):
                    await channel_utils.delete_channel(channel)
                    log_output += f"SUCCESS: Deleted channel '{channel.name}' from the server.\n"
            else:
                log_output += "INFO: 'Special Events & Socials' category not found. Skipping channel deletion.\n"

            # Update current years
            current_years = year_utils.calculate_transition_years(grad_year)
            year_utils.save_current_years(current_years)

            log_output += "\n---ARCHIVING GRADUATING CLASS CHANNEL---\n"
            grad_year_channel = discord.utils.get(ctx.guild.channels, name=f"co-20{grad_year}")
            if grad_year_channel:
                await channel_utils.retire_channel(grad_year_channel, grad_year)
                log_output += f"SUCCESS: Moved channel '{grad_year_channel.name}' to archive category. Byeeee\n"

            log_output += "\n---CREATING NEW CLASS ROLES AND CHANNELS---\n"
            for year_int in current_years.values():
                class_role_name = year_utils.format_class_role_name(year_int)
                class_role = discord.utils.get(ctx.guild.roles, name=class_role_name)
                if not class_role:
                    class_role = await ctx.guild.create_role(
                        name=class_role_name,
                        color=discord.Color.default(),
                        reason=f"Creating new class role for graduation year '{year_int}'"
                    )
                    print(f"Created new role '{class_role_name}' for graduation year '{year_int}'.")
                    log_output += f"SUCCESS: Created new role '{class_role_name}' for graduation year '{year_int}'.\n"
                else:
                    log_output += f"INFO: Role '{class_role_name}' already exists. Skipping creation.\n"

                co_channel_name = year_utils.format_class_channel_name(year_int)
                co_channel = discord.utils.get(ctx.guild.channels, name=co_channel_name)

                if not co_channel:
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        class_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                    class_chat_category = discord.utils.get(ctx.guild.categories, name="Class Chat")
                    if class_chat_category:
                        await ctx.guild.create_text_channel(name=co_channel_name, category=class_chat_category, overwrites=overwrites)
                        log_output += f"SUCCESS: Created new channel '{co_channel_name}' in Class Chat category.\n"
                    else:
                        log_output += "ERROR: Class Chat category not found. Cannot create college class channel. Please create the category first.\n"
                else:
                    log_output += f"INFO: Channel '{co_channel_name}' already exists. Skipping creation. We gucci\n"

            await ctx.send(f"Transition process for graduation year {grad_year-1}'-{grad_year}' completed successfully. Please check log for details.")
            await ctx.send(embed=discord.Embed(title="Transition Logs", description=log_output))
        except Exception as e:
            await ctx.send(f"An error occurred during the transition process: {e}")

    @commands.command(pass_context=True, aliases=['approve', 'approveleader', 'al'], help="Approves a member as a leader and assigns them the 'Leadership' role along with specified ministry roles.\nUsage: approveLeader \"username or nickname\" ministry1 ministry2 ...")
    async def approveLeader(self, ctx, member: discord.Member, *ministries: str):
        """
        Approves a member as a leader by assigning them the 'Leadership' role.

        Args:
            ctx: The context of the command.
            member (discord.Member): The member to approve as a leader.
            ministries (str): The ministries the member will lead.
        """
        m_list = ["VAM" if m.lower() == "vam" else m.capitalize() for m in ministries]

        err_str = ""
        for m in m_list:
            if m.upper() != "VAM" and m not in ROLE_DATA:
                err_str += f"ERROR: Ministry '{m}' not found in the server. Please check the ministry name and try again.\n"

        if err_str:
            embed = discord.Embed(title="Error", description=err_str, color=discord.Color.red())
            embed.set_footer(text="Note: For Visual Arts and Media, please use 'VAM' as the ministry name.")
            return await ctx.send(embed=embed)

        prompt = f"Confirmation: Are you sure you want to approve {member.mention} as a leader for the following ministries:\n{m_list}\nType 'yes' to confirm or 'no' to cancel."
        confirmed = await self._prompt_yes_no(ctx, prompt, timeout=30.0)

        if confirmed is None:
            return await ctx.send(f"Approval process for {member.mention} has timed out. Please try again.")
        elif not confirmed:
            return await ctx.send(f"Approval process for {member.mention} has been cancelled.")

        await ctx.send(f"Proceeding with the approval process for {member.mention}.")

        leadership_role = discord.utils.get(ctx.guild.roles, name="Leadership")
        if leadership_role:
            await member.add_roles(leadership_role)
            await ctx.send(f"Successfully approved {member.mention} as a leader and assigned the 'Leadership' role.")
        else:
            await ctx.send("ERROR: 'Leadership' role not found in the server. Please create the role and try again.")

        mention_str = ""
        for ministry in m_list:
            role_obj = discord.utils.get(ctx.guild.roles, name=ministry)
            if role_obj:
                await member.add_roles(role_obj)
                await ctx.send(f"Successfully assigned the '{ministry}' role to {member.mention}.")
            else:
                await ctx.send(f"ERROR: Role '{ministry}' not found in the server. Please create the role and try again.")

            staff_role = discord.utils.get(ctx.guild.roles, name=f"{ministry} Staff")
            if staff_role:
                mention_str += f"{staff_role.mention} "
            elif role_obj:
                mention_str += f"{role_obj.mention} "

        staff_channel = discord.utils.get(ctx.guild.text_channels, name="new-leaders-notifications")
        if staff_channel:
            embed = discord.Embed(
                title="New Leader Approved",
                description=f"{member.mention} has been approved as a leader for the following ministries: \n{', '.join(m_list)}.",
                color=discord.Color.green()
            )
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text="Staff in charge of these teams please react with any emoji to acknowledge this notification.")
            await staff_channel.send(content=f"{mention_str}".strip(), embed=embed)
        else:
            await ctx.send("ERROR: 'new-leaders-notifications' channel not found in the server. Please create the channel and try again.")

async def setup(bot):
    await bot.add_cog(AdminMacros(bot))
