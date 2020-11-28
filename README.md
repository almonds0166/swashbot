# swashbot

Discord bot that erases messages over time [like gentle beach waves](https://www.youtube.com/watch?v=b44ruhi5ji4).

**Disclaimer**: I am not currently hosting Swashbot on any stable VPS (because doing so costs money), this is more of a personal project hosted privately, but I think it's cool enough of a project to make this repository public and open source. Maybe in the future I will consider hosting Swashbot for universal use.

## Notes

Interact with Swashbot by using its prefix (default `~`), followed by the command and potential arguments.

Swashbot does not wash away pinned messages.

### Gist of commands

* `~help` -- share a help leaflet
* `~time 300` -- erase messages after they've existed for 300 minutes (5 hours)
* `~at least 10` -- don't delete the current 10 most recent messages in the channel
* `~at most 200` -- never keep more than 200 messages in the channel
* `~current` -- get the current settings for the channel
* `~wave` -- erase the last 100 messages in the channel
* `~prefix !` -- change the server prefix to `!`