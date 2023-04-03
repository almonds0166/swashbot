import sys

vi = sys.version_info
version = f"{vi.major}.{vi.minor}.{vi.micro}"

if vi < (3, 10):
   raise RuntimeError(f"please update to Python v3.10 or above (current: v{version})")

try:
   import discord
   from discord.utils import setup_logging
except ImportError as e:
   print((
      f"Hi, friend! I'm having trouble importing the discord.py module. "
      f"If it helps, it looks like we're using Python v{version}. "
      f"So maybe try something like `pip{vi.major}.{vi.minor} install -U discord.py`? "
   ).strip())
   raise e

from main import Swashbot
from config import SWASHBOT_TOKEN, logging_setup

if logging_setup:
   setup_logging(**logging_setup)

if __name__ == "__main__":
   bot = Swashbot()
   bot.run(SWASHBOT_TOKEN)