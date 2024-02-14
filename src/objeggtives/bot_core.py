from __future__ import annotations

import re

import discord
from secretbox import SecretBox

from .struclogger import get_logger

# Initialize runtime and bot
secrets = SecretBox(auto_load=True)
logger = get_logger(__name__)

# TODO: Replace these with a config object
GUILD_ID = secrets.get("GUILD_ID")
DISCORD_TOKEN = secrets.get("DISCORD_TOKEN")
INTENT_PRESENCE = True
INTENT_MEMBERS = True
INTENT_MESSAGE_CONTENT = True
_PREFIX_PATTERN = re.compile("^!{1}[^!]+")


class objeggtivesBot(discord.Client):
    """Define the bot and handle basic events."""

    async def on_ready(self) -> None:
        """Simple console logging indicating ready event has fired."""
        print("objeggtives bot is ready.")
        logger.info("objeggtives bot is ready.")

    async def on_message(self, message: discord.Message) -> None:
        """Handle message events."""

        # Do not listen to myself
        if message.author == self.user:
            logger.debug("Ignoring message from self.")
            print("Ignoring message from self.")
            return None

        # Do not listen to other bots
        if message.author.bot:
            logger.debug("Ignoring message from other bot.")
            print("Ignoring message from other bot.")
            return None

        # Check if message is a command
        if _PREFIX_PATTERN.match(message.content):
            logger.info("Command received: %s", message.content)
            print(f"Command received: {message.content}")
            # TODO: Implement command handling here
            await message.channel.send(f"Command received: {message.content}")

        print(f"Message received: {message.content}")


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
