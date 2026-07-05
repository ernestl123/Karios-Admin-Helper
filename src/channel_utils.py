import discord

async def retire_channel(old_channel: discord.TextChannel, grad_year: int):
    """
    Renames a channel to indicate that it is retired for a specific graduation year and
    move it to the "Archived" category.
    Args:
        old_channel (discord.TextChannel): The channel to rename.
        grad_year (int): The graduation year to append to the channel name.
    """
    archive_category = discord.utils.get(old_channel.guild.categories, name="Archived")

    channel_name = old_channel.name
    if grad_year == -1:
        new_channel_name = f"{channel_name}-archived"
    else:
        new_channel_name = f"{channel_name}-{grad_year}"
    await old_channel.edit(sync_permissions=True, category=archive_category, name=new_channel_name, reason=f"Moving channel to archive for graduation year {grad_year}")
    print(f"Moved channel '{channel_name}' to archive category and renamed it to '{new_channel_name}'.")

async def duplicate_channel(old_channel: discord.TextChannel, overwrites : dict):
    """
    Duplicates a channel with a new name and copies its permissions.

    Args:
        channel (discord.TextChannel): The channel to duplicate.

    Returns:
        discord.TextChannel: The newly created duplicated channel.
    """
    guild = old_channel.guild
    category = old_channel.category
    if not category:
        raise ValueError("Channel must have a category to recreate it.")
    
    try:
        channel = await guild.create_text_channel(
            name=old_channel.name, 
            category=category,
            overwrites=overwrites
        )
        return channel
    except discord.Forbidden:
        raise ValueError(f"Bot does not have permission to create channel '{old_channel.name}' in category '{category.name}'.")

async def transition_channel(channel: discord.TextChannel, grad_year: int, overwrites : dict):
    """
    Transitions a channel to a new graduation year by retiring the old channel and creating a new one.

    Args:
        channel (discord.TextChannel): The channel to transition.
        grad_year (int): The graduation year to append to the new channel name.
        overwrites (dict): The permission overwrites for the new channel(Should put the new role replacement in here).
    """
    await duplicate_channel(channel, overwrites)
    await retire_channel(channel, grad_year)
    return

async def delete_channel(channel: discord.TextChannel):
    """
    Deletes a channel.

    Args:
        channel (discord.TextChannel): The channel to delete.
    """
    try:
        await channel.delete(reason="Deleting channel as per request of admin.")
        print(f"Deleted channel '{channel.name}'.")
    except discord.Forbidden:
        raise ValueError(f"Bot does not have permission to delete channel '{channel.name}'.")