from discord.ext import commands

import discord
import config


class Role(commands.Converter):
    """Converter that ensures command author has higher role than target role"""

    async def convert(self, context: commands.Context, argument: str) -> discord.Role:
        if not context.guild:
            raise commands.NoPrivateMessage("This command cannot be used in DMs")

        try:
            role = await commands.RoleConverter().convert(context, argument)
        except commands.RoleNotFound:
            raise commands.BadArgument(f"Role `{argument}` not found")

        if context.author.id == config.Settings.owner_id:
            return role

        if role.is_default():
            raise commands.BadArgument("You cannot target the @everyone role")

        if role.managed:
            raise commands.BadArgument(f"{role.mention} is managed by an integration")

        if not isinstance(context.author, discord.Member):
            raise commands.BadArgument("Could not verify your permissions")

        if context.author.top_role <= role and context.author != context.guild.owner:
            raise commands.BadArgument(
                f"You cannot target {role.mention} (role hierarchy)"
            )

        if context.guild.me.top_role <= role:
            raise commands.BadArgument(
                f"I cannot target {role.mention} (role hierarchy)"
            )

        return role
