# Swashbot documentation

**Swashbot** is a Discord bot that washes messages away over time like [gentle beach waves](https://www.youtube.com/watch?v=b44ruhi5ji4).

Inspired by friends' privacy concerns about message permanence on Discord, in comparison to ephemeral messaging schemes (for instance, Signal's disappearing messages feature).

[**Swashbot documentation**](#swashbot-documentation)<br/>
&emsp;&emsp;[High-level behavior](#high-level-behavior)<br/>
&emsp;&emsp;&emsp;&emsp;[Zones](#zones)<br/>
&emsp;&emsp;&emsp;&emsp;[Commands](#commands)<br/>
&emsp;&emsp;[Low-level behavior](#low-level-behavior)<br/>
&emsp;&emsp;&emsp;&emsp;[Project structure](#project-structure)<br/>
&emsp;&emsp;&emsp;&emsp;[Working memory](#working-memory)<br/>
&emsp;&emsp;&emsp;&emsp;[Long-term memory](#long-term-memory)<br/>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;[`memo`](#memo)<br/>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;[`prefixes`](#prefixes)<br/>
&emsp;&emsp;&emsp;&emsp;[Complexity analysis](#complexity-analysis)<br/>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;[Space complexity](#space-complexity)<br/>
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;[Time complexity](#time-complexity)<br/>
&emsp;&emsp;[Planned updates](#planned-updates)<br/>
&emsp;&emsp;&emsp;&emsp;[Known bugs](#known-bugs)<br/>
&emsp;&emsp;&emsp;&emsp;[Potential future features](#potential-future-features)<br/>
[**EOF**](#eof)

## High-level behavior

[^ Jump to top](#swashbot-documentation)

With Swashbot, server moderators (specifically, users with the `Manage Channels` permission) can set how much time it takes messages in a channel to erase. In addition, Swashbot can be told to always keep a minimum amount of messages in the channel, as well as to maintain a maximum limit. These three degrees of freedom define three zones, explained below.

Sadly, since users can't befriend bots, and since, even if they could, there's no `Manage Messages` permission in group DMs, Swashbot cannot be used in private group DMs. A cumbersome workaround might be to create a small server with one channel.

### Zones

[^ Jump to top](#swashbot-documentation)

Swashbot washes away messages in a channel according to three zones:

1. **Shore face**: This zone represents messages furthest into the past, or equivalently, furthest up in a channel's history. Swashbot deletes any messages reaching this zone, no matter how short of a time has passed. The limit of this zone may be specified by defining the maximum amount of messages `m` allowed in the channel via the `~at most m` command.
2. **Swash zone**: These messages are erased according to a set time. This expiration time `t` in minutes may be set by the `~time t` command.
3. **Back shore**: The opposite of the shore face, this zone represents the most recent messages in a channel. Swashbot keeps these messages regardless of how much time has passed, until they enter the swash zone. The number of messages in the back shore `m` may be set by the `~at least m` command.

![(Figure describing the three zones visually)](img/zones.png)

Credit for image on left side: [Alex Perez (@a2eorigins) via Unsplash](https://unsplash.com/photos/Iul_cHtH4NY)

### Commands

[^ Jump to top](#swashbot-documentation)

|       Group | Command & syntax | Description                                                  |
| ----------: | :--------------: | :----------------------------------------------------------- |
|        Meta |     `~help`      | Provides a link to this documentation as well as a list of example commands to get the gist. |
|        Meta |     `~info`      | Display some information about the current instance of Swashbot, including a link to this repository and the current commit Swashbot is operating at. |
|        Meta |   `~prefix p`    | Change the bot prefix to `p`. For instance, `~prefix $$` would change the bot prefix to `$$`. Works on a server-by-server basis. No more than four characters. |
| Fundamental |  `~at least m`   | Always keep the `m` most recent messages in the channel. Defines the size of the [back shore](#zones). |
| Fundamental |   `~at most m`   | Keep the channel's message count at most `m` by deleting the oldest messages in the channel. Defines where the [shore face](#zones) begins. |
| Fundamental |    `~current`    | Display current settings for the channel.                    |
| Fundamental |    `~time t`     | Any messages in the [swash zone](#zones) will be erased after `t` minutes. |
| Fundamental |    `~wave m`     | Wash away the last `m` messages. `~wave` without providing the `m` parameter defaults to washing away 100 messages. |

Note that values for `m` and `t` in the commands above also include `0` and `inf` (infinity).

To quickly reset a channel's settings, use `~at least inf`, since this is essentially telling Swashbot to keep an infinite amount of messages in the channel.

## Low-level behavior

[^ Jump to top](#swashbot-documentation)

Swashbot is an instance of a class called `Swashbot` that inherits from [`discord.Client`](https://discordpy.readthedocs.io/en/latest/api.html#client).

It has an `async` task for each channel it swashes over.

### Project structure

[^ Jump to top](#swashbot-documentation)

* `config.py` -- place bot token here
* `run.py` -- run Swashbot
* `swashbot/`
  * `client.py` -- where the Swashbot class is written
  * `debug.py` -- code that helps me debug
  * `utils.py` -- helper classes and functions
  * `cmds/` -- folder containing all the commands' code

### Working memory

[^ Jump to top](#swashbot-documentation)

The most important variables Swashbot keeps track of are `memo`, `prefixes`, and `flotsam`.

`memo` is a dict keyed by channel ID that keeps track of channels' settings.

`prefixes` is a dict keyed by server ID that keeps track of servers' prefixes.

`flotsam` is a dict keyed by channel ID that keeps track of all messages within the swash zone and back shore in the channel via noting the message ID and message creation date.

### Long-term memory

[^ Jump to top](#swashbot-documentation)

In the case of Discord outages, updating code, and other script reboots, Swashbot uses a SQLite database file to remember which channels it should be keeping track of. By default, the file is called `swashbot.ltm` and will henceforce be referred to as Swashbot's LTM.

In Swashbot's LTM, there are two tables: `memo` and `prefixes`.

These tables store server and/or channel IDs as `INTEGER` types. Note that since an `INTEGER` in a SQLite3 database is a *signed* 64-bit integer and thus may be at greatest <img src="https://render.githubusercontent.com/render/math?math=2^{63}-1=9223372036854775807">, we may want to figure out in what circumstances the [*unsigned* 64-bit integer channel and server IDs](https://discord.com/developers/docs/reference#snowflakes) might break this ceiling. According to the Discord documentation, the 42 most significant bits of the ID represent milliseconds since the first second of 2015 (Discord Epoch). Thus, IDs are expected to break the ceiling of a signed SQLite3 integer starting around <img src="https://render.githubusercontent.com/render/math?math=2^{42}=2199023255552"> milliseconds since Discord Epoch, or around Wednesday, September 6, 2084. So, remind me to do something about that by then :ok_hand:

#### `memo`

[^ Jump to top](#swashbot-documentation)

|       `channel`       |  `guild`  | `at_least` | `at_most` |  `time_`  |
| :-------------------: | :-------: | :--------: | :-------: | :-------: |
| `INTEGER PRIMARY KEY` | `INTEGER` | `INTEGER`  | `INTEGER` | `INTEGER` |

`at_least`, `at_most`, and `time_` may be null, representing infinity.

`guild` is the ID of the server, and `channel` is the ID of the channel.

#### `prefixes`

[^ Jump to top](#swashbot-documentation)

|        `guild`        | `prefix` |
| :-------------------: | :------: |
| `INTEGER PRIMARY KEY` |  `TEXT`  |

`guild` is the snowflake ID of the server or group DM channel.

### Complexity analysis

[^ Jump to top](#swashbot-documentation)

Quantities to describe the space and runtime complexity:

|                           Quantity                           |                         Description                          |
| :----------------------------------------------------------: | :----------------------------------------------------------: |
| <img src="https://render.githubusercontent.com/render/math?math=n"> |           Total number of servers Swashbot swashes           |
| <img src="https://render.githubusercontent.com/render/math?math=c_i"> | Number of channels Swashbot swashes in server <img src="https://render.githubusercontent.com/render/math?math=i"> |
| <img src="https://render.githubusercontent.com/render/math?math=c=\sum_{i\in[0,n)}c_i"> |          Total number of channels Swashbot swashes           |
| <img src="https://render.githubusercontent.com/render/math?math=m_{ij}"> | Number of messages in channel <img src="https://render.githubusercontent.com/render/math?math=j"> of server <img src="https://render.githubusercontent.com/render/math?math=i"> |
| <img src="https://render.githubusercontent.com/render/math?math=m=\sum_{i\in[0,n)}\sum_{j\in[0,c_i)}m_{ij}"> |    Total number of messages Swashbot has to keep track of    |

Note: <img src="https://render.githubusercontent.com/render/math?math=O(n)\in O(c)\in O(m)"> 

#### Space complexity

[^ Jump to top](#swashbot-documentation)

Since Swashbot keeps track of how many messages are in the back shore and swash zone, Swashbot's RAM space complexity <img src="https://render.githubusercontent.com/render/math?math=\Theta(m)">. There are ways to implement Swashbot's operations with a handful of <img src="https://render.githubusercontent.com/render/math?math=\Theta(1)">-size pointers & variables for <img src="https://render.githubusercontent.com/render/math?math=\Theta(c)"> space, but with how I envision it, that would require less agile performance and more API requests.

Since Swashbot's LTM needs only to keep track of a channel's settings, and not any messages in the channels, the space of complexity of Swashbot's LTM is <img src="https://render.githubusercontent.com/render/math?math=\Theta(c)">.

#### Time complexity

[^ Jump to top](#swashbot-documentation)

|                           Operation, event, or command |                       Time complexity                        |
| -----------------------------------------------------: | :----------------------------------------------------------: |
|                                     Bot initialization | <img src="https://render.githubusercontent.com/render/math?math=\Theta(m)"> |
|                               Washing away one message | <img src="https://render.githubusercontent.com/render/math?math=\Theta(1)"> |
|           New non-command message appears in a channel | <img src="https://render.githubusercontent.com/render/math?math=\Theta(1)"> |
| Message is deleted (by any client other than Swashbot) | <img src="https://render.githubusercontent.com/render/math?math=\Theta(1)"> |
| Bulk message deletion (by any bot other than Swashbot) | Not yet implemented -- intended to be <img src="https://render.githubusercontent.com/render/math?math=O(m_{ij})"> |
|                           Swashbot removed from server | Not yet implemented -- intended to be <img src="https://render.githubusercontent.com/render/math?math=O(1)"> |
|                                  `~at least m` command | <img src="https://render.githubusercontent.com/render/math?math=\Omega(1)">, <img src="https://render.githubusercontent.com/render/math?math=O(m_{ij})"> |
|                                   `~at most m` command | <img src="https://render.githubusercontent.com/render/math?math=\Omega(1)">, <img src="https://render.githubusercontent.com/render/math?math=O(m_{ij})"> |
|                                      `~time t` command | <img src="https://render.githubusercontent.com/render/math?math=\Omega(1)">, <img src="https://render.githubusercontent.com/render/math?math=O(m_{ij})"> |
|                                      `~wave m` command | <img src="https://render.githubusercontent.com/render/math?math=\Omega(1)">, <img src="https://render.githubusercontent.com/render/math?math=O(m_{ij})"> |

## Planned updates

[^ Jump to top](#swashbot-documentation)

### Known bugs

[^ Jump to top](#swashbot-documentation)

* What happens if an entire server forgets their prefix?
* What happens if two commands are sent within half a second of each other (e.g. worst case might be `~at most inf` followed by `~at most 0`)?
* Users may be able to get around the `Manage Channels` requirement by proxying via a webhook or bot. (Discord users who know what I mean by that will know what I mean by that.)
* When Swashbot is removed from a server, it doesn't (yet) automatically stop its `async` tasks appropriately. This isn't exactly fatal, but it's not elegant.
* When a bot bulk deletes messages in a channel, Swashbot doesn't (yet) refresh its `flotsam` variable appropriately. This isn't exactly fatal, but it's not elegant.

### Potential future features

[^ Jump to top](#swashbot-documentation)

* Would be convenient if Swashbot accepted units of time, like `~time 24h` or `~time 30d`.
* Alternatively, would be cool if Swashbot could perform arithmetic, like `~time 24*60`  or `~time 30*24*60`.
* Maybe have an explicit `~reset` sort of command that quickly resets the channel settings? Note that `~at least inf` does this, but that's not exactly obvious to new users.
* Cleaner error handling
* Fancy transparent analytics:
  * Track how many warnings pop up
  * Track how many of each type of warning (e.g. `discord.NotFound`, `discord.HTTPException`) pops up
* Make the bot more personable

# EOF

[^ Jump to top](#swashbot-documentation)