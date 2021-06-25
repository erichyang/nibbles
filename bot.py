import asyncio

import discord
import os
import random
import pytz

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
from itertools import cycle
from threading import Thread
import time
from datetime import datetime, date, timedelta

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents.all())
client.remove_command('help')

status = cycle([
    'cookie nomming', 'sleeping', 'being a ball of fluff', 'wheel running',
    'tunnel digging', 'wires nibbling', 'food stashing', 'treasure burying',
    'grand adventure', 'collecting taxes'
])

for filename in os.listdir('./util'):
    if filename.endswith('.py'):
        client.load_extension(f'util.{filename[:-3]}')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

loop = asyncio.get_event_loop()
servers = client.get_cog('ServerManage')


@client.event
async def on_ready():
    change_status.start()
    print("Nibbles is awake!")

    _thread = Thread(target=launch_tasks)
    _thread.start()


def launch_tasks():
    asyncio.set_event_loop(client.loop)
    now = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("America/Chicago"))
    midnight = datetime.combine(date.today() + timedelta(days=1), datetime.min.time()) + timedelta(hours=6)
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    tdelta = midnight - now
    midnight_time = tdelta.total_seconds() % (24 * 3600)
    if midnight_time > 43200:
        time.sleep(midnight_time-43200)
    else:
        time.sleep(midnight_time)
    announcement_manager.start()


async def announce_year_progress(channels):
    tdelta = datetime.today() - datetime(datetime.today().year, 1, 1)
    percent = (float(tdelta.days) / 365)
    whole = int(percent * 15)
    partial = int(percent * 90) % 6
    empty = 15 - whole - partial
    braille = {
        0: '',
        1: '⣄',
        2: '⣆',
        3: '⣇',
        4: '⣧',
        5: '⣷',
        6: '⣿'
    }
    partial = braille[partial]
    year_progress = f'[{(whole * "⣿")}{partial}{(empty * "⣀")}]'
    for channel in channels:
        await channel.send(f'{datetime.today().year} Progress Bar: \n{year_progress} {(percent * 100):.2f}%')


@tasks.loop(hours=12)
async def announcement_manager():
    # wheel
    await client.get_cog('Gamble').announce_wheel(await servers.wheel_channels())

    now = datetime.utcnow()
    if now.hour != 18:
        # genshin_banner
        await client.get_cog('Summon').new_banner_rotation(await servers.banner_channels())
        # year_progress
        await announce_year_progress(await servers.year_progress_channels())
        # birthday
        birthdays = servers.birthday_channels()
        for birthday in birthdays:
            await client.get_cog('Summon').birthday(birthday[0], birthday[1])


@tasks.loop(minutes=random.randrange(10, 45))
async def change_status():
    await client.change_presence(activity=discord.Streaming(
        name=next(status), url='https://twitch.tv/bitnoms'))


@client.event
async def on_member_join(member):
    channel = servers.greetings_channel(member.guild.id)
    await channel.send(
        f'Haii {member.name}, '
        f'I\'m nibbles and welcome to the server! <:kayaya:778399319803035699>')
    if member.guild.id == 607298393370394625:
        await member.add_roles(discord.utils.get(member.guild.roles, name='Moons'))
        await member.edit(nick=member.name.lower())


@client.event
async def on_member_remove(member):
    channel = servers.greetings_channel(member.guild.id)
    await channel.send(f'Bai bai {member.name} <:qiqi:813767632904781915>')


@client.event
async def on_command_error(ctx, error):
    if '.transfer' in ctx.message.content:
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("nibbles can't do anything, something is missing! <:ShibaNervous:703366029425901620>")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        channel = await client.fetch_channel(819271204468031508)
        await channel.send(f'[{datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}] {error}\n')


@client.event
async def on_guild_join(guild):
    await guild.owner.send("Haiii I'm nibbles, I am happy to meet you <a:ChikaYay:846769277944332319>")
    await guild.owner.send("Set up for nibbles is ez! There are numerous things that nibbles can do, use the command "
                           ".settings in a channel you would want nibbles to be in to start!")
    await guild.owner.send("If you run into any issues, you could always ask ʙɪᴛ#5595!")
    return

utility = ['choose', 'poll', 'get_pfp', 'size', 'profile', 'set_desc', 'set_birthday']
genshin = ['banner', 'event_wish', 'reg_wish', 'genshin_inventory', 'genshin_character', 'pity', 'quick_sell']
anime = ['anime_list', 'anime_list_add', 'anime_list_remove', 'anime_inventory', 'anime_search', 'anime_character',
         'anime_character_kick', 'anime_give']
economy = ['gamble_black_jack', 'gamble_coin', 'bal', 'transfer']
leaderboard = ['leaderboard', 'rank']
todo = ['todo_list', 'todo_add', 'todo_check']
mod = ['purge', 'settings']


@client.command(name='help', hidden=True)
async def descriptions(ctx):
    desc = 'Here are the categories of nibbles\'s commands! React to the corresponding category to learn more!\n'
    desc += 'Mention nibbles for an :8ball: response!\n'
    desc += 'For more help, join [Nibble\'s training ground](https://discord.gg/hycRhPYNpP)'

    embed = discord.Embed(title="Nibbles is here to help", color=random.randint(0, 0xFFFFFF), description=desc)

    embed.add_field(name='**Anime** <a:KannaEat:844266819430776924>', value=str(anime))
    embed.add_field(name='**Genshin** <:genshin:849405822781227069>', value=str(genshin))
    embed.add_field(name='**Economy** 💰', value=str(economy))
    if ctx.guild.id == 607298393370394625:
        embed.add_field(name='**Leaderboard** 🌟', value=str(leaderboard))
    embed.add_field(name='**Utility** 🔧', value=str(utility))
    embed.add_field(name='**To-do** ✅', value=str(todo))
    if ctx.author.permissions_in(ctx.channel).manage_guild:
        embed.add_field(name='**Moderation Tools** 🔨', value=str(mod))
    help_msg = await ctx.send(content='Help menu', embed=embed)

    await help_msg.add_reaction('<a:KannaEat:844266819430776924>')
    await help_msg.add_reaction('<:genshin:849405822781227069>')
    await help_msg.add_reaction('💰')
    if ctx.guild.id == 607298393370394625:
        await help_msg.add_reaction('🌟')
    await help_msg.add_reaction('🔧')
    await help_msg.add_reaction('✅')
    if ctx.author.permissions_in(ctx.channel).manage_guild:
        await help_msg.add_reaction('🔨')


@client.command(hidden=True)
@has_permissions(manage_guild=True)
async def mod_help(ctx):
    output = ''
    for command in client.commands:
        if command.hidden:
            output += command.name + '\n'
    await ctx.send(output)


@client.event
async def on_message(message):
    if message.reference is None and client.user.mentioned_in(message):
        eight_ball = [
            'Nibbles agree.', 'Yesssu!', 'Yes yes.', 'Nibbles approve.',
            'You can bet nom noms on it.', 'Nibbles thinks that is correct.',
            'Most likely.', 'Good good.', 'Ooooo wats dat?',
            'My nom noms said yes.', 'Huh? What did you say?.',
            'I\'m sleepy... ask later.', 'Its a secret hehe.',
            'Mommy says stranger danger!.', 'Bit said he doesn\'t know.',
            'Nibbles thinks that is wrong.', 'My nom noms said no.',
            'Nibbles disagree.', 'Noooooo!', 'That is incorrect.'
        ]
        await message.channel.send(f'{random.choice(eight_ball)}')
    else:
        await client.process_commands(message)


@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.content == 'Help menu' and not user.bot:
        embed = discord.Embed.Empty
        if reaction.emoji == '🔧':
            embed = discord.Embed(title='Utility', description='All sorts of commands that might come in handy!')
            for comm_name in utility:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif str(reaction.emoji) == '<:genshin:849405822781227069>':
            desc = 'Get started by wishing on either the daily rotating banner or the permanent banner.' \
                   'Use .we to wish on the event banner and .wr for the permanent banner. ' \
                   'Use the .banner command to see today\'s banner. '
            embed = discord.Embed(title='Genshin', description='A Genshin gacha simulator!\n' + desc)
            for comm_name in genshin:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif str(reaction.emoji) == '<a:KannaEat:844266819430776924>':
            embed = discord.Embed(title='Anime', description='Collect all your favorite waifus! To get started, '
                                                             'add some of your favorite animes to your anime list to '
                                                             'make characters appear in a designated channel.')
            for comm_name in anime:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif reaction.emoji == '💰':
            embed = discord.Embed(title='Economy', description="Nom noms wealth management and GAMBLING 🎰.")
            for comm_name in economy:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif reaction.emoji == '🌟':
            embed = discord.Embed(title='Leaderboard', description="How active are you in Project Void?")
            for comm_name in leaderboard:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif reaction.emoji == '✅':
            embed = discord.Embed(title='To-do List', description='Manage your task lists with nibbles!')
            for comm_name in todo:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        elif reaction.emoji == '🔨':
            embed = discord.Embed(title='Moderation Tools', description='haha mods go <:BennetBonk:853419733776728064>')
            for comm_name in mod:
                embed.add_field(name=comm_name, value=help_embed_value(comm_name), inline=False)
        await reaction.message.edit(embed=embed)


def help_embed_value(comm_name):
    command = client.get_command(comm_name)
    value = command.description
    if len(command.aliases) != 0:
        value += f"\n{'aliases' if len(command.aliases) > 1 else 'alias'}: {command.aliases}"
    return value


@client.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == '🍪' and payload.message_id == 804860150195945493:
        guild = await client.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        await member.add_roles(discord.utils.get(guild.roles, name='Cookie Squad'))


@client.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == '🍪' and payload.message_id == 804860150195945493:
        guild = await client.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        await member.remove_roles(discord.utils.get(guild.roles, name='Cookie Squad'))

client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.90H7LW32mCJIzmtVyZTQehjhfSE')

@client.command(hidden=True)
async def send_data(ctx):
    directory = '/home/nibbles/data/'
    for file in os.listdir(directory):
        print(file)
        if file.endswith('.json') or file.endswith('.db'):
            await ctx.send(file=discord.File(os.path.join(directory, file)))
            await asyncio.sleep(5)

