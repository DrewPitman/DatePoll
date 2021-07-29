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
TOKEN = os.getenv('DISCORD_TOKEN')

# make a bot and THE dictionary for player bot.availability
bot = commands.Bot(command_prefix='!')



@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'{bot.user.name} has connected to Discord!')

    for guild in bot.guilds:
        print(guild.name)
    # assign availabilities
    # use guild id string to make it so that the bot can save different availability dicts to different servers
    bot.save_availability = pickle.load(file=open("availability.p", "rb"))
    user_list = list(set([y for _, x in bot.save_availability for y in x]))
    bot.user_dict = {}

    # prepare bot.availability from last session
    for x in user_list:
        bot.user_dict[x] = await bot.fetch_user(x)
    bot.availability = {x: set([bot.user_dict[z] for z in y]) for x, y in bot.save_availability if
                        x >= datetime.date.today()}


# this is how we want the bot to display dates on Discord
def interpret_input(x):
    return x.strftime("%a, %b %d")


# when we parse days of the week, we assume that the user is talking about upcoming dates
def parse(x):
    return dateparser.parse(x, settings={'PREFER_DATES_FROM': 'future'})


# a function to turn user input into a date range
# currently understands "from .. to" and "next [weekday]"
def read_dates(*args):
    # clean up input
    args = list(args)

    trash_strings = ("from", "starting")
    for s in trash_strings:
        if s in args:
            args.remove(s)

    # turn args into a string
    date_list = ' '.join(args).split(" to ")

    # make "next [weekday]" work
    for i in range(len(date_list)):
        if "next " in date_list[i] and date_list[i].index("next ") == 0:
            date_list[i] = parse(date_list[i].replace("next ", '')).date()
            if date_list[i].isocalendar()[1] == datetime.date.today().isocalendar()[1]:
                date_list[i] += datetime.timedelta(weeks=1)
        else:
            date_list[i] = parse(date_list[i]).date()

    # I would like to make it so that "next two weeks" and such works

    if len(date_list) == 2:
        if date_list[0] > date_list[1]:
            # we assume that weekdays were given and that this caused issued
            date_list[1] += (1 + divmod((date_list[0] - date_list[1]).days, 7)[0]) * datetime.timedelta(weeks=1)
        num_days = date_list[1] - date_list[0]
        num_days = num_days.days
        date_range = [date_list[0] + datetime.timedelta(days=x) for x in range(num_days + 1)]
    else:
        date_range = date_list
    return date_range


# bot commands

# Testing
@bot.command(name='hello', help='Was trained in your jedi arts by Count Dooku')
async def hello_there(ctx, *args):
    if "there" in args[0]:
        reply = "General Kenobi!"
    else:
        reply = "where?"
    await ctx.send(reply)


# Tell the user who is available and when
@bot.command(name="show", help="the bot will tell you who is available and when")
async def show(ctx, *args):
    if args:
        date_range = read_dates(*args)
    else:
        date_range = [x for x in bot.availability if x >= datetime.date.today()]

    date_range.sort()

    display_list = [interpret_input(x) + "\t:\t" + ", ".join([y.name for y in bot.availability.get(x, [])])
                    for x in date_range if bot.availability.get(x)]
    display_str = "\n".join(display_list)
    if not display_str:
        display_str = "No availability"
    await ctx.send(display_str)


# tell the bot that you're available
@bot.command(name="add", help="tells the bot you're available on a given date or dates")
async def bot_add(ctx, *args: str):
    # get user
    user = ctx.author
    date_range = read_dates(*args)

    # add to bot.availability dictionary
    for d in date_range:
        if d in bot.availability.keys():
            bot.availability[d].add(user)
        else:
            bot.availability[d] = {user}

    bot.save_availability = [(x, [z.id for z in y]) for x, y in bot.availability.items()]
    pickle.dump(bot.save_availability, open("availability.p", "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.name + ", you've been marked available on " +
                   '; '.join([interpret_input(x) for x in date_range]))


# tell the bot you're unavailable
@bot.command(name="remove", help="tells the bot you're no longer available on a given date or dates")
async def bot_remove(ctx, *args: str):
    # get user
    user = ctx.author
    date_range = read_dates(*args)

    # add to bot.availability dictionary
    for d in date_range:
        if d in bot.availability.keys():
            try:
                bot.availability[d].remove(user)
            except ValueError:
                pass

    bot.save_availability = [(x, [z.id for z in y]) for x, y in bot.availability.items()]
    pickle.dump(bot.save_availability, open("availability.p", "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.name + ", you've been marked unavailable on " +
                   '; '.join([interpret_input(x) for x in date_range]))


# make buttons work
# with help from:
# https://gist.github.com/Rapptz/dbfd8cd945a9245e5504a54c2b9eda03

class PollButton(discord.ui.Button['Poll']):
    def __init__(self, start_date: datetime.date, entry: int):
        self.date = start_date + datetime.timedelta(days=entry)
        button_label = interpret_input(self.date)
        try:
            button_label += " : " + ', '.join([x.name for x in bot.availability[self.date]])
        except KeyError:
            pass
        # entry = divmod(entry, 5)[0]
        super().__init__(style=discord.ButtonStyle.blurple, label=button_label, row=entry)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Poll = self.view
        try:
            if interaction.user in bot.availability[self.date]:
                bot.availability[self.date].remove(interaction.user)
            else:
                bot.availability[self.date].add(interaction.user)
        except KeyError:
            bot.availability[self.date] = {interaction.user}

        bot.save_availability = [(x, [z.id for z in y]) for x, y in bot.availability.items()]
        pickle.dump(bot.save_availability, open("availability.p", "wb"))

        if bot.availability[self.date]:
            self.label = interpret_input(self.date) + " : " + ', '.join([x.name for x in bot.availability[self.date]])
        else:
            self.label = interpret_input(self.date)

        await interaction.response.edit_message(view=view)


class Poll(discord.ui.View):
    def __init__(self, start_date: datetime.date):
        super().__init__(timeout=None)  # timeout=None allows users to access

        for x in range(5):
            self.add_item(PollButton(start_date, x))


async def poll_thread(ctx: commands.Context, content: str, start_date):
    await ctx.send(content, view=Poll(start_date))


@bot.command(name="poll", help="a poll that allows users to toggle bot.availability without text commands")
async def poll(ctx: commands.Context):
    start_dates = [datetime.date.today() + datetime.timedelta(days=5 * x) for x in range(3)]

    await asyncio.gather(
        poll_thread(ctx, "Poll:", start_dates[0]),
        poll_thread(ctx, '\u200b', start_dates[1]),
        poll_thread(ctx, '\u200b', start_dates[2])
    )


bot.run(TOKEN)
