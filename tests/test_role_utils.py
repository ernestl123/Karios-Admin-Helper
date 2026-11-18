import discord
import pytest
from unittest.mock import AsyncMock
from utils.role_utils import (
    give_role,
    remove_role,
    retire_role,
    duplicate_role,
    transition_role
)

@pytest.mark.asyncio
async def test_give_role_member_convention(mock_guild):
    member = mock_guild.members[1] # NormalUser
    res = await give_role(member, "Staff")
    assert res is True
    member.add_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_give_role_ctx_member_role_convention(mock_ctx, mock_guild):
    member = mock_guild.members[1]
    res = await give_role(mock_ctx, member, "Staff")
    assert res is True
    member.add_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_give_role_ctx_role_member_name_convention(mock_ctx, mock_guild):
    res = await give_role(mock_ctx, "Staff", "NormalUser")
    assert res is True
    mock_guild.members[1].add_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_give_role_nonexistent_role(mock_guild):
    member = mock_guild.members[1]
    with pytest.raises(ValueError, match="Role 'NonexistentRole' not found"):
        await give_role(member, "NonexistentRole")

@pytest.mark.asyncio
async def test_give_role_nonexistent_member(mock_ctx):
    with pytest.raises(ValueError, match="Member 'Ghost' not found"):
        await give_role(mock_ctx, "Staff", "Ghost")

@pytest.mark.asyncio
async def test_give_role_add_roles_exception(mock_guild):
    member = mock_guild.members[1]
    member.add_roles = AsyncMock(side_effect=discord.Forbidden(AsyncMock(), "Forbidden"))
    with pytest.raises(ValueError, match="Failed to assign role"):
        await give_role(member, "Staff")

@pytest.mark.asyncio
async def test_remove_role_member_convention(mock_guild):
    member = mock_guild.members[0]
    res = await remove_role(member, "Admin Staff")
    assert res is True
    member.remove_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_remove_role_ctx_convention(mock_ctx, mock_guild):
    member = mock_guild.members[0]
    res = await remove_role(mock_ctx, member, "Admin Staff")
    assert res is True
    member.remove_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_remove_role_nonexistent_role(mock_guild):
    member = mock_guild.members[0]
    with pytest.raises(ValueError, match="Role 'FakeRole' not found"):
        await remove_role(member, "FakeRole")

@pytest.mark.asyncio
async def test_retire_role(mock_guild):
    role = mock_guild.roles[1] # Staff
    res = await retire_role(role, 26)
    assert res is True
    role.edit.assert_awaited_once_with(
        name="Staff '26",
        color=discord.Color.default(),
        reason="Transitioning role for graduation year '26'"
    )

@pytest.mark.asyncio
async def test_duplicate_role(mock_guild):
    role = mock_guild.roles[1]
    role.guild = mock_guild
    mock_guild.create_role = AsyncMock(return_value="new_role_obj")
    res = await duplicate_role(role)
    assert res == "new_role_obj"
    mock_guild.create_role.assert_awaited_once()

@pytest.mark.asyncio
async def test_transition_role(mock_guild):
    role = mock_guild.roles[1]
    role.guild = mock_guild
    mock_guild.create_role = AsyncMock(return_value="duplicated_role")
    new_role = await transition_role(role, 26)
    assert new_role == "duplicated_role"
    role.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_role_exception(mock_guild):
    member = mock_guild.members[0]
    member.remove_roles = AsyncMock(side_effect=Exception("Failed"))
    with pytest.raises(ValueError, match="Failed to remove role"):
        await remove_role(member, "Admin Staff")

@pytest.mark.asyncio
async def test_retire_role_exception(mock_guild):
    role = mock_guild.roles[1]
    role.edit = AsyncMock(side_effect=Exception("Edit failed"))
    with pytest.raises(ValueError, match="Failed to edit role"):
        await retire_role(role, 26)

@pytest.mark.asyncio
async def test_duplicate_role_exception(mock_guild):
    role = mock_guild.roles[1]
    mock_guild.create_role = AsyncMock(side_effect=Exception("Create failed"))
    with pytest.raises(ValueError, match="Failed to copy role"):
        await duplicate_role(role)
