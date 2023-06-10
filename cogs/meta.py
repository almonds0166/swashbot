from typing import Optional
from pathlib import Path
import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from main import Swashbot

class MetaCog(commands.Cog):
   """TODO: replace with a help formatter
   """
   def __init__(self, client: Swashbot) -> None:
      self.client = client

   @commands.hybrid_command(name="help", description="share a help leaflet")
   async def slash_help(self, ctx: commands.Context) -> None:
      if not isinstance(ctx.message.channel, discord.abc.Messageable): return
      p = self.client.command_prefix

      help_meta = (
         f"`{p}help`: Display this message\n"
      )

      help_fundamental = (
         f"`{p}atleast 10`: Always have at least 10 messages in the channel\n"
         f"`{p}atmost 200`: Always have at most 200 messages in the channel\n"
         f"`{p}current`: Display current settings for this channel\n"
         f"`{p}minutes 120`: Messages wash away after 120 minutes\n"
         f"`{p}wave`: Wash away the last 100 messages\n"
      )

      embed = discord.Embed(
         title="Example commands",
         description="[Read the documentation here](https://github.com/almonds0166/swashbot/blob/master/docs/docks.md)",
         color=self.client.color
      )

      embed.add_field(
         name="Meta",
         value=help_meta.strip(),
         inline=False
      )

      embed.add_field(
         name="Fundamental",
         value=help_fundamental.strip(),
         inline=False
      )

      await ctx.message.reply(embed=embed)

   @commands.hybrid_command(name="stats", description="get statistics")
   async def slash_stats(self, ctx: commands.Context) -> None:

      content = f"I've been up for **{self.client.uptime}**"
      busy_level = self.client.busy_level
      if busy_level:
         content += f"\n⚠️ Note: busy level is **{busy_level}**"

      statistics = [
         f"* **{self.client.disconnects}** disconnect(s)",
         f"* **{self.client.errors}** error(s)",
         f"* **{self.client.latency*1000:.1f}ms** latency",
         f"* **{self.client.commands_processed}** command(s) processed",
         f"* washing **{len(self.client.memo.settings)}** channel(s)",
         f"* in **{len(self.client.memo.channels)}** server(s)",
         f"* **{self.client.messages_deleted}** message(s) deleted",
         f"* at a rate of **{self.client.deletion_rate}**",
      ]

      embed = discord.Embed(
         title=f"Statistics",
         description="\n".join(statistics),
         color=self.client.color
      )

      await ctx.reply(content, embed=embed)

   @commands.hybrid_command(name="backup", description="make a backup of Swashbot's long-term memory (must be bot owner)")
   async def slash_backup(self, ctx: commands.Context, tag: Optional[str]=None):
      if not await self.client.is_owner(ctx.author):
         await ctx.reply("You're not my owner 👀")
         return

      backup_file = self.client.memo.backup(tag)
      await ctx.reply(f"I made a backup named `{backup_file!r}`")

   @commands.hybrid_command(name="tail", description="print out tail of some file")
   async def slash_tail(self, ctx: commands.Context, file: str="debug.log", n: int=5):
      if not await self.client.is_owner(ctx.author):
         await ctx.reply("You're not my owner 👀")
         return

      try:
         with open(Path(file), "r") as f:
            lines = f.readlines()
            tail = "".join(lines[-n:]).strip()
      except FileNotFoundError:
         await ctx.message.add_reaction("👀")
         cwd = Path(".")
         files = [f.name for f in cwd.iterdir()]
         max_length = max(len(f) for f in files)
         num_columns = 80 // (max_length + 2)
         ls_string = ""
         for i, f in enumerate(files):
            ls_string += f.ljust(max_length + 2)
            if (i + 1) % num_columns == 0:
               ls_string += "\n"

         msg = (
            f"Hm, I can't find `{file!r}` here. "
            f"If it helps, I'm currently at `{Path('.').resolve()}`. "
            f"Here're the files I can see:\n"
            f"```\n"
            f"{ls_string}\n"
            f"```"
         )

      else:
         msg = f"`{file!r}`:\n```\n{tail}\n```"

      async with ctx.typing(): await asyncio.sleep(1)
      try:
         await ctx.reply(msg)
      except discord.NotFound:
         pass

   @commands.hybrid_command(name="slash", description="sync slash commands")
   async def slash_slash(self, ctx: commands.Context):
      if not await self.client.is_owner(ctx.author):
         await ctx.reply("You're not my owner 👀")
         return

      synced = await self.client.tree.sync()
      msg = f"Synced {len(synced)} commands."
      self.client.log.info(msg)
      if ctx.interaction:
         await ctx.reply(f"Synced {len(synced)} commands.")
      else:
         await ctx.message.add_reaction("👌")

async def setup(client: Swashbot) -> None:
   client.remove_command("help")
   await client.add_cog(MetaCog(client))