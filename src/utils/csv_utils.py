import csv
import discord

def read_csv(file_path: str):
    """
    Reads a CSV file and returns its contents as a list of dictionaries.

    Args:
        file_path (str): The path to the CSV file.
    """

    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]
    

async def mass_migrate_csv(reader: csv.DictReader, guild: discord.Guild):
    """
    Args:
        reader (csv.DictReader): The CSV reader object.
        guild (discord.Guild): The guild to migrate users to.

    Returns:
        str: A summary of the migration process.
    """
    output = ""

    for row in reader:
        name = row.get('Name')
        teams = row.get('Teams').split(', ') if row.get('Teams') else []

        teams.append("Leadership")
        print(f"Name: {name}, Teams: {teams}")

        member = discord.utils.find(
            lambda m: m.nick and m.nick.lower() == name.lower(), 
            guild.members
        )
        if not member:
            output += f"🛑Member with nickname '{name}' not found in guild '{guild.name}'. Manual assignment required.\n"
            continue
            
        # Assign roles to the member given each team in teams
        for team in teams:
            if team == "Life Group":
                team = "Life Group Leader"
                
            role = discord.utils.get(guild.roles, name=team)
            if not role:
                output += f"🛑Role '{team}' not found in guild '{guild.name}'. Manual assignment required.\n"
                continue
            
            try:
                await member.add_roles(role, reason=f"Assigning role '{team}' to member '{member.name}' from CSV migration")
                print(f"Assigned role '{team}' to member '{member.name}'.")
            except Exception as e:
                output += f"🛑Failed to assign role '{team}' to member. Manual assignment required for '{member.name}': {e}\n"

    return output