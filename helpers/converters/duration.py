from discord.ext import commands
from datetime import datetime, timedelta, timezone

import re


class Duration(commands.Converter):
    """Converter that parses duration strings into Duration objects with datetime"""

    def __init__(self, dt: datetime):
        self.datetime = dt

    @classmethod
    async def convert(cls, context: commands.Context, argument: str) -> "Duration":
        """
        Convert duration string to Duration object
        Formats: 1d, 2h, 30m, 1w, or combinations like 1d12h30m
        """
        if not argument:
            raise commands.BadArgument("Duration cannot be empty")

        pattern = r"(\d+)([smhdw])"
        matches = re.findall(pattern, argument.lower())

        if not matches:
            raise commands.BadArgument(
                "Invalid duration format. Use format like: 1d, 2h, 30m, 1w, or 1d12h"
            )

        total_seconds = 0
        units = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
        }

        for value, unit in matches:
            total_seconds += int(value) * units[unit]

        if total_seconds <= 0:
            raise commands.BadArgument("Duration must be greater than 0")

        max_timeout = 28 * 24 * 60 * 60
        if total_seconds > max_timeout:
            raise commands.BadArgument("Duration cannot exceed 28 days for timeouts")

        return cls(datetime.now(timezone.utc) + timedelta(seconds=total_seconds))

    @staticmethod
    def parse_to_timedelta(duration_str: str) -> timedelta:
        """Parse duration string to timedelta without converter context"""
        import re

        pattern = r"(\d+)([smhdwy])"
        matches = re.findall(pattern, duration_str.lower())

        if not matches:
            raise ValueError("Invalid duration format")

        total_seconds = 0
        units = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
            "y": 31536000,
        }

        for value, unit in matches:
            total_seconds += int(value) * units[unit]

        return timedelta(seconds=total_seconds)

    def to_datetime(self) -> datetime:
        """Return the datetime object"""
        return self.datetime

    def __str__(self) -> str:
        """String representation showing relative time"""
        delta = self.datetime - datetime.now(timezone.utc)

        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 and not parts:
            parts.append(f"{seconds}s")

        return "".join(parts) if parts else "0s"

    def __repr__(self) -> str:
        return f"Duration({self.datetime.isoformat()})"
