# bot.py
import os
import asyncio
from datetime import datetime, time, date, timedelta, timezone

import discord
from discord.ext import commands, tasks
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='$', intents = intents)
timezone = timezone(timedelta(hours=8))
delay = timedelta(0, 0)
hour_interval = 2

progress_string = "How's the progress over here?"

the_time = datetime.now(tz=timezone)
#reminder_time = datetime(the_time.year, the_time.month, the_time.day, 20, 55, 0, 0, timezone)

reminder_channels = []

@tasks.loop(hours = hour_interval)
async def hows_the_progress():
    current_time = datetime.now(tz=timezone)
    reminder_time = current_time + delay
    time_until_reminder = reminder_time - current_time

    hours = time_until_reminder.total_seconds()//3600
    minutes = (time_until_reminder.total_seconds()//60) % 60
    seconds = round(time_until_reminder.total_seconds() - hours * 3600 - minutes * 60)

    print("Reminder Set.")
    print(f"Current Time: {current_time}")
    print("Waiting for {0:.0f} hours, {1:.0f} minutes, {2} seconds.".format(hours, minutes, seconds))

    await asyncio.sleep(time_until_reminder.total_seconds())
    for reminder in reminder_channels:        
        message_channel = reminder["channel"]
        print(f"Reminder Sent to channel {message_channel.name} of {message_channel.guild.name}.")
        await message_channel.send(progress_string)

@hows_the_progress.before_loop
async def before():
    await bot.wait_until_ready()

    #get guilds
    for guild in bot.guilds:
        print(f"Connected to guild '{guild.name}'")
        reminder_channels.append({"guild" : guild, "channel" : get(guild.channels, name='general')})
        
    print("\nReady.")

@bot.command(name="when")
async def when_progress(ctx):
    await ctx.channel.send(hows_the_progress.next_iteration)

def split_timedelta(time):
    hours = time.total_seconds()//3600
    minutes = (time.total_seconds()//60) % 60
    seconds = round(time.total_seconds() - hours * 3600 - minutes * 60)

    return {"hours":int(hours), "minutes":int(minutes), "seconds":seconds}

@bot.command(name="howlong")
async def how_long_until_progress(ctx):
    time_next = hows_the_progress.next_iteration - datetime.now(tz=timezone)
    time_next = split_timedelta(time_next)
    
    await ctx.channel.send(f'{time_next["hours"]} hours, {time_next["minutes"]} minutes, {time_next["seconds"]} seconds.')

@bot.command(name="p")
async def progress(ctx):
    await ctx.channel.send(progress_string)

@bot.command(name="pm")
async def pingpong(ctx, name):
    await ctx.guild.get_member_named(name).send(progress_string)

@bot.command(name="pmid")
async def pingpong_id(ctx, id : int):
    await ctx.guild.get_member(id).send(progress_string)
    
@bot.command(name="members")
async def show_members(ctx):
    message = 'Members: \n'

    for member in ctx.guild.members:
        member_string = member.name + f' ({member.id})\n'
        message += member_string

    print("Displaying Members:\n" + message)

    await ctx.channel.send(message)

@bot.command(name="toggle")
async def toggle_reminders(ctx):
    print(f"Got channel {ctx.channel}")
    if hows_the_progress.is_running():
        hows_the_progress.cancel()
        print("Reminders disabled.")
        await ctx.channel.send("Progress reminders are now off.")
    else:
        hows_the_progress.start()
        print("Reminders enabled.")
        await ctx.channel.send("Progress reminders are now on.")

@bot.command(name="setchannel")
async def set_reminder_channel(ctx, channel_name=None):
    if channel_name is None:
        message_channel = ctx.channel
    else:
        for channel in ctx.guild.channels:
            if (channel.name == channel_name):
                message_channel = channel
    
    for rc in reminder_channels:
        if (rc["guild"] == ctx.guild):
            rc["channel"] = message_channel
            reminder = rc
            break

    #Check guild and channel
    guild = reminder["guild"]
    channel = reminder["channel"]

    if (channel.id != message_channel.id):
        err_msg = "SUMTING WONG"
        print(err_msg)
        await channel.send(err_msg)
    else:
        print(f"Target channel for guild '{guild.name}' changed to #{channel.name} (id: {channel.id})")
        await channel.send(f"Reminders have been set to Channel #{message_channel.name}.")

hows_the_progress.start()
bot.run(TOKEN)