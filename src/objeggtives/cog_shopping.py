from __future__ import annotations

import discord
from discord.ext import commands

from . import liststore
from . import struclogger

logger = struclogger.get_logger()

STORE_NAME = "shopping.db"


class ShoppingCog(commands.Cog):
    """Define a cog for debugging purposes."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the cog."""
        self.bot = bot
        self.store = liststore.get_liststore(STORE_NAME)
        logger.info("%s initialized.", self.__cog_name__)

    @commands.command()
    async def shoppinginfo(self, ctx: commands.Context[commands.Bot]) -> None:
        """Respond with an embed of the shopping store info."""
        logger.info("Shopping info requested by %s (%s).", ctx.author, ctx.author.id)

        with self.store as store:
            connected = store.connected
            total, closed = store.counts()
            percent_closed = (closed / total) * 100 if total > 0 else 0

        embed = discord.Embed(
            title="Shopping Store Info",
            description=f"""\
                Store Name: {STORE_NAME}
                Connected: {connected},
                Total Items: {total},
                Closed Items: {closed},
                Percent Closed: {percent_closed:.2f}%
                """,
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)
