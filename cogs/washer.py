from datetime import datetime
from typing import Optional

import discord
from discord.ext import tasks, commands

from main import Swashbot, SwashbotMessageable

_swashbot_pace_seconds = 5

_permission_to_delete = discord.Permissions(
   manage_messages=True,
   view_channel=True,
   read_message_history=True,
)

class WasherCog(commands.Cog):
   def __init__(self, client: Swashbot) -> None:
      self.client = client
      self.watcher.start()

   @tasks.loop(seconds=_swashbot_pace_seconds, reconnect=True)
   async def watcher(self) -> None:
      """Main watchdog loop that keeps track of when we have messages to delete
      """
      task = self.client.new_task()
      messages = 0

      for channel, settings in self.client.memo.settings.items():
         if not channel in self.client.decks: continue
         deck = self.client.decks[channel]
         discord_channel: Optional[SwashbotMessageable] = None

         insufficient_permissions = False
         clean_shoreface = False
         clean_swashzone = False

         while len(deck) > settings.at_most:
            if discord_channel is None:
               discord_channel = await self.client.try_channel(channel)
               if not await self.client.check_permissions(discord_channel, _permission_to_delete):
                  insufficient_permissions = True
                  break

            if not clean_shoreface:
               self.client.log.debug(f"{task}: #{discord_channel.name} ({channel}): Looks like I have about {len(deck) - settings.at_most} message(s) in the shore face...")
               clean_shoreface = True

            id = deck.pop_oldest()
            await self.client.try_delete(discord_channel, id)
            messages += 1

         if insufficient_permissions: continue

         if deck.oldest is None: continue
         now = datetime.utcnow()
         created_at = deck.oldest.created_at.replace(tzinfo=None)
         age_minutes = (now - created_at).total_seconds() / 60
         
         while len(deck) > settings.at_least and age_minutes >= settings.minutes:
            if discord_channel is None:
               discord_channel = await self.client.try_channel(channel)
               if not await self.client.check_permissions(discord_channel, _permission_to_delete):
                  insufficient_permissions = True
                  break
            
            if not clean_swashzone:
               self.client.log.debug(f"{task}: #{discord_channel.name} ({channel}): Looks like I have some messages to clean in the swash zone...")

            id = deck.pop_oldest()
            await self.client.try_delete(discord_channel, id)
            messages += 1

         if insufficient_permissions: continue # superfluous

      if messages:
         self.client.log.debug(f"{task}: Cleaned {messages} message(s) total...")

async def setup(client: Swashbot) -> None:
   await client.add_cog(WasherCog(client))