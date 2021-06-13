
import discord

async def command(client, param, ctx):
   """
   Syntax:
      ~help

   Description:
      Sends a help message leaflet into the channel
   """
   p = client.prefixes.get(ctx.guild.id, "~")

   tmp = "group DM" if ctx.guild is None else "server"

   help_meta = (
      f"`{p}help`: Display this message\n"
      f"`{p}info`: Display some info about Swashbot\n"
      f"`{p}prefix !`: Change the bot prefix for this {tmp} to `!`\n"
   )

   help_fundamental = (
      f"`{p}at least 10`: Always have at least 10 messages in the channel\n"
      f"`{p}at most 200`: Always have at most 200 messages in the channel\n"
      f"`{p}current`: Display current settings for this channel\n"
      f"`{p}time 120`: Messages wash away after 120 minutes\n"
      f"`{p}wave`: Wash away the last 100 messages\n"
   )

   e = discord.Embed(
      title="Example commands",
      description="[Read the documentation here](https://github.com/almonds0166/swashbot/blob/master/docs/docks.md)",
      color=client.color
   )

   e.add_field(
      name="Meta",
      value=help_meta.strip(),
      inline=False
   )

   e.add_field(
      name="Fundamental",
      value=help_fundamental.strip(),
      inline=False
   )

   await ctx.channel.send(embed=e)