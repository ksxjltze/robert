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
intents.reactions = True

bot = commands.Bot(command_prefix='$', intents = intents)

#Singapore Time
timezone = timezone(timedelta(hours=8))

#Initial Reminder Interval
seconds_interval = 0
minutes_interval = 0
hour_interval = 4

#seconds, minutes, hours
default_interval = [0, 0, 4]

#Interval constraints
minimum_second_interval = 5
minimum_minute_interval = 1

#Reminder default string
progress_string = "How's the progress over here?"

robert_guilds = {}

#Helpers
def split_timedelta(time):
    hours = time.total_seconds()//3600
    minutes = (time.total_seconds()//60) % 60
    seconds = round(time.total_seconds() - hours * 3600 - minutes * 60)

    return {"hours":int(hours), "minutes":int(minutes), "seconds":seconds}

#Tasks
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


class Progress(commands.Cog, name = "How to Progress"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    #cog test
    @commands.command(name = "hello")
    async def hello(self, ctx, *, member: discord.Member = None):
        """Says hello"""
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}~'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar.'.format(member))
        self._last_member = member

    @commands.command(name="when", brief="Displays the time of the next progress reminder.")
    async def when_progress(self, ctx):
        await ctx.channel.send(hows_the_progress.next_iteration)

    @commands.command(name="p", brief="INSTANT PROGRESS.")
    async def progress(self, ctx):
        await ctx.channel.send(progress_string)

    @commands.command(name="howlong", brief="Displays the time until next progress reminder.")
    async def how_long_until_progress(self, ctx):
        time_next = hows_the_progress.next_iteration - datetime.now(tz=timezone)
        time_next = split_timedelta(time_next)
        
        await ctx.channel.send(f'{time_next["hours"]} hours, {time_next["minutes"]} minutes, {time_next["seconds"]} seconds.')

    #not tested
    #TODO: isolate for each server
    @commands.command(name="setinterval", brief="Sets the progress reminder interval (Hours, Minutes, Seconds).", 
    help=
    "Sets the progress reminder interval (Seconds, Minutes, Hours).\n"
    "NOTE: Only applies after current reminder has been sent.\n"
    "Enter no arguments to reset to default interval.\n"
    "Minutes and seconds arguments can be omitted - e.g. '$setinterval 5' will set the interval to 5 hours.")
    async def set_progress_interval(self, ctx, hours = -1, minutes =0, seconds = 0):
        #default interval
        if (hours < 0):
            second_interval = default_interval[0]
            minute_interval = default_interval[1]
            hour_interval = default_interval[2]
        else:
            second_interval = seconds
            minute_interval = minutes
            hour_interval = hours

        if hour_interval == 0:
            if minute_interval == 0:
                second_interval = max(minimum_second_interval, second_interval)
            else:
                minute_interval = max(minimum_minute_interval, minute_interval)

        hows_the_progress.change_interval(seconds=second_interval, minutes=minute_interval, hours=hour_interval)
        await  ctx.channel.send(f'Set interval to {hour_interval} hours, {minute_interval} minutes, {second_interval} seconds.')

    @commands.command(name="restart", brief="Restarts the progress reminder task.")
    async def test_progress(self, ctx):
        hows_the_progress.restart()
        await ctx.channel.send("Restarting PROGRESS")


    @commands.command(name="toggle", brief="Toggles progress reminders.")
    async def toggle_reminders(self, ctx):
        print(f"Got channel {ctx.channel}")

        guild = robert_guilds[ctx.guild.id]
        guild["enabled"] = not guild["enabled"]

        is_enabled = guild["enabled"]
        print(f"Guild {guild['guild']} #{guild['channel']} - reminders: {is_enabled}")

        if robert_guilds[ctx.guild.id]["enabled"]:
            await ctx.channel.send("Progress reminders are now on.")
        else:
            await ctx.channel.send("Progress reminders are now off.")

    @commands.command(name="setchannel", brief="Sets the reminder channel.")
    async def set_reminder_channel(self, ctx, channel_name=None):
        message_channel = ctx.channel
        msg = ''

        if channel_name is not None:
            try:
                ch = ctx.guild.get_channel(int(channel_name)) #get by id
                found = False

                if ch is not None:
                    message_channel = ch
                    found = True
            except:
                guild_channels = await ctx.guild.fetch_channels()
                for gc in guild_channels:
                    if gc.name == channel_name:
                        message_channel = gc
                        found = True
                        break
            
            if not found:
                msg = "Channel not found."

        reminder = robert_guilds[ctx.guild.id]
        guild = reminder["guild"]

        reminder["channel"] = message_channel
        channel = reminder["channel"]

        print(f"Target channel for guild '{guild.name}' changed to #{channel.name} (id: {channel.id})")
        await ctx.channel.send(msg + f"\nReminders have been set to Channel #{channel.name}.")


class Messager(commands.Cog, name = "Messaging"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(name="pm", brief="Sends a message to a specified user.")
    async def pingpong(self, ctx, name):
        await ctx.guild.get_member_named(name).send(progress_string)

    @commands.command(name="pmid", brief="Sends a message to a specified user, using their discord id.")
    async def pingpong_id(self, ctx, id : int, msg = progress_string):
        user =  await bot.fetch_user(id)
        await user.send(msg)

        ret_msg = f"Sent message '{msg}' to user {user.name}"
        print(ret_msg)
        await ctx.channel.send(ret_msg)

    @commands.command(name="see", brief="Sees the message history between a user (id) and Robert Surov.")
    async def see_message(self, ctx, id, count = 1):
        ret_msg = ''

        user =  await bot.fetch_user(id)
        messages = await user.history(limit = count).flatten()

        for message in reversed(messages):
            ret_msg += message.author.name + ': ' + message.content + '\n'

        await ctx.channel.send(ret_msg)
    
class ServerUtils(commands.Cog, name = "Server Utilities"):
    @commands.command(name="members", brief="Displays the members of the current server." )
    async def show_members(self, ctx):
        message = 'Members: \n'

        for member in ctx.guild.members:
            member_string = member.name + f' ({member.id})\n'
            message += member_string

        print("Displaying Members:\n" + message)

        await ctx.channel.send(message)

class ProgressGame(commands.Cog, name = "Idle Game"):
    @commands.command(name="profile", brief="Displays your PROGRESS profile")
    async def show_profile(self, ctx):
        await ctx.channel.send("WIP")

#Events
@bot.event
async def on_reaction_add(reaction, user):
    await user.send("PROGRESS")

hows_the_progress.start()
bot.add_cog(Progress(bot))
bot.add_cog(Messager(bot))
bot.add_cog(ServerUtils(bot))
bot.run(TOKEN)