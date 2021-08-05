# DatePoll.py

# created with help from this guide on making bots for Discord:
# https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python

import asyncio
import datetime
import os
import pickle

import dateparser
import discord
from discord.ext import commands
from dotenv import load_dotenv

# import environment variables from the .env file
load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = os.getenv('DevEnvBot_TOKEN')

# default critical mass size
DEFAULT_CM = 2 ** 16
# make a bot and THE dictionary for player bot.availability
bot = commands.Bot(command_prefix='!')


# synchronous functions

# this is how we want the bot to display dates on Discord
def interpret_input(x):
    return x.strftime("%a, %b %d")


# when we parse days of the week, we assume that the user is talking about upcoming dates
def parse(x):
    return dateparser.parse(x, settings={'PREFER_DATES_FROM': 'future'})


# turns user input into a date range
# currently understands "from .. to" and "next [weekday]"
# I would like to make it so that "next two weeks" and such works, we'll see what the future holds
def read_dates(*args):
    # clean up input
    args = list(args)

    trash_strings = ("from", "starting", "the")
    for s in trash_strings:
        if s in args:
            args.remove(s)

    # turn args into a string
    date_list = ' '.join(args).split(" to ")

    # make "next [weekday]" work. Also, convert string input to dates
    for i in range(len(date_list)):
        if "next " in date_list[i] and date_list[i].index("next ") == 0:
            date_list[i] = parse(date_list[i].replace("next ", '')).date()
            if date_list[i].isocalendar()[1] == datetime.date.today().isocalendar()[1]:
                date_list[i] += datetime.timedelta(weeks=1)
        else:
            date_list[i] = parse(date_list[i]).date()

    if len(date_list) == 2:  # we have a range of multiple dates
        if date_list[0] > date_list[1]:
            # we assume that weekdays were given and that this caused issued
            date_list[1] += (1 + divmod((date_list[0] - date_list[1]).days, 7)[0]) * datetime.timedelta(weeks=1)
        num_days = date_list[1] - date_list[0]
        num_days = num_days.days
        date_range = [date_list[0] + datetime.timedelta(days=x) for x in range(num_days + 1)]
    else:  # we have just one date
        date_range = date_list
    return date_range


# turns a list of dates into a human readable string
def date_str(ctx, date_range):
    date_range.sort()

    # convert dates to strings and display in the channel
    display_list = [
        interpret_input(x) + "\t:\t" + ", ".join([y.name for y in bot.availability[ctx.guild.id].get(x, [])])
        for x in date_range if bot.availability[ctx.guild.id].get(x)]
    display_str = "\n".join(display_list)
    if not display_str:
        display_str = "No availability"
    return display_str


# generate the names of pickle files
def p_file(guild, prefix: str):
    avail_str = "pickle_jar/availability_" + str(guild.id) + ".p"
    cm_str = "pickle_jar/cm_" + str(guild.id) + ".p"
    if prefix:
        if prefix == "availability":
            return avail_str
        elif prefix == "cm":
            return cm_str
        else:
            raise ValueError("prefix should be 'availability' or 'cm'")
    else:
        return avail_str, cm_str


# determine if critical mass has been reached
def cm_reached(guild):
    for k in bot.availability[guild.id]:
        if len(bot.availability[guild.id][k]) >= bot.cm[guild.id]:
            bot.cm_bool[guild.id] = True
            return True
    bot.cm_bool[guild.id] = False
    return False


# asynchronous functions
async def alert_cm(ctx):
    date_range = [x for x, y in bot.availability[ctx.guild.id].items() if len(y) >= bot.cm[ctx.guild.id]]
    display_str = "critical mass of " + str(bot.cm[ctx.guild.id]) + " reached:\n" + date_str(ctx, date_range)
    await ctx.send(display_str)


# bot events

# what the bot does when it first wakes up
@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(bot.user.name + " has connected to Discord!")

    for guild in bot.guilds:
        print(guild.name)

    # use guild ids so that the bot can maintain different availability and critical mass dicts for different servers
    bot.availability = {}
    bot.cm = {}
    bot.cm_bool = {}
    for guild in bot.guilds:
        # work with availability
        try:
            # get availability from last session
            save_availability = pickle.load(file=open(p_file(guild, "availability"), "rb"))
            user_list = list(set([y for _, x in save_availability for y in x]))
            bot.user_dict = {}

            # reformat for convenience
            for x in user_list:
                bot.user_dict[x] = await guild.fetch_member(x)
            bot.availability[guild.id] = {x: set([bot.user_dict[z] for z in y]) for x, y in
                                          save_availability if x >= datetime.date.today()}
        except:
            bot.availability[guild.id] = {}

        # work with critical mass
        try:
            bot.cm[guild.id] = pickle.load(file=open(p_file(guild, "cm"), "rb"))
            cm_reached(guild)
        except:
            bot.cm[guild.id] = DEFAULT_CM
            bot.cm_bool[guild.id] = False


# make the necessary data structures when first added to a server
@bot.event
async def on_guild_join(guild):
    # may one day add functionality to remember old files when added
    bot.availability[guild.id] = {}
    bot.cm[guild.id] = DEFAULT_CM
    bot.cm_bool[guild.id] = False

@bot.event
async def on_guild_remove(guild):
    bot.availability.pop(guild.id)
    bot.cm.pop(guild.id)
    bot.cm_bool.pop(guild.id)
    os.remove(p_file(guild,"availability"))
    os.remove(p_file(guild, "cm"))



# bot commands

# Pure silliness
@bot.command(name='hello', help='hint: I was trained in your jedi arts by Count Dooku')
async def hello_there(ctx, *args):
    if not args:
        reply = "hello where?"
    elif "there" in args[0]:
        reply = "General Kenobi!"
    else:
        reply = "I have absolutely no idea what you're saying right now"
    await ctx.send(reply)


@bot.command(name="cm", help="define the critical mass before enough people have scheduled")
async def cm(ctx, n: int):
    if n >= 1:
        bot.cm[ctx.guild.id] = n
        pickle.dump(bot.cm[ctx.guild.id], open(p_file(ctx.guild, "cm"), "wb"))
        if cm_reached(ctx.guild):
            await alert_cm(ctx)
    else:
        raise ValueError("critical mass must be a positive integer.")


# Tell the user who is available and when
@bot.command(name="show", help="the bot will tell you who is available on upcoming dates \noptional input: date range")
async def show(ctx, *args):
    # get dates to display
    if args:
        date_range = read_dates(*args)
    else:
        date_range = [x for x in bot.availability[ctx.guild.id] if x >= datetime.date.today()]

    if bot.cm_bool[ctx.guild.id]:
        display_str = "critical mass of " + str(bot.cm[ctx.guild.id]) + " reached.\n"
    else:
        display_str = ""
    display_str += date_str(ctx, date_range)
    await ctx.send(display_str)


# tell the bot that you're available
@bot.command(name="add", help="tell the bot you're available on a given date or dates")
async def bot_add(ctx, *args: str):
    # get user
    user = ctx.author
    date_range = read_dates(*args)

    # add to bot.availability dictionary
    for d in date_range:
        if d in bot.availability[ctx.guild.id].keys():
            bot.availability[ctx.guild.id][d].add(user)
        else:
            bot.availability[ctx.guild.id][d] = {user}

    # pickle availability in case of shutdown
    save_availability = [(x, [z.id for z in y]) for x, y in bot.availability[ctx.guild.id].items()]
    pickle.dump(save_availability, open(p_file(ctx.guild, "availability"), "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.display_name + ", you've been marked available on " +
                   '; '.join([interpret_input(x) for x in date_range]))

    if not bot.cm_bool[ctx.guild.id]:
        if cm_reached(ctx.guild):
            await alert_cm(ctx)


# tell the bot you're unavailable
@bot.command(name="drop", help="tell the bot you're no longer available on a given date or dates")
async def bot_remove(ctx, *args: str):
    user = ctx.author
    if args[0] == "all":
        date_range = list(bot.availability[ctx.guild.id].keys())
    else:
        date_range = read_dates(*args)

    # add to bot.availability dictionary
    for d in date_range:
        if d in bot.availability[ctx.guild.id].keys():
            try:
                bot.availability[ctx.guild.id][d].remove(user)
            except:
                pass
            if not bot.availability[ctx.guild.id][d]:
                bot.availability[ctx.guild.id].pop(d)

    # pickle the availability in case of shutdown
    save_availability = [(x, [z.id for z in y]) for x, y in bot.availability[ctx.guild.id].items()]
    pickle.dump(save_availability, open(p_file(ctx.guild, "availability"), "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.display_name + ", you've been marked unavailable on " +
                   '; '.join([interpret_input(x) for x in date_range]))

    if bot.cm_bool[ctx.guild.id]:
        if not cm_reached(ctx.guild):
            await ctx.send("We have fallen below critical mass.")


# make buttons work
# with help from:
# https://gist.github.com/Rapptz/dbfd8cd945a9245e5504a54c2b9eda03

# class for the buttons that appear for the command '!poll'
class PollButton(discord.ui.Button['Poll']):
    def __init__(self, ctx: commands.Context, start_date: datetime.date, entry: int):
        # make button labels before calling __init__
        self.date = start_date + datetime.timedelta(days=entry)
        button_label = interpret_input(self.date)
        try:
            if bot.availability[ctx.guild.id][self.date]:
                print([x.guild.me.display_name for x in bot.availability[ctx.guild.id][self.date]])
                button_label += " : " + ', '.join([x.display_name for x in bot.availability[ctx.guild.id][self.date]])
        except:
            pass
        # entry = divmod(entry, 5)[0]
        super().__init__(style=discord.ButtonStyle.blurple, label=button_label, row=entry)

    # gets called when a button is pressed
    async def callback(self, interaction: discord.Interaction):
        # helps the button recognize that it's being pushed
        assert self.view is not None
        view: Poll = self.view

        # toggles whether the user pressing the button is in the availability dict
        try:
            if interaction.user in bot.availability[interaction.guild.id][self.date]:
                bot.availability[interaction.guild.id][self.date].remove(interaction.user)
            else:
                bot.availability[interaction.guild.id][self.date].add(interaction.user)
        except:
            bot.availability[interaction.guild.id][self.date] = {interaction.user}

        # pickles the availability dict in case of a shutdown
        save_availability = [(x, [z.id for z in y]) for x, y in bot.availability[interaction.guild.id].items()]
        pickle.dump(save_availability, open(p_file(interaction.guild, "availability"), "wb"))

        # update button label to show user's available on the button's date
        if bot.availability[interaction.guild.id][self.date]:
            self.label = interpret_input(self.date) + " : " + ', '.join(
                [x.display_name for x in bot.availability[interaction.guild.id][self.date]])
        else:
            self.label = interpret_input(self.date)

        # edit the results of the button-press into to the message
        await interaction.response.edit_message(view=view)

        # check for critical mass and send a message if critical mass is reached
        if bot.cm_bool[interaction.guild.id]:
            if not cm_reached(interaction.guild):
                await interaction.channel.send("We have fallen below critical mass.")
        else:
            if cm_reached(interaction.guild):
                await alert_cm(interaction.channel)


# class for a group of buttons appearing in a single message for the command '!pull'
class Poll(discord.ui.View):
    def __init__(self, ctx: commands.Context, start_date: datetime.date):
        super().__init__(timeout=None)  # timeout=None allows users to access

        for x in range(5):
            self.add_item(PollButton(ctx, start_date, x))


# function that creates a single message with buttons in it
async def poll_thread(ctx: commands.Context, content: str, start_date):
    await ctx.send(content, view=Poll(ctx, start_date))


# bot command to make a poll consisting of buttons across multiple messages
@bot.command(name="poll", help="buttons allow users to toggle availability \noptional input: number of days in poll")
async def poll(ctx: commands.Context, days: int = 20):
    # delete old polls first
    messages = await ctx.channel.history(limit=100).flatten()
    messages = [m for m in messages if ("!poll" in m.content and "!" == m.content[0]) or (
            m.author.id == bot.user.id and m.content in ("Poll:", "\u200b"))]
    for m in messages:
        await m.delete()

    # make a new poll with at least as many days as 'days'
    n = divmod(days - 1, 5)[0] + 1
    start_dates = [datetime.date.today() + datetime.timedelta(days=5 * x) for x in range(n)]
    poll_thread_list = [poll_thread(ctx, "Poll:", start_dates[0])] + [poll_thread(ctx, '\u200b', start_dates[i])
                                                                      for i in range(1, n)]
    await asyncio.gather(*poll_thread_list)


bot.run(TOKEN)
