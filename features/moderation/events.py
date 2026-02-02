from typing import Optional

from discord.ext import commands
from discord.ext import tasks

import discord
import aiosqlite

from bot import Bot


class Events(commands.Cog):
    """
    Event listeners
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.db
        self.unban_check.start()

    @tasks.loop(minutes=1)
    async def unban_check(self) -> Optional[aiosqlite.Cursor]:
        """
        Loop to check for unbans
        """
        current_time = discord.utils.utcnow().isoformat()
        records = await self.db.fetchall(
            """
            SELECT guild_id, user_id
            FROM unbans
            WHERE unban_time <= ?
            """,
            (
                current_time,
            ),
        )

        for record in records:
            guild = self.bot.get_guild(record[0])
            if guild is None:
                continue

            user = discord.Object(id=record[1])
            try:
                await guild.unban(user, reason="Temporary ban expired")

            except discord.NotFound:
                pass

            await self.db.execute(
                """
                DELETE FROM unbans
                WHERE guild_id = ? 
                AND user_id = ?
                """,
                (
                    record[0],
                    record[1],
                ),
            )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """
        Listener for when a member is unbanned from the server
        """
        record = await self.db.fetchrow(
            """
            SELECT user_id
            FROM unbans
            WHERE guild_id = ? AND user_id = ?
            """,
            (
                guild.id,
                user.id,
            ),
        )

        if record:
            await self.db.execute(
                """
                DELETE FROM unbans
                WHERE guild_id = ? 
                AND user_id = ?
                """,
                (
                    guild.id,
                    user.id,
                ),
            )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Events(bot))