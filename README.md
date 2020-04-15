# swashbot

Discord bot that removes messages [like gentle beach waves](https://www.youtube.com/watch?v=b44ruhi5ji4).

**Disclaimer**: This is a bot meant for personal use and meant to work in a single channel in a single server. To expand the functionality to multiple channels or servers, take a look at the code and, for instance, change the `options` dict into a dict that maps `{server_id}:{channel_id}` pairs to their own `options` dicts. In that case, I'd recommend ditching `pickle` for serializing and use something faster & better suited to many small changes within a relatively large database (e.g. SQLite3, MessagePack, I haven't looked into it much). I might implement these changes with time, but no promises.

## Notes

Interact with Swashbot by mentioning the bot with the `@` symbol, followed by the command and potential arguments.

Swashbot does not wash away pinned messages.

### Gist of commands

* `@Swashbot here`: Set the channel that Swashbot washes
* `@Swashbot help`: Get the current settings for the channel
* `@Swashbot at least 10`: Always have at least 10 messages in the channel
* `@Swashbot at most 50`: Always have no more than
* `@Swashbot time 60`: Messages within the at-least/at-most range will wash away after an hour (60 minutes) since they were first posted
* `@Swashbot time 0`: Shortcut to set the `at least` setting to the current `at most` setting
* `@Swashbot time inf`: Disable time-based message deletions
* `@Swashbot tsunami`: Delete the last 100 messages

## Set-up

* Create a bot over at [the Discord dev portal](https://discordapp.com/developers/applications) and invite it to your server (OAuth2 tab). Make sure to give it permission to `Read Message History`, `Manage Messages`, and `Send Messages`.
* Set an environment variable called `SWASHBOT_TOKEN` to contain your bot's token.
* As one does, run `swashbot.py` with Python 3.6+ and the latest `discord.py` module.
* Set the channel using `@Swashbot here`. The initial set of options is to delete all messages past count 50.