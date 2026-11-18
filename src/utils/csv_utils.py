import csv
from typing import Any, Iterable, List, Optional, Tuple
import discord

def read_csv(file_path: str) -> List[dict]:
    """
    Reads a CSV file and returns its contents as a list of dictionaries.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list of dict: The CSV records.
    """
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def _find_member_by_name(guild: discord.Guild, name: str) -> Optional[discord.Member]:
    """
    Finds a member in the guild matching name against nickname, display name, or username.
    """
    clean_name = name.strip().lower()
    for m in guild.members:
        if m.nick and m.nick.lower() == clean_name:
            return m
        if m.display_name and m.display_name.lower() == clean_name:
            return m
        if m.name and m.name.lower() == clean_name:
            return m
    return None

async def mass_migrate_csv(reader_or_rows: Iterable[dict], guild: discord.Guild) -> Tuple[str, str]:
    """
    Migrates users to leadership and ministry roles based on CSV data.

    Args:
        reader_or_rows: An iterable or list of dict rows with 'Name' and 'Teams' keys.
        guild (discord.Guild): The guild to migrate users in.

    Returns:
        tuple[str, str]: (error_output, success_output)
    """
    error_output = ""
    success_output = ""

    # Convert to list if it's an iterator so caller can reuse or we can safely iterate
    rows = list(reader_or_rows)

    team_aliases = {
        "Life Group": "Life Group Leader",
        "A/V": "Worship"
    }

    for row in rows:
        if not row:
            continue
        name = row.get('Name')
        if not name or not str(name).strip():
            continue

        raw_teams = row.get('Teams')
        teams = [t.strip() for t in raw_teams.split(',')] if raw_teams else []

        if "Leadership" not in teams:
            teams.append("Leadership")

        member = _find_member_by_name(guild, str(name))
        if not member:
            error_output += f"🛑Member with nickname '{name}' not found in guild '{guild.name}'. Manual assignment required.\n"
            continue

        for team in teams:
            normalized_team = team_aliases.get(team, team)
            role = discord.utils.get(guild.roles, name=normalized_team)
            if not role:
                error_output += f"🛑Role '{normalized_team}' not found in guild '{guild.name}'. Manual assignment required.\n"
                continue

            try:
                await member.add_roles(role, reason=f"Assigning role '{normalized_team}' to member '{member.name}' from CSV migration")
                success_output += f"✅Assigned role '{normalized_team}' to '{name}'.\n"
            except Exception as e:
                error_output += f"🛑Failed to assign role '{normalized_team}' to member. Manual assignment required for '{member.name}': {e}\n"

    return error_output, success_output
