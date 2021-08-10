# DatePoll

A Discord bot that keeps track of when guild members say they're available.

This bot has support for several text commands, 
but its primary feature is a poll with buttons that users can press.

## Using DatePollBot on Discord
The bot can be [added to your discord using this link.](https://discord.com/api/oauth2/authorize?client_id=869565481063948369&permissions=261523762368&scope=bot)

Once added, the command 
> !help

will show all available commands.
### Commands
* > !poll

will generate a sequence of 4 messages 
displaying a total of 20 buttons for guild members to click on. 
The message with the command and 
any polls appearing in the 100 most recent messages on the channel are first deleted.
Each button has a date in "Weekday, Month Day" format.
The dates appear sequential, starting from the current date in UTC.
When a member clicks on one of these buttons, 
their name will appear (or disappear) next to the date,
and their availability on that date will be stored in a calendar by the bot.

**Alternate command:**
> !poll [integer]

Will generate a sequence of messages with a total of [integer] buttons, 
rounded up to the nearest 5.
The content of these buttons is as described above.


* > !cm [integer]

This is the critical mass command.
Critical mass is initially set to a large integer (2^16).
Once this command is issued on a Discord server, 
the critical mass is set to [integer].
If every date on the calendar has fewer than [integer] guild members on it and
then at least one date gains a total of [integer] or more guild members,
then the bot will send a notification message informing the guild that
critical mass has been reached.

* > !show

will cause the bot to respond with a message 
showing all present and future availability of everyone on the calendar.

**Alternate commands:**
> !show [date range]

will show the availability of everyone on the calendar in the date range given.
date ranges are meant to be in natural language.

> !show cm

will show the availability of those on the calendar 
on dates which surpass critical mass, if defined.

* > !add [date range]

Adds the author of the message to the calendar 
on all dates provided in [date range].

**WARNING:** The label of a button in an active poll 
will not update to reflect changes made using text commands 
until the button is pressed.

* > !drop [date range]

Removes the author of the message from the calendar 
on all dates provided in [date range].

**WARNING:** The label of a button in an active poll 
will not update to reflect changes made using text commands 
until the button is pressed.

## Navigating this repository

### DatePoll.py
All of the functions, commands, methods, and classes for DatePollBot reside in *DatePoll.py*.
The code is organized into 6 sections: 
1. The header
2. global synchronous functions
3. global asynchronous functions
4. bot events
5. bot commands
6. all classes, methods, and functions needed for the "!poll" command.

Note that sections 2-5 exclude functions and bot commands used to make "!poll" work.

### pickle_jar/

*pickle_jar/* is a directory containing all of the ".p" pickle files used by the bot.
Pickling is used to save the calendar (*bot.availability[guild.id]*) as well as the critical mass 
of each guild using the bot. This is done so that nothing is lost if the bot is interrupted.

Each guild has its own pair of pickle files, one for availability and one for critical mass,
and these files are named using the guild's id to avoid ambiguity.

### .env
While not included on GitHub or other public databases, the code in *DatePoll.py*
relies on an environment file called *.env* kept in the same directory as *DatePoll.py*.
*.env* should be as follows:

> &#35; .env <br>
> DISCORD_TOKEN=[Discord bot token]

**WARNING:** Using a member token instead of a bot token will get you banned from Discord.
