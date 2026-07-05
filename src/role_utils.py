import discord

async def give_role(member: discord.Member, role_name: int):
    """
    Assigns a role to a member by role name.
    Args:
        member (discord.Member): The member to assign the role to.
        role_name (int): The name of the role to assign.
    
    Returns:
        bool: True if the role was successfully assigned, False otherwise.
    """
    role = discord.utils.get(member.guild.roles, name=role_name)
    if not role:
        raise ValueError(f"Role '{role_name}' not found in guild '{member.guild.name}'.")
    
    try:
        await member.add_roles(role, reason=f"Assigning role '{role_name}' to member '{member.name}'")
        print(f"Assigned role '{role_name}' to member '{member.name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to assign role '{role_name}' to member '{member.name}': {e}")
    
async def retire_role(role: discord.Role, grad_year: int):
    """
    Renames a role to indicate that it is retired for a specific graduation year and
    switch color to gray
    Args:
        role (discord.Role): The role to rename.
        grad_year (int): The last two digits of the graduation year to append to the role name.
    """
    new_role_name = f"{role.name} '{grad_year}"
    try:
        await role.edit(name=new_role_name, color=discord.Color.default(), reason=f"Transitioning role for graduation year '{grad_year}")
        print(f"Edited role '{role.name}' to '{new_role_name}'.")
        return True
    except Exception as e:
        raise ValueError(f"Failed to edit role '{role.name}': {e}")

async def duplicate_role(role: discord.Role):
    """
    Duplicates a role

    Args:
        role (discord.Role): The role to duplicate.

    Returns:
        discord.Role: The newly created duplicated role.
    """
    try:
        return await role.guild.create_role(name=role.name, color=role.color, reason=f"Copying role '{role.name}' for new year")
    except Exception as e:
        raise ValueError(f"Failed to copy role '{role.name}': {e}")

async def transition_role(role: discord.Role, grad_year: str):
    """
    Transitions a role to a new graduation year by retiring the old role and creating a new one.

    Args:
        role (discord.Role): The role to transition.
        grad_year (str): The graduation year to append to the new role name.
    """
    new_role = await duplicate_role(role)
    await retire_role(role, grad_year)
    return new_role