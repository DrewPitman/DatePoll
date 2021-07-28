# DatePoll.py

# created with help from this guide on making bots for Discord:
# https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python

import datetime
import os
import threading
import asyncio

import dateparser
import discord
from discord.ext import commands
from dotenv import load_dotenv

import pickle

# import environment variables from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
README_webhook_url = os.getenv('README_webhook_url')

# make a bot
bot = commands.Bot(command_prefix='!')

# make a dictionary for dates
availability = {}  # date : user_id pairs
pickle.dump(availability, open("availability.p", "wb"))

weekday_tup = (
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday', 'Sunday')


# this is how we want the bot to display dates on Discord
def interpret_input(x):
    return x.strftime("%a, %b %d")


# when we parse days of the week, we assume that the user is talking about upcoming dates
def parse(x):
    return dateparser.parse(x, settings={'PREFER_DATES_FROM': 'future'})


# a function to turn user input into a date range
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
    print("date_list:", date_list)

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


# bot events and commands

# say hi so I know it's running
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


# Testing
@bot.command(name='HelloThere', help='Was trained in your jedi arts by Count Dooku')
async def say_hello(ctx):
    reply = "General Kenobi!"
    await ctx.send(reply)


# Tell the user who is available and when
@bot.command(name="show", help="the bot will tell you who is available and when")
async def show(ctx, *args):
    if args:
        date_range = read_dates(*args)
    else:
        date_range = [x for x in availability if x >= datetime.date.today()]

    date_range.sort()

    display_list = [interpret_input(x) + "\t:\t" + ", ".join([y.name for y in availability.get(x, [])])
                    for x in date_range if availability.get(x)]
    display_str = "\n".join(display_list)
    if not display_str:
        display_str = "No availability"
    print(type(ctx))
    await ctx.send(display_str)


# tell the bot that you're available
@bot.command(name="add", help="tells the bot you're available on a given date or dates")
async def bot_add(ctx, *args: str):
    # get user
    user = ctx.author
    print("user: ", user)
    date_range = read_dates(*args)

    # add to availability dictionary
    for d in date_range:
        if d in availability.keys():
            availability[d].add(user)
        else:
            availability[d] = {user}


    pickle.dump(availability, open("availability.p", "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.name + ", you've been marked available on " +
                   '; '.join([interpret_input(x) for x in date_range]))


# tell the bot you're unavailable
@bot.command(name="remove", help="tells the bot you're no longer available on a given date or dates")
async def bot_remove(ctx, *args: str):
    # get user
    user = ctx.author
    print("user: ", user)
    date_range = read_dates(*args)

    # add to availability dictionary
    for d in date_range:
        if d in availability.keys():
            try:
                availability[d].remove(user)
            except:
                pass

    save_availability = {x:set([z.id for z in y]) for x,y in availability.items()}
    pickle.dump(save_availability, open("availability.p", "wb"))

    # inform the user
    await ctx.send("Thanks " + ctx.author.name + ", you've been marked unavailable on " +
                   '; '.join([interpret_input(x) for x in date_range]))


# make buttons work
# with help from:
# https://gist.github.com/Rapptz/dbfd8cd945a9245e5504a54c2b9eda03

class PollButton(discord.ui.Button['Poll']):
    def __init__(self, ctx: commands.Context, start_date: datetime.date, entry: int):
        self.date = start_date + datetime.timedelta(days=entry)
        try:
            button_label = interpret_input(self.date) + " : " + ', '.join([x.name for x in availability[self.date]])
        except:
            button_label = interpret_input(self.date)
        # entry = divmod(entry, 5)[0]
        super().__init__(style=discord.ButtonStyle.blurple, label=button_label, row=entry)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Poll = self.view
        try:
            if self.ctx.author in availability[self.date]:
                availability[self.date].remove(self.ctx.author)
            else:
                availability[self.date].add(self.ctx.author)
        except:
            availability[self.date] = {self.ctx.author}

        save_availability = {x: set([z.id for z in y]) for x, y in availability.items()}
        pickle.dump(save_availability, open("availability.p", "wb"))

        if availability[self.date]:
            self.label = interpret_input(self.date) + " : " + ', '.join([x.name for x in availability[self.date]])
        else:
            self.label = interpret_input(self.date)

        await interaction.response.edit_message(view=view)

class Poll(discord.ui.View):
    def __init__(self, ctx: commands.Context, start_date: datetime.date):
        super().__init__()

        for x in range(5):
            self.add_item(PollButton(ctx, start_date, x))


async def poll_thread(ctx: commands.Context, content: str, start_date):
    await ctx.send(content, view=Poll(ctx, start_date))

@bot.command(name="poll", help="a poll that allows users to toggle availability without text commands")
async def poll(ctx: commands.Context):
    start_dates = [datetime.date.today() + datetime.timedelta(days=5 * x) for x in range(3)]

    await asyncio.gather(
        poll_thread(ctx, "Poll:\npart 1", start_dates[0]),
        poll_thread(ctx, "part 2", start_dates[1]),
        poll_thread(ctx, 'part 3', start_dates[2])
    )


bot.run(TOKEN)

print("yes, hello, I am the heres!")