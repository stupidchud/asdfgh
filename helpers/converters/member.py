from discord.ext import commands

import discord
import config


class Member(commands.Converter):
    """Converter that handles both guild members and users, with hierarchy checks for members"""

    async def convert(self, context: commands.Context, argument: str):
        if not context.guild:
            raise commands.NoPrivateMessage("This command cannot be used in DMs")

        try:
            member = await commands.MemberConverter().convert(context, argument)

            if context.author.id == config.Settings.owner_id:
                return member

            if member == context.author:
                raise commands.BadArgument("You cannot target yourself")

            if member == context.guild.me:
                raise commands.BadArgument("I cannot target myself")

            if not isinstance(context.author, discord.Member):
                raise commands.BadArgument("Could not verify your permissions")

            if (
                context.author.top_role <= member.top_role
                and context.author != context.guild.owner
            ):
                raise commands.BadArgument(
                    f"You cannot target {member.mention} (role hierarchy)"
                )

            if context.guild.me.top_role <= member.top_role:
                raise commands.BadArgument(
                    f"I cannot target {member.mention} (role hierarchy)"
                )

            return member

        except commands.MemberNotFound:
            pass

        try:
            user = await commands.UserConverter().convert(context, argument)

            # Basic checks for users
            if context.author.id != config.Settings.owner_id:
                if user.id == context.author.id:
                    raise commands.BadArgument("You cannot target yourself")
                if user.id == context.guild.me.id:
                    raise commands.BadArgument("I cannot target myself")

            return user

        except commands.UserNotFound:
            raise commands.BadArgument(f"User `{argument}` not found")
