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

    @commands.command(name="when")
    async def when_progress(self, ctx):
        await ctx.channel.send(hows_the_progress.next_iteration)

    @commands.command(name="p")
    async def progress(self, ctx):
        await ctx.channel.send(progress_string)

    @commands.command(name="howlong")
    async def how_long_until_progress(self, ctx):
        time_next = hows_the_progress.next_iteration - datetime.now(tz=timezone)
        time_next = split_timedelta(time_next)
        
        await ctx.channel.send(f'{time_next["hours"]} hours, {time_next["minutes"]} minutes, {time_next["seconds"]} seconds.')

    #not tested
    #TODO: isolate for each server
    @commands.command(name="setinterval")
    async def set_progress_interval(self, ctx, seconds = -1, minutes = 0, hours = 0):
        #default interval
        if (seconds < 0):
            second_interval = default_interval[0]
            minute_interval = default_interval[1]
            hour_interval = default_interval[2]
        else:
            second_interval = seconds
            minute_interval = minutes
            hour_interval = hours

        hows_the_progress.change_interval(second_interval, minute_interval, hour_interval)
        await  ctx.channel.send(f'Set interval to {hour_interval} hours, {minute_interval} minutes, {second_interval} seconds.')

    @commands.command(name="restart")
    async def test_progress(self, ctx):
        hows_the_progress.restart()
        await ctx.channel.send("Restarting PROGRESS")


    @commands.command(name="toggle")
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

    @commands.command(name="setchannel")
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

    @commands.command(name="pm")
    async def pingpong(self, ctx, name):
        await ctx.guild.get_member_named(name).send(progress_string)

    @commands.command(name="pmid")
    async def pingpong_id(self, ctx, id : int, msg = progress_string):
        user =  await bot.fetch_user(id)
        await user.send(msg)

        ret_msg = f"Sent message '{msg}' to user {user.name}"
        print(ret_msg)
        await ctx.channel.send(ret_msg)

    @commands.command(name="see")
    async def see_message(self, ctx, id, count = 1):
        ret_msg = ''

        user =  await bot.fetch_user(id)
        messages = await user.history(limit = count).flatten()

        for message in reversed(messages):
            ret_msg += message.author.name + ': ' + message.content + '\n'

        await ctx.channel.send(ret_msg)
    
class ServerUtils(commands.Cog, name = "Server Utilities"):
    @commands.command(name="members")
    async def show_members(self, ctx):
        message = 'Members: \n'

        for member in ctx.guild.members:
            member_string = member.name + f' ({member.id})\n'
            message += member_string

        print("Displaying Members:\n" + message)

        await ctx.channel.send(message)

hows_the_progress.start()
bot.add_cog(Progress(bot))
bot.add_cog(Messager(bot))
bot.add_cog(ServerUtils(bot))
bot.run(TOKEN)