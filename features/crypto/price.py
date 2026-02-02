from typing import Optional

from discord.ext import commands

from bot import Bot
from helpers.context import Context
from helpers.utils import symboltocurrency

import discord

from .api import client


class Crypto(commands.Cog):
    """
    CryptoCompare API interactions
    """
    
    def __init__(self, bot: Bot, api_key: Optional[str] = None):
        self.bot = bot
        self.client = client.CryptoCompare(api_key=api_key)


    @commands.group(name="crypto", invoke_without_command=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def crypto(self, context: Context) -> discord.Message:
        """
        Cryptocurrency commands
        """
        return await context.send_help()


    @crypto.command(name="price")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def price(
        self,
        context: Context,
        symbol: str,
        currency: str = "USD"
    ) -> discord.Message:
        """
        Get the current price of a cryptocurrency
        """
        try:
            price = await self.client.get_price(symbol, currency)
            return await context.send(f"price of **{symbol.lower()}** in **{currency.lower()}** is **{await symboltocurrency(currency)}{price}**")

        except Exception as e:
            return await context.warn(f"error fetching price:\n```{e}```")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Crypto(bot))