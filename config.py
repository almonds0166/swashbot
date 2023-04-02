import os

# Place your bot token and prefix here
SWASHBOT_TOKEN = ""
SWASHBOT_PREFIX = "~"
SWASHBOT_DATABASE = "swashbot.ltm"

# Note that the environment variable versions take precedence
SWASHBOT_TOKEN = os.environ.get("SWASHBOT_TOKEN", SWASHBOT_TOKEN)
SWASHBOT_PREFIX = os.environ.get("SWASHBOT_PREFIX", SWASHBOT_PREFIX)
SWASHBOT_DATABASE = os.environ.get("SWASHBOT_DATABASE", SWASHBOT_DATABASE)

if not SWASHBOT_TOKEN:
   raise RuntimeError("'SWASHBOT_TOKEN' not set")

if not SWASHBOT_PREFIX:
   raise RuntimeError("'SWASHBOT_PREFIX' not set")

if not SWASHBOT_DATABASE:
   raise RuntimeError("'SWASHBOT_DATABASE' not set")