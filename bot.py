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
    now = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("America/Chicago"))
    midnight = datetime.combine(date.today() + timedelta(days=1),
                                datetime.min.time()) + timedelta(hours=6)
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    tdelta = midnight - now
    launch_time = tdelta.total_seconds() % (24 * 3600)
    time.sleep(launch_time)
    client.get_cog('Gamble').announce.start()
    client.get_cog('Summon').new_banner_rotation.start()
    client.get_cog('UserDatabase').vacuum.start()
    client.get_cog('GachaDatabase').vacuum.start()


@tasks.loop(minutes=random.randrange(10, 45))
async def change_status():
    await client.change_presence(activity=discord.Streaming(
        name=next(status), url='https://discord.gg/wWyDZgREFf'))


@client.event
async def on_member_join(member):
    prim = servers.find_primary_channel(member.guild.id)
    if prim is None:
        return
    await member.guild.get_channel(prim).send(
        f'Heyaa {member.name}, '
        f'I\'m nibbles! <:kayaya:778399319803035699>')
    await member.add_roles(discord.utils.get(member.guild.roles, name='Moons'))
    await member.edit(nick=member.name.lower())


@client.event
async def on_member_remove(member):
    prim = servers.find_primary_channel(member.guild.id)
    if prim is None:
        return
    await member.guild.get_channel(prim).send(
        f'Bai bai {member.name} <:qiqi:813767632904781915>')


@client.event
async def on_command_error(ctx, error):
    if '.transfer' in ctx.message.content:
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "nibbles can't do anything, something is missing! <:ShibaNervous:703366029425901620>"
        )
    else:
        if not isinstance(error, commands.CommandNotFound):
            print(f'[{datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}] {error}\n')


@client.command(name='help', hidden=True)
async def descriptions(ctx):
    embed_var = discord.Embed(title="Nibbles is here to help",
                              color=random.randint(0, 0xFFFFFF))
    for item in client.commands:
        if not item.hidden:
            embed_var.add_field(name=item.name,
                                value=item.description,
                                inline=False)
    await ctx.send(embed=embed_var)


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
            'You can count on it.', 'Nibbles thinks that is correct.',
            'Most likely.', 'Good good.', 'Ooooo wats dat?',
            'My nom noms said yes.', 'Huh? What did you say?.',
            'I\'m sleepy... ask later.', 'Its a secret hehe.',
            'Mommy says stranger danger!.', 'Daddy said he doesn\'t know.',
            'Nibbles thinks that is wrong.', 'My nom noms said no.',
            'Nibbles disagree.', 'Noooooo!', 'That is incorrect.'
        ]
        await message.channel.send(random.choice(eight_ball))
    else:
        await client.process_commands(message)


@client.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == '🍪' and payload.message_id == 804860150195945493:
        guild = await client.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        await member.add_roles(
            discord.utils.get(guild.roles, name='Cookie Squad'))


@client.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == '🍪' and payload.message_id == 804860150195945493:
        guild = await client.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        await member.remove_roles(
            discord.utils.get(guild.roles, name='Cookie Squad'))


client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.90H7LW32mCJIzmtVyZTQehjhfSE')
