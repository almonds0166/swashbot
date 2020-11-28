
import discord

async def command(client, param, ctx):
   """
   Syntax:
      ~wave
      ~wave m

   Description:
      Wash away m of the most recent messages in the channel. If m is not
      specified, washes away 100 messages. If m == 0, adds a waving emoji to
      your message :P
   """
   if param.isdigit():
      param = max(0, int(param))
   elif param in ("inf", "infty", "infinity"):
      param = INF
   else:

      return

   if param == 0:
      # This waving emoji GIF was shamelessly stolen from the
      # Blob Emoji server https://discord.gg/pFUhE5z
      # one day I'll make a GIF in Krita unique to Swashbot
      try:
         await ctx.msg.add_reaction("<a:awave:780163655568064513>")
      except discord.NotFound:
         pass
      return

   try:
      await ctx.msg.add_reaction("⏲️")
      await ctx.msg.add_reaction("🌊")
   except discord.NotFound:
      pass

   await client.delete_multiple_messages(ctx.channel, ctx.msg.created_at, param)

   try:
      await ctx.msg.remove_reaction("⏲️", client.user)
      await ctx.msg.remove_reaction("🌊", client.user)
      await ctx.msg.add_reaction("👌")
      await ctx.msg.delete(delay=1)
   except discord.NotFound:
      pass