from __future__ import annotations

import datetime

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

    @commands.command(aliases=["sget", "shoppingget"])
    async def shoppingwrite(self, ctx: commands.Context[commands.Bot]) -> None:
        """Write a new item to the shopping store using the context message."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        logger.info("Shopping write requested by %s (%s).", ctx.author, ctx.author.id)

        with self.store as store:
            item = liststore.ListItem(
                author=ctx.author.id,
                created_at=int(now.timestamp()),
                updated_at=int(now.timestamp()),
                closed_at=0,
                message_reference=ctx.message.id,
                message=ctx.message.clean_content,
                priority=liststore.ListPriority.NONE,
            )
            store.write(item)

        await ctx.message.add_reaction("📝")

    @commands.command(aliases=["slist"])
    async def shoppinglist(self, ctx: commands.Context[commands.Bot]) -> None:
        """Display a list of items from the store that are not closed."""
        logger.info("Shopping list requested by %s, (%s)", ctx.author, ctx.author.id)

        with self.store as store:
            rows = store.get()

        lines = []
        for row in rows:
            created = datetime.datetime.fromtimestamp(row.created_at)
            lines.append(f"- {created.strftime('%Y-%m-%d')} {row.message}")

        _embed = {
            "color": 0x9900CC,
            "title": "Active shopping list items:",
            "author": {
                "name": ctx.author.display_name,
                "icon_url": ctx.author.display_avatar.url,
            },
            "description": "\n".join(lines),
        }

        embed = discord.Embed().from_dict(_embed)

        await ctx.send(embed=embed)
