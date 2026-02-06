from discord.ext import commands
from enum import Enum

class Modules(str, Enum):
    VANITY = "vanity"
    BOTADD = "botadd"
    BAN = "ban"
    KICK = "kick"
    ROLES = "roles"
    CHANNELS = "channels" # Creating, Deleting
    EMOJIS = "emojis"     # Deleting
    WEBHOOKS = "webhooks" # Creating

class AntinukeModules(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            return Modules(argument.lower())

        except ValueError:
            valid = ", ".join([m.value for m in Modules])
            raise commands.BadArgument(f"Invalid module")
