import datetime
from typing import Optional, Tuple
import discord

POLL_OPTIONS = [
    "I can drive TO large group (Friday)",
    "I can drive BACK FROM large group (Friday)",
    "I can drive TO Sunday Service",
    "I can drive BACK FROM Sunday Service"
]

def get_week_dates(reference_date: Optional[datetime.date] = None) -> Tuple[datetime.date, datetime.date]:
    """
    Returns the Monday and Sunday dates for the week containing reference_date.
    Defaults to today if reference_date is None.

    Args:
        reference_date: Optional date to compute the week for.

    Returns:
        tuple[datetime.date, datetime.date]: (monday_date, sunday_date)
    """
    if reference_date is None:
        reference_date = datetime.date.today()
    monday = reference_date - datetime.timedelta(days=reference_date.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday

def format_poll_title(monday: datetime.date, sunday: datetime.date) -> str:
    """
    Formats the poll title for a given week's Monday and Sunday.
    Example: 'Staff Availability (11/16 - 11/22)'

    Args:
        monday: Monday date of the week.
        sunday: Sunday date of the week.

    Returns:
        str: Formatted poll title.
    """
    return f"Staff Availability ({monday.month}/{monday.day} - {sunday.month}/{sunday.day})"

def create_staff_availability_poll(
    monday_date: Optional[datetime.date] = None,
    duration_hours: int = 72
) -> discord.Poll:
    """
    Creates a discord.Poll instance for staff availability for the given week.

    Args:
        monday_date: Optional Monday date. If omitted, computes current week's Monday.
        duration_hours: Poll duration in hours. Defaults to 72 (3 days).

    Returns:
        discord.Poll: Configured poll instance ready to be sent.
    """
    monday, sunday = get_week_dates(monday_date)
    title = format_poll_title(monday, sunday)

    poll = discord.Poll(
        question=title,
        duration=datetime.timedelta(hours=duration_hours),
        multiple=True
    )

    for option in POLL_OPTIONS:
        poll.add_answer(text=option)

    return poll
