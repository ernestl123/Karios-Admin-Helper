import io
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import pytest
from cogs.AdminMacros import AdminMacros
from conftest import MockAttachment, MockMember, MockMessage, MockRole

@pytest.fixture
def cog(mock_bot):
    return AdminMacros(mock_bot)

@pytest.mark.asyncio
async def test_cog_check(cog, mock_ctx, mock_guild):
    # AdminUser has role "Admin Staff", which is in Admin_Access_Roles
    assert await cog.cog_check(mock_ctx) is True

    # User without admin role
    unauth_member = mock_guild.members[1]
    mock_ctx.author = unauth_member
    assert await cog.cog_check(mock_ctx) is False

@pytest.mark.asyncio
async def test_give_role_command(cog, mock_ctx, mock_guild):
    await cog.giveRole(mock_ctx, "Staff", "NormalUser")
    mock_ctx.send.assert_awaited()
    sent_msg = mock_ctx.send.await_args[0][0]
    assert "successfully assigned" in sent_msg
    mock_guild.members[1].add_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_give_staff_command(cog, mock_ctx, mock_guild):
    member = mock_guild.members[1]
    await cog.giveStaff(mock_ctx, member)
    mock_ctx.send.assert_awaited()
    sent_msg = mock_ctx.send.await_args[0][0]
    assert "Successfully assigned the 'Staff' role" in sent_msg
    member.add_roles.assert_awaited_once()

@pytest.mark.asyncio
async def test_onboard_staff_command(cog, mock_ctx, mock_guild):
    member = mock_guild.members[1]
    mock_guild.roles.append(MockRole("Prayer Staff", 15, guild=mock_guild))
    mock_guild.roles.append(MockRole("VAM Staff", 16, guild=mock_guild))

    await cog.onboardStaff(mock_ctx, member, "Prayer", "VAM")
    # Roles assigned: Staff, Prayer, Prayer Staff, VAM, VAM Staff (5 total)
    assert member.add_roles.await_count == 5
    mock_ctx.send.assert_awaited()
    sent_msg = mock_ctx.send.await_args[0][0]
    assert "onboarded with the 'Staff' role and the following additional roles: Prayer, Prayer Staff, VAM, VAM Staff" in sent_msg

@pytest.mark.asyncio
async def test_offboard_staff_command(cog, mock_ctx, mock_guild):
    staff_role = mock_guild.roles[1]
    prayer_role = mock_guild.roles[4]
    prayer_staff_role = MockRole("Prayer Staff", 15, guild=mock_guild)
    member = MockMember("DepartingStaff", 2001, roles=[staff_role, prayer_role, prayer_staff_role], guild=mock_guild)
    mock_guild.members.append(member)

    await cog.offboardStaff(mock_ctx, member, notify_staff_channel=True)
    staff_channel = mock_guild.channels[0]
    staff_channel.send.assert_awaited()
    assert member.remove_roles.await_count >= 2

@pytest.mark.asyncio
async def test_get_years_and_set_years(cog, mock_ctx, tmp_path):
    years_file = tmp_path / "current_years.json"
    with patch("utils.year_utils.get_default_years_path", return_value=years_file):
        await cog.getYears(mock_ctx)
        mock_ctx.send.assert_awaited()
        call_kwargs = mock_ctx.send.await_args[1]
        assert "embed" in call_kwargs

        await cog.setYears(mock_ctx, "Senior", 2030)
        sent = mock_ctx.send.await_args[0][0]
        assert "Updated graduation year for **Senior** to **2030**" in sent

@pytest.mark.asyncio
async def test_assign_leadership_command(cog, mock_ctx, mock_guild):
    csv_content = b"Role,Name\nPrayer,NormalUser\n"
    attachment = MockAttachment("leaders.csv", csv_content)
    mock_ctx.message = MockMessage(author=mock_ctx.author, channel=mock_ctx.channel, attachments=[attachment])

    await cog.assignLeadership(mock_ctx)
    mock_ctx.send.assert_awaited()
    sent_msg = mock_ctx.send.await_args[0][0]
    assert "Successfully processed 1/1 rows" in sent_msg
    mock_guild.members[1].add_roles.assert_awaited()

@pytest.mark.asyncio
async def test_update_leadership_command(cog, mock_ctx, mock_guild, tmp_path):
    csv_content = b"Name,Teams\nNormalNick,Prayer\n"
    attachment = MockAttachment("leadership.csv", csv_content)
    mock_ctx.message = MockMessage(author=mock_ctx.author, channel=mock_ctx.channel, attachments=[attachment])

    with patch("os.path.exists", return_value=False):
        await cog.updateLeadership(mock_ctx)
        mock_guild.members[1].add_roles.assert_awaited()

@pytest.mark.asyncio
async def test_delete_channel_confirmed(cog, mock_ctx, mock_guild):
    channel = mock_guild.channels[0]
    with patch.object(cog, "_prompt_yes_no", new=AsyncMock(return_value=True)):
        await cog.deleteChannel(mock_ctx, channel)
        channel.delete.assert_awaited_once()
        sent = mock_ctx.send.await_args[0][0]
        assert "deleted" in sent

@pytest.mark.asyncio
async def test_delete_channel_cancelled(cog, mock_ctx, mock_guild):
    channel = mock_guild.channels[0]
    with patch.object(cog, "_prompt_yes_no", new=AsyncMock(return_value=False)):
        await cog.deleteChannel(mock_ctx, channel)
        channel.delete.assert_not_awaited()
        sent = mock_ctx.send.await_args[0][0]
        assert "cancelled" in sent

@pytest.mark.asyncio
async def test_transition_ministry(cog, mock_ctx, mock_guild):
    mock_guild.create_text_channel = AsyncMock(return_value="new_chan")
    mock_guild.create_role = AsyncMock(return_value=MockRole("NewPrayer"))
    await cog.transitionMinistry(mock_ctx, "Prayer", 26)
    mock_ctx.send.assert_awaited()
    sent = mock_ctx.send.await_args[0][0]
    assert "Successfully transitioned ministry 'Prayer'" in sent

@pytest.mark.asyncio
async def test_approve_leader_success(cog, mock_ctx, mock_guild):
    member = mock_guild.members[1]
    prayer_staff_role = MockRole("Prayer Staff", 99, guild=mock_guild)
    mock_guild.roles.append(prayer_staff_role)

    with patch.object(cog, "_prompt_yes_no", new=AsyncMock(return_value=True)):
        await cog.approveLeader(mock_ctx, member, "Prayer")

        # Verify assigned roles: should assign 'Leadership' and 'Prayer' (not 'Prayer Staff')
        added_roles = [call[0][0] for call in member.add_roles.call_args_list]
        added_role_names = [r.name for r in added_roles]

        assert "Leadership" in added_role_names
        assert "Prayer" in added_role_names
        assert "Prayer Staff" not in added_role_names

        # The notification channel should notify and mention the staff role
        notif_chan = mock_guild.channels[1] # new-leaders-notifications
        notif_chan.send.assert_awaited_once()
        assert prayer_staff_role.mention in notif_chan.send.await_args[1]["content"]

@pytest.mark.asyncio
async def test_approve_leader_cancelled(cog, mock_ctx, mock_guild):
    member = mock_guild.members[1]
    with patch.object(cog, "_prompt_yes_no", new=AsyncMock(return_value=False)):
        await cog.approveLeader(mock_ctx, member, "Prayer")
        member.add_roles.assert_not_awaited()
        sent = mock_ctx.send.await_args[0][0]
        assert "cancelled" in sent


@pytest.mark.asyncio
async def test_transition_invalid_year(cog, mock_ctx):
    await cog.transition(mock_ctx, 2026) # 4 digits instead of 2
    mock_ctx.send.assert_awaited()
    sent = mock_ctx.send.await_args[0][0]
    assert "Invalid graduation year" in sent

@pytest.mark.asyncio
async def test_transition_mass_macro(cog, mock_ctx, mock_guild, tmp_path):
    mock_guild.create_text_channel = AsyncMock(return_value="created_chan")
    mock_guild.create_role = AsyncMock(return_value=MockRole("NewRole"))

    years_file = tmp_path / "current_years.json"
    with patch("utils.year_utils.get_default_years_path", return_value=years_file):
        await cog.transition(mock_ctx, 26)
        mock_ctx.send.assert_awaited()
        # Should report successful completion
        sent_messages = [call[0][0] for call in mock_ctx.send.call_args_list if call[0]]
        assert any("completed successfully" in msg for msg in sent_messages if isinstance(msg, str))
