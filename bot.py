from typing import Optional

from discord.gateway import DiscordWebSocket
from discord.ext import commands

import discord
import logging
import aiohttp

from helpers.context import Context
from helpers.database import Database

import config

description = """
asdfgh.
"""

logger: logging.Logger = logging.getLogger(__name__)

# def command(example_response: Optional[str] = None, **kwargs: Any):
#     """
#     Custom command decorator that supports example_response parameter
#     """

#     def decorator(func: Callable) -> Callable:
#         func.__example_response__ = example_response
#         cmd = commands.command(**kwargs)(func)
#         cmd.example_response = example_response

#         return cmd

#     return decorator


# def hybrid_command(example_response: Optional[str] = None, **kwargs: Any):
#     """
#     Custom hybrid_command decorator that supports example_response parameter
#     Works as both slash command and text command
#     """

#     def decorator(func: Callable) -> Callable:
#         func.__example_response__ = example_response
#         cmd = commands.hybrid_command(**kwargs)(func)
#         cmd.callback.__example_response__ = example_response

#         return cmd

#     return decorator


# def group(example_response: Optional[str] = None, **kwargs: Any):
#     """
#     Custom group decorator that supports example_response parameter
#     """

#     def decorator(func: Callable) -> Callable:
#         func.__example_response__ = example_response
#         cmd = commands.group(**kwargs)(func)
#         cmd.example_response = example_response

#         return cmd

#     return decorator


async def identify(self):
    payload = {
        "op": self.IDENTIFY,
        "d": {
            "token": self.token,
            "properties": {
                "$os": "iOS",  # Must be 'iOS' or 'Android'
                "$browser": "Discord iOS",
                "$device": "Discord iOS",
                "$referrer": "",
                "$referring_domain": "",
            },
            "compress": True,
            "large_threshold": 250,
            "v": 3,
        },
    }

    if self.shard_id is not None and self.shard_count is not None:
        payload["d"]["shard"] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload["d"]["presence"] = {
            "status": state._status,
            "game": state._activity,
            "since": 0,
            "afk": False,
        }

    if state._intents is not None:
        payload["d"]["intents"] = state._intents.value

    await self.call_hooks(
        "before_identify", self.shard_id, initial=self._initial_identify
    )
    await self.send_as_json(payload)


if config.Settings.mobile:
    DiscordWebSocket.identify = identify


class Bot(commands.AutoShardedBot):
    """
    asdfgh

    Yet another advanced Discord bot written in Python using discord.py
    """

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    def __init__(self) -> None:
        allowed_mentions = discord.AllowedMentions(
            roles=False, everyone=False, users=True
        )
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=self.get_prefix,
            description=description,
            chunk_guilds_at_startup=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
            help_command=None
        )

        self.db = Database(config.Settings.db_path)

    async def get_prefix(self, message):
        if not message.guild:
            return config.Settings.default_prefix

        result = await self.db.fetchone(
            """
            SELECT prefix 
            FROM prefixes 
            WHERE guild_id = ?
            """,
            (message.guild.id,),
        )
        return result[0] if result else config.Settings.default_prefix

    async def setup_hook(self):
        """Load extensions and sync commands"""
        self.session = aiohttp.ClientSession()

        for feature in config.Settings.features:
            try:
                await self.load_extension("features." + feature)
                logger.info(f"Loaded {feature}")

            except Exception as e:
                logger.exception(e)

        # try:
        #     synced = await self.tree.sync()
        #     logger.info(f"Synced {len(synced)} slash command(s) globally")
        # except Exception as e:
        #     logger.exception(e)

    async def on_message(self, message):
        if str(self.user.id) in message.content:
            await message.channel.send(
                f"my prefix here is `{await self.get_prefix(message)}`"
            )

        await self.process_commands(message)

    async def on_command_error(
        self, context: commands.Context, exception: commands.CommandError
    ) -> Optional[discord.Message]:
        if isinstance(exception, (commands.CommandNotFound, commands.DisabledCommand)):
            return

        if not context.command:
            return

        if isinstance(exception, commands.ConversionError):
            return await context.send(str(exception.original))

        if isinstance(exception, commands.MissingRequiredArgument):
            return await context.send(
                f"{exception.param.name} is a required argument that is missing"
            )

        if isinstance(exception, commands.BadArgument):
            return await context.send(str(exception))

        if isinstance(
            exception,
            (
                commands.FlagError,
                commands.BadFlagArgument,
                commands.MissingFlagArgument,
                commands.MissingRequiredFlag,
                commands.TooManyArguments,
                commands.TooManyFlags,
                commands.MissingPermissions,
                commands.BotMissingPermissions,
                commands.ExtensionAlreadyLoaded,
                commands.ExtensionNotFound,
                commands.ExtensionError,
            ),
        ):
            return await context.send(str(exception))
