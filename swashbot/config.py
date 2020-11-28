
import os

# memory file location (prefer environment variable value, if available)
MEMORY = "./swashbot.ltm"
MEMORY = os.getenv("SWASHBOT_MEMORY", MEMORY)

# bot token
TOKEN = os.getenv("SWASHBOT_TOKEN", "(no token given yet!)")

# debug log
DEBUG_LOG = "./debug.log"

# Swashbot debug/development Discord webhook link
# by default, Swashbot sends warn and error logging information here
WEBHOOK = ""
WEBHOOK = os.getenv("SWASHBOT_WEBHOOK", WEBHOOK)

# the throttle at which Swashbot waits between checks for each channel
# I doubt this will ever need to be changed, since one second works perfectly well
# units of seconds
THROTTLE = 1

# rgb colour of Swashbot's embeds
COLOUR = (46, 137, 139)