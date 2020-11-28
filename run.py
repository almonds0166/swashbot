
import os

try:
   import discord
except ImportError as e:
   v = sys.version_info
   print(
      f"Hey, did you happen to install the discord.py module yet?\n"
      f"If it helps, you're using Python {v.major}.{v.minor}.{v.micro}\n"
      f"So maybe try `pip{v.major} install discord.py`?\n"
      f"Or `py -{v.major}.{v.minor} -m pip install discord.py` if you're on Windows?\n"
      f"Hope all goes well!\n"
   )
   raise e
import asyncio

from swashbot.config import TOKEN
from swashbot import Swashbot

if __name__ == "__main__":
   client = Swashbot(TOKEN)
   client.run()