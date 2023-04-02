from datetime import datetime

from discord.ext import tasks, commands

from main import Swashbot

_swashbot_pace_seconds = 3

class WasherCog(commands.Cog):
   def __init__(self, client: Swashbot) -> None:
      self.client = client
      self.watcher.start()

   @tasks.loop(seconds=_swashbot_pace_seconds, reconnect=True)
   async def watcher(self) -> None:
      for channel, settings in self.client.memo.channels.items():
         if not channel in self.client.decks: continue
         deck = self.client.decks[channel]
         discord_channel = await self.client.try_channel(channel)

         while len(deck) > settings.at_most:
            id = deck.pop_oldest()
            await self.client.try_delete(discord_channel, id)

         if deck.oldest is None: continue
         now = datetime.utcnow()
         created_at = deck.oldest.created_at.replace(tzinfo=None)
         age_minutes = (now - created_at).total_seconds() / 60
         
         while len(deck) > settings.at_least and age_minutes >= settings.minutes:
            id = deck.pop_oldest()
            await self.client.try_delete(discord_channel, id)

async def setup(client: Swashbot) -> None:
   await client.add_cog(WasherCog(client))