# swashbot

Discord bot that erases messages over time [like gentle beach waves](https://www.youtube.com/watch?v=b44ruhi5ji4).

**Disclaimer**: I am not currently hosting Swashbot on any stable VPS; this is more of a personal project hosted privately, but I think it's cool enough of a project to make this repository public and open source. Maybe in the future I will consider hosting Swashbot for universal use.

## Notes

Interact with Swashbot using some of the commands listed below.

Swashbot does not wash away **pinned messages**.

Requires Python **3.10** or greater.

### Gist of commands

* `~help` -- share a help leaflet
* `~current` -- get the current settings for the channel
* `~wave` -- 📝 erase the last 100 messages in the channel
* `~minutes 300` -- 📝🔧 erase messages after they've existed for 300 minutes (5 hours)
* `~atleast 10` -- 📝🔧 don't delete the current 10 most recent messages in the channel
* `~atmost 200` -- 📝🔧 never keep more than 200 messages in the channel

(📝 requires Manage Messages permission; 🔧 requires Manage Channel permission)
