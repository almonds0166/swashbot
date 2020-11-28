
import discord

INF = None

async def command(client, param, ctx):
   """
   Syntax:
      ~current

   Description:
      Get it? Current? Haaa
      Explicitly tells users how Swashbot is working to swash in the channel
   """
   cid = ctx.channel.id

   e = discord.Embed(
      title="Current settings for this channel",
      description=status_message(client.memo.get(cid, client.DEFAULT_SETTINGS)),
      color=client.color
   )

   await ctx.channel.send(embed=e)
   
def status_message(memo):
   """
   Creates a status string for the current settings
   """

   at_least = memo.at_least
   at_most  = memo.at_most
   time     = memo.time

   if at_most is INF and time is INF:
      return "No action taken."

   f = ""
   if at_least == 0 and at_most == 0:
      f += "Turbid! Delete all new messages immediately. "
      f += "Wait, doesn't that mean this message will get deleted in a split second?\n"
   elif at_least == 0:
      if at_most is not INF:
         f += f"Immediately delete all messages past count {at_most}.\n"
         f += f"Everything else takes {time} minute"
      else:
         f += f"Messages take {time} minute"
      f += "s" if time != 1 else ""
      f += " to wash away.\n"
   elif at_least == at_most and at_most is not INF:
      f += f"Immediately delete all messages past count {at_most}.\n"
   else:
      f += f"Always keep the {at_least} most recent message"
      f += "s" if at_least != 1 else ""
      f += ".\n"
      if at_most is not INF:
         f += f"Delete all messages past count {at_most}.\n"
         if time is not INF:
            f += f"Any messages in-between take {time} minute"
            f += "s" if time != 1 else ""
            f += " to wash away.\n"
      else:
         f += f"Any other messages take {time} minute"
         f += "s" if time != 1 else ""
         f += " to wash away.\n"

   return f.strip()
