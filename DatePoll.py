# DatePoll.py

# created with help from this guide on making bots for Discord:
# https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python

import datetime
import os

from dateparser import parse
from discord.ext import commands
from dotenv import load_dotenv

# import pickle

# import environment variables from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
README_webhook_url = os.getenv('README_webhook_url')

# make a bot
bot = commands.Bot(command_prefix='!')

# make a dictionary for dates
availability = {}  # date : user_id pairs


# say hi so I know it's running
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


# Testing
@bot.command(name='HelloThere', help='Was trained in your jedi arts by Count Dooku')
async def say_hello(ctx):
    reply = "General Kenobi!"
    await ctx.send(reply)


# Tell me that you're available
@bot.command(name="available", help="tells the bot you're available on a given date at a given time")
async def available(ctx, *args: str):
    # get user
    user = ctx.author
    print("user: ", user)
    # clean up input
    trash_strings = ("from", "starting")
    for s in trash_strings:
        if s in args:
            args = list(args)
            args.remove(s)
    args = ' '.join(args)

    # deal with date ranges
    args = args.split(" to ")
    if len(args) == 2:
        start_date = parse(args[0])
        end_date = parse(args[1])
        num_days = end_date - start_date
        num_days = num_days.days
        date_range = [start_date + datetime.timedelta(days=x) for x in range(num_days)]
    else:
        date_range = [parse(args[0])]

    # add to availability dictionary
    for d in date_range:
        d_date = d.date()
        if d_date in availability.keys():
            availability[d_date].add(user)
        else:
            availability[d_date] = {user}
    print(date_range)
    print(availability)
    # time = avail.time()
    await ctx.send("Thanks!")


bot.run(TOKEN)
# TEST_PUSH 1