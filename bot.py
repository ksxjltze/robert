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

seconds_interval = 0
minutes_interval = 0
hour_interval = 4

#seconds, minutes, hours
default_interval = [0, 0, 4]

progress_string = "How's the progress over here?"

the_time = datetime.now(tz=timezone)
#reminder_time = datetime(the_time.year, the_time.month, the_time.day, 20, 55, 0, 0, timezone)

robert_guilds = {}

@tasks.loop(seconds = seconds_interval, minutes = minutes_interval, hours = hour_interval)
async def hows_the_progress():
    for guild_id, guild in robert_guilds.items():
        if guild["enabled"]:
            message_channel = guild["channel"]
            print(f"Reminder Sent to channel #{message_channel.name} of {message_channel.guild.name} ({guild_id}).")
            await message_channel.send(progress_string)

@hows_the_progress.before_loop
async def before():
    await bot.wait_until_ready()

    #get guilds
    for guild in bot.guilds:
        print(f"Connected to guild '{guild.name}'")

        if guild.id not in robert_guilds:
            print(f"Registering guild {guild.name} ({guild.id}, setting channel to #general)")
            guild_channel = {"guild" : guild, "channel" : get(guild.channels, name='general'), "enabled" : False}
            robert_guilds[guild.id] = guild_channel
        
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

#not tested
#TODO: isolate for each server
@bot.command(name="setinterval")
async def set_progress_interval(ctx, seconds = -1, minutes = 0, hours = 0):

    #default interval
    if (seconds < 0):
        second_interval = default_interval[0]
        minute_interval = default_interval[1]
        hour_interval = default_interval[2]
    else:
        second_interval = seconds
        minute_interval = minutes
        hour_interval = hours

    await  ctx.channel.send(f'Set interval to {hour_interval} hours, {minute_interval} minutes, {second_interval} seconds.')


@bot.command(name="p")
async def progress(ctx):
    await ctx.channel.send(progress_string)

@bot.command(name="pm")
async def pingpong(ctx, name):
    await ctx.guild.get_member_named(name).send(progress_string)

@bot.command(name="pmid")
async def pingpong_id(ctx, id : int, msg = progress_string):
    user =  await bot.fetch_user(id)
    await user.send(msg)

    ret_msg = f"Sent message '{msg}' to user {user.name}"
    print(ret_msg)
    await ctx.channel.send(ret_msg)

@bot.command(name="restart")
async def test_progress(ctx):
    hows_the_progress.restart()
    await ctx.channel.send("Restarting PROGRESS")
    
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

    guild = robert_guilds[ctx.guild.id]
    guild["enabled"] = not guild["enabled"]

    is_enabled = guild["enabled"]
    print(f"Guild {guild['guild']} - {guild['channel']} reminders: {is_enabled}")

    if robert_guilds[ctx.guild.id]["enabled"]:
        await ctx.channel.send("Progress reminders are now on.")
    else:
        await ctx.channel.send("Progress reminders are now off.")

@bot.command(name="setchannel")
async def set_reminder_channel(ctx, channel_name=None):
    if channel_name is None:
        message_channel = ctx.channel
    else:
        message_channel = robert_guilds[ctx.guild.id]["channel"]

    reminder = robert_guilds[ctx.guild.id]
    guild = reminder["guild"]
    channel = reminder["channel"]

    reminder["channel"] = message_channel

    print(f"Target channel for guild '{guild.name}' changed to #{channel.name} (id: {channel.id})")
    await ctx.channel.send(f"Reminders have been set to Channel #{channel.name}.")

hows_the_progress.start()
bot.run(TOKEN)