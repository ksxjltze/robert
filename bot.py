# bot.py
import os
import asyncio
from datetime import datetime, date, timedelta, timezone

import discord
from discord.ext import commands, tasks
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
timezone = timezone(timedelta(hours=8))
delay = timedelta(0, 0)

the_time = datetime.now(tz=timezone)
#reminder_time = datetime(the_time.year, the_time.month, the_time.day, 20, 55, 0, 0, timezone)

reminder_channels = []

@tasks.loop(hours = 1)
async def called_once_a_day():
    for guild in bot.guilds:
        print(f"Connected to guild '{guild.name}'")
        reminder_channels.append({"guild" : guild, "channel" : get(guild.channels, name='general')})

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
        #await message_channel.send("How's the progress over here?")

@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    print("\nReady.")
    
@bot.command(name="toggle")
async def toggle_reminders(ctx):
    print(f"Got channel {ctx.channel}")
    if called_once_a_day.is_running():
        called_once_a_day.cancel()
        print("Reminders disabled.")
        await ctx.channel.send("Progress reminders are now off.")
    else:
        called_once_a_day.start()
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
    

    
called_once_a_day.start()
bot.run(TOKEN)