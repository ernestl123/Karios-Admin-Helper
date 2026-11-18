# Karios Admin Helper

A Discord bot tailored for Kairos Church of San Diego's college ministry, simplifying Discord tasks and server management for ministry leaders.

---

## Table of Contents
1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Testing Instructions](#testing-instructions)
4. [Command Usage & Documentation](#command-usage--documentation)
   - [Access Control](#access-control)
   - [Role Management Commands](#role-management-commands)
   - [Leader Onboarding & Approval](#leader-onboarding--approval)
   - [CSV Automation Commands](#csv-automation-commands)
   - [Channel Management Commands](#channel-management-commands)
   - [School Year Transition Macros](#school-year-transition-macros)
   - [Graduation Year Tracking](#graduation-year-tracking)
   - [Help Command](#help-command)
5. [Webhook Server](#webhook-server)

---

## Overview

- **Stack**: Python 3.13, `discord.py` 2.6.2, `Flask` 3.1.2.
- **Architecture**:
  - `src/bot.py`: Main bot startup, cog loader, command routing.
  - `src/webhook.py`: Flask webhook listener for Google Forms submissions.
  - `src/cogs/AdminMacros.py`: Primary administrative commands cog.
  - `src/cogs/help.py`: Custom help command embed.
  - `src/utils/`: Modular utilities for roles (`role_utils.py`), channels (`channel_utils.py`), CSVs (`csv_utils.py`), and graduation years (`year_utils.py`).

---

## Setup & Configuration

### 1. Environment & Dependencies

Create a virtual environment and install the required packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### 2. Configuration (`config.json`)

Create `config.json` in the project root (gitignored):

```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN",
  "prefix": "!",
  "form_log_channel_id": 123456789012345678,
  "VAM_ticket_log_channel_id": 123456789012345678,
  "form_port": 5000,
  "form_webhook_secret": "YOUR_OPTIONAL_WEBHOOK_SECRET",
  "pc_client_id": "OPTIONAL_PLANNING_CENTER_CLIENT_ID",
  "pc_client_secret": "OPTIONAL_PLANNING_CENTER_SECRET"
}
```

---

## Testing Instructions

The repository includes a comprehensive `pytest` test suite covering 100% of the bot's features, commands, utilities, and webhook integration.

### Run All Tests

```bash
.venv/bin/pytest
```

### Run Tests with Verbose Output

```bash
.venv/bin/pytest -v
```

### Run Tests with Code Coverage Report

```bash
.venv/bin/pytest --cov=src --cov-report=term-missing
```

### Run Specific Test Modules

```bash
# Run command cog tests
.venv/bin/pytest tests/test_admin_macros.py -v

# Run webhook server tests
.venv/bin/pytest tests/test_webhook.py -v

# Run utility tests
.venv/bin/pytest tests/test_role_utils.py tests/test_channel_utils.py tests/test_csv_utils.py -v
```

---

## Command Usage & Documentation

### Access Control
All administrative commands are protected by a cog check. Only users with roles specified under `role_info.Admin_Access_Roles` in `roles.json` (e.g., `"Admin Staff"`, `"Pastor"`, `"Shadow Admin"`) can execute them.

Commands can be invoked using the configured prefix (e.g., `!`) or by mentioning the bot (e.g., `@Kairos Admin Bot <command>`).

---

### Role Management Commands

#### `giveRole`
Assigns a specified role to a member. Supports quotes for role and member names containing spaces.
- **Usage**: `giveRole "<role_name>" "<member_name>"`
- **Example**:
  ```text
  !giveRole "Worship" "JohnDoe"
  !giveRole "Life Group Leaders" "Jane Doe"
  ```

#### `giveStaff` *(Hidden)*
Assigns the `"Staff"` role to a member.
- **Usage**: `giveStaff @member`
- **Example**:
  ```text
  !giveStaff @JohnDoe
  ```

---

### Leader Onboarding & Approval

#### `onboardStaff`
Onboards a new staff member by assigning the `"Staff"` role, each specified ministry role, and the corresponding `"<Ministry> Staff"` role (e.g., `"Prayer"` and `"Prayer Staff"`).
- **Usage**: `onboardStaff @member [role1] [role2] ...`
- **Example**:
  ```text
  !onboardStaff @JohnDoe Prayer Worship
  ```

#### `offboardStaff`
Removes the `"Staff"` role and any active ministry roles (defined in `roles.json`) from the member. Optionally posts a farewell message to the `#staff` channel.
- **Usage**: `offboardStaff @member [notify_staff_channel=True]`
- **Example**:
  ```text
  !offboardStaff @JohnDoe
  !offboardStaff @JohnDoe False
  ```

#### `approveLeader` (Aliases: `approve`, `approveleader`, `al`)
Approves a member as a leader.
1. Validates that all requested ministries exist in `roles.json` (use `VAM` for Visual Arts and Media).
2. Prompts the invoking admin for interactive `yes`/`no` confirmation.
3. Assigns the `"Leadership"` role and each `<Ministry>` role (e.g., `"Prayer"`, `"VAM"`).
4. Sends an announcement embed with the leader's avatar to the `#new-leaders-notifications` channel, mentioning the corresponding staff in charge.
- **Usage**: `approveLeader @member [ministry1] [ministry2] ...`
- **Example**:
  ```text
  !al @JohnDoe Prayer VAM
  ```

---

### CSV Automation Commands

#### `assignLeadership`
Assigns roles to members using an attached 2-column CSV file (`Role,Name`).
- **Usage**: `assignLeadership` *(attach CSV)*
- **CSV Format**:
  ```csv
  Role,Name
  Prayer,JohnDoe
  Worship,JaneDoe
  ```
- **Behavior**: Skips the header row, case-insensitively resolves each member and role, and assigns the roles. Displays processed count and any missing members or roles.

#### `updateLeadership`
Bulk migrates members to leadership roles using an attached CSV (`Name,Teams`).
- **Usage**: `updateLeadership` *(attach CSV)*
- **CSV Format**:
  ```csv
  Name,Teams
  JohnDoe,"Prayer, Worship"
  JaneDoe,"Life Group"
  ```
- **Behavior**:
  - Automatically appends the `"Leadership"` role.
  - Maps `"Life Group"` to `"Life Group Leader"` and `"A/V"` to `"Worship"`.
  - Resolves members by nickname, display name, or username.
  - Writes the processed rows to `current_leadership.csv`.
  - Sends a summary embed (or `.txt` file if log exceeds 4000 characters).

---

### Channel Management Commands

#### `transitionChannel`
Retires an existing channel and creates a new clean copy with identical category and permissions.
- **Usage**: `transitionChannel "<channel_name>" <grad_year>`
- **Example**:
  ```text
  !transitionChannel "worship" 26
  ```
- **Behavior**: Duplicates the channel, renames the old channel to `<name>-<grad_year>`, and moves the old channel to the `"Archived"` category with permissions synced.

#### `retireChannel`
Moves a channel directly to the `"Archived"` category without creating a duplicate.
- **Usage**: `retireChannel #channel [grad_year=-1]`
- **Example**:
  ```text
  !retireChannel #college-chat 26
  !retireChannel #old-event-chat
  ```

#### `deleteChannel`
Deletes a channel with interactive confirmation (`yes` / `no` within 30 seconds).
- **Usage**: `deleteChannel #channel`
- **Example**:
  ```text
  !deleteChannel #temp-channel
  ```

---

### School Year Transition Macros

#### `transitionMinistry` *(Hidden)*
Transitions a single ministry's role and associated channel for a new graduation year.
- **Usage**: `transitionMinistry "<ministry_name>" <grad_year>`
- **Example**:
  ```text
  !transitionMinistry "Prayer" 26
  !transitionMinistry "VAM" 26
  ```

#### `transition` *(Hidden)*
The master annual transition macro that updates the entire server for the upcoming school year.
- **Usage**: `transition <grad_year>` *(2-digit year, e.g., 26 for 2026)*
- **Example**:
  ```text
  !transition 26
  ```
- **Process**:
  1. Validates that the graduation year is 2 digits and server channel count does not exceed limits.
  2. For every ministry role in `roles.json`:
     - Creates a duplicate role with active color for the incoming year.
     - Renames the old role to `<Name> '<grad_year>` and changes color to gray.
     - Moves the associated channel to `"Archived"` and sets permissions for the replacement role.
  3. Deletes all temporary channels in the `"Special Events & Socials"` category.
  4. Updates `current_years.json` (Senior +1, Junior +2, Sophomore +3, Freshman +4).
  5. Archives the graduating senior channel (`#co-20<grad_year>`).
  6. Creates new class roles (e.g., `Class of '30`) and channels (e.g., `#co-2030` under `"Class Chat"`).
  7. Posts a detailed log embed of all actions taken.

---

### Graduation Year Tracking

#### `getYears` *(Hidden)*
Displays current graduation years for all four classes.
- **Usage**: `getYears`
- **Example**:
  ```text
  !getYears
  ```

#### `setYears` *(Hidden)*
Manually overrides the graduation year for a specific class in `current_years.json`.
- **Usage**: `setYears <class_name> <year_number>`
- **Example**:
  ```text
  !setYears Senior 2026
  !setYears Freshman 2030
  ```

---

### Help Command

#### `help` *(Hidden from default command list)*
Displays an organized Discord embed detailing all public bot commands and their usage syntax.
- **Usage**: `help`
- **Example**:
  ```text
  !help
  ```

---

## Webhook Server

The bot runs a background Flask server on the port configured in `form_port` (default `5000`).

- **Endpoint**: `POST /webhook`
- **Header**: `Webhook-Secret: <form_webhook_secret>`
- **Payload**:
  ```json
  {
    "title": "Rides Form",
    "data": {
      "Timestamp": "2026-11-18 10:00:00",
      "Name": "Student Name",
      "Notes": "Needs ride from campus"
    }
  }
  ```
- **Embed Colors**:
  - `"Late Rides Form"`: Red
  - `"Rides Form"`: Blue
  - Forms with `"driver"` in title: Green
