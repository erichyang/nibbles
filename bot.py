import asyncio

import discord
import os
import random
import pytz

from discord.ext import commands, tasks
from itertools import cycle
from threading import Thread
import time
from datetime import datetime, date, timedelta

from discord.ext.commands import has_permissions

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True,
                                              voice_states=True))
client.remove_command('help')

status = cycle(['cookie nomming', 'sleeping', 'being a ball of fluff', 'wheel running', 'tunnel digging',
                'wires nibbling', 'food stashing', 'treasure burying', 'grand adventure', 'collecting taxes'])

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

for filename in os.listdir('./util'):
    if filename.endswith('.py'):
        client.load_extension(f'util.{filename[:-3]}')

loop = asyncio.get_event_loop()
if os.path.exists('log.txt'):
    os.remove('log.txt')


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
    launch_time = tdelta.total_seconds() % (24*3600)
    time.sleep(launch_time)
    client.get_cog('Gamble').announce.start()
    client.get_cog('Summon').new_banner_rotation.start()
    client.get_cog('UserDatabase').vacuum.start()
    client.get_cog('GachaDatabase').vacuum.start()


@tasks.loop(minutes=random.randrange(10, 45))
async def change_status():
    await client.change_presence(activity=discord.Streaming(name=next(status), url='https://twitch.tv/bitnoms'))


@client.event
async def on_member_join(member):
    await member.guild.get_channel(681149093858508834).send(f'Heyaa {member.name}, '
                                                            f'I\'m nibbles! <:kayaya:778399319803035699>')
    await member.add_roles(discord.utils.get(member.guild.roles, name='Moons'))
    await member.edit(nick=member.name.lower())


@client.event
async def on_member_remove(member):
    await member.guild.get_channel(681149093858508834).send(f'Bai bai {member.name} <:qiqi:781667748031103036>')


@client.event
async def on_command_error(ctx, error):
    if '.transfer' in ctx.message.content:
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("nibbles can't do anything, something is missing! <:ShibaNervous:703366029425901620>")
    else:
        with open('log.txt', 'a') as _f:
            _f.write(f'[{datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}] {error}\n')


@client.command(name='help', hidden=True)
async def descriptions(ctx):
    embed_var = discord.Embed(title="Nibbles is here to help", color=0x8109e9)
    for item in client.commands:
        if not item.hidden:
            embed_var.add_field(name=item.name, value=item.description, inline=False)
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
    if client.user.mentioned_in(message):
        eight_ball = [' It is certain.', ' It is decidedly so.', 'Without a doubt.', 'Yes – definitely.',
                      ' You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.',
                      ' Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.',
                      'Cannot predict now.', 'Concentrate and ask again.', "Don't count on it.", ' My reply is no.',
                      'My sources say no.', 'Outlook not so good.', 'Very doubtful.']
        await message.channel.send(random.choice(eight_ball))
    else:
        await client.process_commands(message)


with open('bot_token', 'r') as f:
    client.run(f.read())
