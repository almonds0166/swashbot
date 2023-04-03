import os
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from utils.logging import build_logging_setup

# Place your bot token and prefix here
SWASHBOT_TOKEN = ""
SWASHBOT_PREFIX = "~"
SWASHBOT_DATABASE = "swashbot.ltm"

# Note that the environment variable versions take precedence
SWASHBOT_TOKEN = os.environ.get("SWASHBOT_TOKEN", SWASHBOT_TOKEN)
SWASHBOT_PREFIX = os.environ.get("SWASHBOT_PREFIX", SWASHBOT_PREFIX)
SWASHBOT_DATABASE = os.environ.get("SWASHBOT_DATABASE", SWASHBOT_DATABASE)

checks = {
   "SWASHBOT_TOKEN": SWASHBOT_TOKEN,
   "SWASHBOT_PREFIX": SWASHBOT_PREFIX,
   "SWASHBOT_DATABASE": SWASHBOT_DATABASE,
}

for name, value in checks.items():
   if not value:
      raise RuntimeError(f"{name!r} not set")

# Customize logging down here
# Disable logging by setting SWASHBOT_LOG to an empty string
SWASHBOT_LOG = "debug.log"
SWASHBOT_LOG = os.environ.get("SWASHBOT_LOG", SWASHBOT_LOG)

logging_setup = build_logging_setup(
   SWASHBOT_LOG,
   file_count=7,
   when="midnight",
   interval=1,
   swashbot_log_level=DEBUG,
   discord_log_level=DEBUG,
   http_log_level=INFO,
)
