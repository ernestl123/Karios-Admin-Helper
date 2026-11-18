import discord
from typing import Any, Dict, Optional

async def retire_channel(old_channel: discord.TextChannel, grad_year: int = -1) -> bool:
    """
    Renames a channel to indicate that it is retired for a specific graduation year and
    moves it to the 'Archived' category.

    Args:
        old_channel (discord.TextChannel): The channel to retire.
        grad_year (int): The graduation year to append to the channel name (-1 for generic '-archived').

    Returns:
        bool: True if channel was successfully retired.
    """
    archive_category = discord.utils.get(old_channel.guild.categories, name="Archived")
    channel_name = old_channel.name
    if grad_year == -1:
        new_channel_name = f"{channel_name}-archived"
    else:
        new_channel_name = f"{channel_name}-{grad_year}"

    try:
        kwargs = {
            "name": new_channel_name,
            "reason": f"Moving channel to archive for graduation year {grad_year}"
        }
        if archive_category:
            kwargs["category"] = archive_category
            kwargs["sync_permissions"] = True

        await old_channel.edit(**kwargs)
        print(f"Moved channel '{channel_name}' to archive category and renamed it to '{new_channel_name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to retire channel '{channel_name}': {e}")

async def duplicate_channel(old_channel: discord.TextChannel, overwrites: Optional[Dict[Any, Any]] = None) -> discord.TextChannel:
    """
    Duplicates a channel with its existing name, category, and specified permission overwrites.

    Args:
        old_channel (discord.TextChannel): The channel to duplicate.
        overwrites (dict, optional): Permission overwrites for the new channel.

    Returns:
        discord.TextChannel: The newly created channel.
    """
    guild = old_channel.guild
    category = old_channel.category

    try:
        channel = await guild.create_text_channel(
            name=old_channel.name,
            category=category,
            overwrites=overwrites
        )
        return channel
    except discord.Forbidden:
        category_name = category.name if category else "None"
        raise ValueError(f"Bot does not have permission to create channel '{old_channel.name}' in category '{category_name}'.")
    except Exception as e:
        raise ValueError(f"Failed to duplicate channel '{old_channel.name}': {e}")

async def transition_channel(
    target: Any,
    grad_year_or_name: Any,
    overwrites_or_grad: Optional[Any] = None,
    overwrites: Optional[Dict[Any, Any]] = None
) -> discord.TextChannel:
    """
    Transitions a channel to a new graduation year by retiring the old channel and creating a new copy.
    Supports both invocations:
    1. transition_channel(channel: discord.TextChannel, grad_year: int, overwrites: dict = None)
    2. transition_channel(ctx, channel_name: str, grad_year: int, overwrites: dict = None)

    Returns:
        discord.TextChannel: The newly created duplicate channel.
    """
    # Duck typing: Check if target is a channel object
    if hasattr(target, 'category') and hasattr(target, 'edit') and hasattr(target, 'guild'):
        channel = target
        grad_year = int(grad_year_or_name)
        perms = overwrites_or_grad if isinstance(overwrites_or_grad, dict) else overwrites
    else:
        guild = getattr(target, 'guild', None)
        if not guild:
            raise ValueError("Invalid target provided to transition_channel.")
        channel_name = str(grad_year_or_name)
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            raise ValueError(f"Channel '{channel_name}' not found in guild '{guild.name}'.")
        grad_year = int(overwrites_or_grad)
        perms = overwrites

    new_channel = await duplicate_channel(channel, perms)
    await retire_channel(channel, grad_year)
    return new_channel

async def delete_channel(channel: discord.TextChannel) -> bool:
    """
    Deletes a channel.

    Args:
        channel (discord.TextChannel): The channel to delete.

    Returns:
        bool: True if deletion succeeded.
    """
    try:
        channel_name = channel.name
        await channel.delete(reason="Deleting channel as per request of admin.")
        print(f"Deleted channel '{channel_name}'.")
        return True
    except discord.Forbidden:
        raise ValueError(f"Bot does not have permission to delete channel '{channel.name}'.")
    except Exception as e:
        raise ValueError(f"Failed to delete channel '{channel.name}': {e}")
