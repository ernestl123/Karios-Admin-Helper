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
    new_role_name = f"{role.name} '{grad_year}"
    try:
        await role.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year '{grad_year}")
        print(f"Edited role '{role.name}' to '{new_role_name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to edit role '{role.name}': {e}")

async def copy_role(role: discord.Role):
    try:
        new_role = await role.guild.create_role(name=role.name, color=role.color, reason=f"Copying role '{role.name}' for new year")
        return new_role
    except Exception as e:
        raise ValueError(f"Failed to copy role '{role.name}': {e}")
    