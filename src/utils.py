import discord

async def graduate_channel(ctx, channel_name, grad_year):
    """
    Retires a channel by moving it to the archive category and renaming it with the graduation year.

    Args:
        ctx: The context of the command.
        channel_name (str): The name of the channel to retire.
        grad_year (int): The graduation year to append to the channel name.
    
    Returns:
        bool: True if the channel was successfully retired and recreated, False otherwise.
    """
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if not channel:
        return None
    try:
        await recreate_channel(ctx, channel)
        
    except ValueError as e:
        print(f"Error recreating channel: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
    try:
        await retire_channel(channel, grad_year)
        return True
    except Exception as e:
        print(f"Error retiring channel: {e}")
        return None
    
async def retire_channel(channel, grad_year: int):
    """
    Moves a channel to the archive category and renames it with the graduation year.

    Args:
        channel (discord.TextChannel): The channel to retire.
        grad_year (int): The graduation year to append to the channel name.

    Returns:
        discord.TextChannel: The retired channel with the new name.
    """
    archive_category = discord.utils.get(channel.guild.categories, name="Archived")

    channel_name = channel.name
    if grad_year == -1:
        new_channel_name = f"{channel_name}-archived"
    else:
        new_channel_name = f"{channel_name}-{grad_year}"
    await channel.edit(sync_permissions=True, category=archive_category, name=new_channel_name, reason=f"Moving channel to archive for graduation year {grad_year}")
    print(f"Moved channel '{channel_name}' to archive category and renamed it to '{new_channel_name}'.")
    return channel

async def recreate_channel(ctx, old_channel):
    """
    Recreates a channel in the same category with the same name and permissions as the old channel.

    Args:
        ctx: The context of the command.
        old_channel (discord.TextChannel): The channel to recreate.
    
    Returns:
        discord.TextChannel: The newly created channel.
    """
    category = old_channel.category
    if not category:
        raise ValueError("Channel must have a category to recreate it.")
    
    try:
        channel = await ctx.guild.create_text_channel(
            name=old_channel.name, 
            category=category,
            overwrites=old_channel.overwrites
        )
        return channel
    except discord.Forbidden:
        await ctx.send(f"Failed to create channel '{old_channel.name}' in Leadership category. Check permissions.")
        return None

async def retire_role(role: discord.Role, grad_year: int):
    """
    Retires a role by renaming it with the graduation year.
    Args:
        role (discord.Role): The role to retire.
        grad_year (int): The graduation year to append to the role name.
    
    Returns:
        bool: True if the role was successfully retired, False otherwise.
    """
    new_role_name = f"{role.name} '{grad_year}"
    try:
        await role.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year '{grad_year}")
        print(f"Edited role '{role.name}' to '{new_role_name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to edit role '{role.name}': {e}")

async def copy_role(role: discord.Role):
    """
    Copies a role by creating a new role with the same name and color.
    Args:
        role (discord.Role): The role to copy.
    
    Returns:
        discord.Role: The newly created role.
    """
    try:
        new_role = await role.guild.create_role(name=role.name, color=role.color, reason=f"Copying role '{role.name}' for new year")
        return new_role
    except Exception as e:
        raise ValueError(f"Failed to copy role '{role.name}': {e}")

async def assign_role(member : discord.Member, role_name : str, guild : discord.Guild):
    """
    Assigns a role to a member by role name.
    Args:
        member (discord.Member): The member to assign the role to.
        role_name (str): The name of the role to assign.
        guild (discord.Guild): The guild where the role exists.
    
    Returns:
        bool: True if the role was successfully assigned, False otherwise.
    """
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        raise ValueError(f"Role '{role_name}' not found in guild '{guild.name}'.")
    
    try:
        await member.add_roles(role, reason=f"Assigning role '{role_name}' to member '{member.name}'")
        print(f"Assigned role '{role_name}' to member '{member.name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to assign role '{role_name}' to member '{member.name}': {e}")

async def assign_new_member(discord_member, name, school, college, grad_year, guild):
    await discord_member.edit(nick=name)

    print(f"Assigning 'Form Submitter' role to member: {discord_member.name}")
    if await assign_role(discord_member, "Fellowship", guild):
        print(f"Successfully assigned 'Fellowship' role to {discord_member.name}.")
    else:
        print(f"Failed to assign 'Fellowship' role to {discord_member.name}.")

    if school:
        if await assign_role(discord_member, school, guild):
            print(f"Successfully assigned '{school}' role to {discord_member.name}.")
        else:
            print(f"Failed to assign '{school}' role to {discord_member.name}.")
    if college:
        if await assign_role(discord_member, college, guild):
            print(f"Successfully assigned '{college}' role to {discord_member.name}.")
        else:
            print(f"Failed to assign '{college}' role to {discord_member.name}.")
    if grad_year:
        if await assign_role(discord_member, grad_year, guild):
            print(f"Successfully assigned '{grad_year}' role to {discord_member.name}.")
        else:
            print(f"Failed to assign '{grad_year}' role to {discord_member.name}.")