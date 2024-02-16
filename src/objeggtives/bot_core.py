from __future__ import annotations

import datetime
from typing import Any

import discord
from discord.ext import commands
from secretbox import SecretBox

from . import struclogger

# Initialize runtime and bot
secrets = SecretBox(auto_load=True)
struclogger.init_struclogger()
logger = struclogger.get_logger(__name__)
logger.setLevel("INFO")

# TODO: Replace these with a config object
GUILD_ID = secrets.get("GUILD_ID")
DISCORD_TOKEN = secrets.get("DISCORD_TOKEN")
INTENT_PRESENCE = True
INTENT_MEMBERS = True
INTENT_MESSAGE_CONTENT = True


class objeggtivesBot(commands.Bot):
    """Define the bot and handle basic events."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the bot."""
        super().__init__(*args, **kwargs)

    async def start(self, *args: Any, **kwargs: Any) -> None:
        """Start the bot."""
        logger.info("Starting bot...")

        # TODO: Create a cog manager
        await self.add_cog(_DebugCog(self))

        await super().start(*args, **kwargs)


class _DebugCog(commands.Cog):
    """Define a cog for debugging purposes."""

    def __init__(self, bot: objeggtivesBot) -> None:
        """Initialize the cog."""
        self.bot = bot
        logger.info("DebugCog initialized.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Log when the bot is ready."""
        logger.info(f"{self.bot.user} has connected to Discord!")

    @commands.command()
    async def ping(self, ctx: commands.Context[objeggtivesBot]) -> None:
        """Respond with a pong."""
        _sent = ctx.message.created_at
        _now = datetime.datetime.now(tz=datetime.timezone.utc)
        _diff = _now - _sent

        await ctx.send(f"Pong! {_diff.total_seconds():.2f}s", delete_after=5)


def main() -> int:
    """Define and run the bot."""
    intents = discord.Intents.default()
    intents.presences = INTENT_PRESENCE
    intents.members = INTENT_MEMBERS
    intents.message_content = INTENT_MESSAGE_CONTENT
    bot = objeggtivesBot(command_prefix="!", intents=intents)

    bot.run(DISCORD_TOKEN)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
