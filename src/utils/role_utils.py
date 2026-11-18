import discord
from typing import Any, Optional, Tuple

def _resolve_member(guild: discord.Guild, member_or_name: Any) -> Optional[discord.Member]:
    """Helper to resolve a discord.Member from an object or name string."""
    if hasattr(member_or_name, "add_roles") and hasattr(member_or_name, "roles"):
        return member_or_name

    search = str(member_or_name).strip().lower()
    for m in guild.members:
        if m.name and m.name.lower() == search:
            return m
        if m.display_name and m.display_name.lower() == search:
            return m
        if m.nick and m.nick.lower() == search:
            return m
    return None

def _resolve_role(guild: discord.Guild, role_or_name: Any) -> Optional[discord.Role]:
    """Helper to resolve a discord.Role from an object or name string."""
    if hasattr(role_or_name, "color") and hasattr(role_or_name, "edit"):
        return role_or_name
    return discord.utils.get(guild.roles, name=str(role_or_name))

def _resolve_call_args(target: Any, arg2: Any, arg3: Optional[Any] = None) -> Tuple[Any, Any]:
    """
    Normalizes arguments for give_role / remove_role to support multiple calling conventions:
    1. (member, role_name)
    2. (ctx, member, role_name)
    3. (ctx, role_name, member_name)
    """
    # 2-argument convention: (member, role_name)
    if arg3 is None:
        member = target
        guild = getattr(member, 'guild', None)
        if not guild:
            raise ValueError("Cannot resolve guild from provided member.")
        role = _resolve_role(guild, arg2)
        if not role:
            raise ValueError(f"Role '{arg2}' not found in guild '{guild.name}'.")
        return member, role

    # 3-argument conventions: target is ctx / guild
    guild = getattr(target, 'guild', None)
    if not guild:
        raise ValueError("Cannot resolve guild from provided context/target.")

    # Convention: (ctx, member, role_name)
    if hasattr(arg2, "add_roles") and hasattr(arg2, "roles"):
        member = arg2
        role = _resolve_role(guild, arg3)
        if not role:
            raise ValueError(f"Role '{arg3}' not found in guild '{guild.name}'.")
        return member, role

    # Convention: (ctx, role_obj, member)
    if hasattr(arg3, "add_roles") and hasattr(arg3, "roles"):
        member = arg3
        role = _resolve_role(guild, arg2)
        if not role:
            raise ValueError(f"Role '{arg2}' not found in guild '{guild.name}'.")
        return member, role

    # Both are strings:
    # First try arg2 as role, arg3 as member
    role = _resolve_role(guild, arg2)
    member = _resolve_member(guild, arg3)

    if not member or not role:
        # Try alternate: arg2 as member, arg3 as role
        alt_member = _resolve_member(guild, arg2)
        alt_role = _resolve_role(guild, arg3)
        if alt_member and alt_role:
            return alt_member, alt_role

    if not member:
        raise ValueError(f"Member '{arg3}' not found in guild '{guild.name}'.")
    if not role:
        raise ValueError(f"Role '{arg2}' not found in guild '{guild.name}'.")

    return member, role

async def give_role(target: Any, role_or_name: Any, member_or_role: Optional[Any] = None) -> bool:
    """
    Assigns a role to a member. Supports multiple invocation styles:
    - give_role(member, role_name)
    - give_role(ctx, member, role_name)
    - give_role(ctx, role_name, member_name)

    Args:
        target: discord.Member or commands.Context
        role_or_name: Role name (str), discord.Role, or discord.Member
        member_or_role: Optional role or member depending on calling style.

    Returns:
        bool: True if role was successfully assigned.
    """
    member, role = _resolve_call_args(target, role_or_name, member_or_role)
    try:
        await member.add_roles(role, reason=f"Assigning role '{role.name}' to member '{member.name}'")
        print(f"Assigned role '{role.name}' to member '{member.name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to assign role '{role.name}' to member '{member.name}': {e}")

async def remove_role(target: Any, role_or_name: Any, member_or_role: Optional[Any] = None) -> bool:
    """
    Removes a role from a member. Supports multiple invocation styles:
    - remove_role(member, role_name)
    - remove_role(ctx, member, role_name)
    - remove_role(ctx, role_name, member_name)

    Args:
        target: discord.Member or commands.Context
        role_or_name: Role name (str), discord.Role, or discord.Member
        member_or_role: Optional role or member depending on calling style.

    Returns:
        bool: True if role was successfully removed.
    """
    member, role = _resolve_call_args(target, role_or_name, member_or_role)
    try:
        await member.remove_roles(role, reason=f"Removing role '{role.name}' from member '{member.name}'")
        print(f"Removed role '{role.name}' from member '{member.name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to remove role '{role.name}' from member '{member.name}': {e}")

async def retire_role(role: discord.Role, grad_year: Any) -> bool:
    """
    Renames a role to indicate that it is retired for a specific graduation year and
    switches color to default (gray).

    Args:
        role (discord.Role): The role to rename.
        grad_year: The last two digits of the graduation year to append.

    Returns:
        bool: True if role was successfully edited.
    """
    new_role_name = f"{role.name} '{grad_year}"
    try:
        await role.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year '{grad_year}'")
        print(f"Edited role '{role.name}' to '{new_role_name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to edit role '{role.name}': {e}")

async def duplicate_role(role: discord.Role) -> discord.Role:
    """
    Duplicates a role with its current color.

    Args:
        role (discord.Role): The role to duplicate.

    Returns:
        discord.Role: The newly created duplicated role.
    """
    try:
        return await role.guild.create_role(name=role.name, color=role.color, reason=f"Copying role '{role.name}' for new year")
    except Exception as e:
        raise ValueError(f"Failed to copy role '{role.name}': {e}")

async def transition_role(role: discord.Role, grad_year: Any) -> discord.Role:
    """
    Transitions a role to a new graduation year by retiring the old role and creating a new one.

    Args:
        role (discord.Role): The role to transition.
        grad_year: The graduation year to append to the retired role name.

    Returns:
        discord.Role: The newly created role.
    """
    new_role = await duplicate_role(role)
    await retire_role(role, grad_year)
    return new_role
