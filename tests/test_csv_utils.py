import csv
import pytest
from utils.csv_utils import read_csv, mass_migrate_csv
from conftest import MockRole

def test_read_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Teams\nAlice,Worship\nBob,Prayer\n", encoding="utf-8")
    rows = read_csv(str(csv_file))
    assert len(rows) == 2
    assert rows[0] == {"Name": "Alice", "Teams": "Worship"}
    assert rows[1] == {"Name": "Bob", "Teams": "Prayer"}

@pytest.mark.asyncio
async def test_mass_migrate_csv_success(mock_guild):
    # Member NormalUser has nick NormalNick
    mock_guild.roles.append(MockRole("Life Group Leader", 50))
    mock_guild.roles.append(MockRole("Worship", 51))

    rows = [
        {"Name": "NormalNick", "Teams": "Life Group, A/V"}
    ]

    error_out, success_out = await mass_migrate_csv(rows, mock_guild)
    assert error_out == ""
    assert "Assigned role 'Life Group Leader' to 'NormalNick'" in success_out
    assert "Assigned role 'Worship' to 'NormalNick'" in success_out
    assert "Assigned role 'Leadership' to 'NormalNick'" in success_out

    member = mock_guild.members[1]
    assert member.add_roles.await_count == 3

@pytest.mark.asyncio
async def test_mass_migrate_csv_missing_member(mock_guild):
    rows = [
        {"Name": "UnknownPerson", "Teams": "Prayer"}
    ]
    error_out, success_out = await mass_migrate_csv(rows, mock_guild)
    assert "Member with nickname 'UnknownPerson' not found" in error_out
    assert success_out == ""

@pytest.mark.asyncio
async def test_mass_migrate_csv_missing_role(mock_guild):
    rows = [
        {"Name": "AdminNick", "Teams": "NonexistentMinistry"}
    ]
    error_out, success_out = await mass_migrate_csv(rows, mock_guild)
    assert "Role 'NonexistentMinistry' not found" in error_out
    assert "Assigned role 'Leadership' to 'AdminNick'" in success_out
