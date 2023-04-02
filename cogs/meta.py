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

      content = f"I've been up for {self.client.uptime}"
      busy_level = self.client.busy_level
      if busy_level:
         content += f"\n⚠️ Note: busy level is **{busy_level}**"

      statistics = [
         f"* **{self.client.disconnects}** disconnect(s)",
         f"* **{self.client.errors}** error(s)",
         f"* washing **{len(self.client.memo.channels)}** channel(s)",
         f"* in **{len(self.client.memo.guilds)}** server(s)",
         f"* **{self.client.messages_deleted}** message(s) deleted",
         f"* at a rate of **{self.client.deletion_rate}**",
      ]

      embed = discord.Embed(
         title=f"Statistics",
         description="\n".join(statistics),
         color=self.client.color
      )

      await ctx.reply(content, embed=embed)

async def setup(client: Swashbot) -> None:
   client.remove_command("help")
   await client.add_cog(MetaCog(client))