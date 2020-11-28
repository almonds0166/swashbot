
async def command(client, param, ctx):
   """
   Syntax:
      ~debug

   Description:
      Just tells me how many servers and channels swashbot
      is swashing about in, and gives me the current channel settings
   """
   cid = ctx.channel.id

   if cid in client.memo:
      f = (
         f"```python\n"
         f"memo = {{\n"
         f"   \"at_least\": {client.memo[cid].at_least},\n"
         f"   \"at_most\": {client.memo[cid].at_most},\n"
         f"   \"time\": {client.memo[cid].time},\n"
         f"}}\n"
         f"```\n"
      )
   else:
      f = "No settings saved for this channel yet.\n"

   f += (
      f"`n` = `{len(client.all_guilds)}`\n"
      f"`c` = `{len(client.all_channels)}`\n"
   )

   await ctx.channel.send(f)