from typing import Optional, Union

from discord.ext.commands import Context as DiscordContext, Command
from datetime import datetime, timezone

import discord
import config

from helpers.converters.duration import Duration


class Context(DiscordContext):
    """A custom context class that extends Discord's Context."""

    async def confirm(
        self,
        emoji: Optional[str] = config.Emoji.Context.success,
        message: Optional[str] = None,
    ) -> discord.Message:
        return await (
            self.send(f"{emoji} {message}")
            if emoji and message
            else self.message.add_reaction(emoji)
        )

    async def error(
        self,
        emoji: Optional[str] = config.Emoji.Context.error,
        message: Optional[str] = None,
    ) -> discord.Message:
        return await (
            self.send(f"{emoji} {message}")
            if emoji and message
            else self.message.add_reaction(emoji)
        )

    async def warn(
        self,
        emoji: Optional[str] = config.Emoji.Context.warning,
        message: Optional[str] = None,
    ) -> discord.Message:
        return await (
            self.send(f"{emoji} {message}")
            if emoji and message
            else self.message.add_reaction(emoji)
        )

    async def punishment(
        self,
        emoji: Optional[str] = config.Emoji.Moderation.envelope,
        punishment: Optional[str] = None,
        member: Optional[Union[discord.Member, discord.User]] = None,
        until: Optional[Union[Duration, datetime]] = None,
    ) -> discord.Message:
        until_dt = until.to_datetime() if isinstance(until, Duration) else until
        return await self.send(
            f"{emoji} applied **{punishment}** to {member.mention}"
            + (
                f" until <t:{int(until_dt.timestamp())}:f> ({(until_dt - datetime.now(timezone.utc)).days} days)"
                if until_dt
                else ""
            )
        )

    async def send_help(self, prefix: str, command: Command = None) -> discord.Message:
        if not command:
            return await self.send("Command not found")

        aliases: str = ', '.join(command.aliases) if command.aliases else ''
        return await self.send(
            f"{prefix}{command.qualified_name} ({aliases}): {command.help or command.short_doc}"
        )