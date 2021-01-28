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

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True,
                                              voice_states=True))
client.remove_command('help')

status = cycle(['cookie nomming', 'sleeping', 'being a ball of fluff', 'wheel running', 'tunnel digging',
                'wires nibbling', 'food stashing', 'treasure burying', 'grand adventure', 'collecting taxes'])

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

loop = asyncio.get_event_loop()


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
    if isinstance(error, commands.MissingRequiredArgument) and ctx.message.content not in ['.help', '.bal']:
        await ctx.send("nibbles can't do anything, something is missing! <:ShibaNervous:703366029425901620>")
    else:
        print(datetime.now())
        print(error)


@client.command(aliases=['help'])
async def descriptions(ctx, command):
    embed_var = discord.Embed(title="Nibbles is here to help", color=0x8109e9)
    desc = {
        'choose': ['Nibbles helps you choose because you\'re too indecisive',
                   '.choose go to work, play video games, something else'],
        'coin_flip': ['flips a coin!', '.coin_flip'],
        'get_pfp': ['gets profile picture of yours or others', '.get_pfp; .get_pfp @<user>'],
        'poll': ['Nibbles helps you discover that other people are indecisive too', '.poll Do you like nibbles?'],
        'profile': ['check your profile that has your exp and nom noms', '.profile; .profile @nibbles'],
        'set_desc': ['set your beautiful message to be seen on your profile :D', '.set_desc Hi I am nibbles!'],
        'bal': ['count the nom noms in your stash, ooo so many <:wow:788914745008586763>', '.bal'],
        'leaderboard': ['check the top ten people with the highest points!', '.leaderboard; .lb; .xp_lb; .pts_lb'],
        'bal_lb': ['flex on your friends or something you gambling addicts', '.bal_lb'],
        'gamble_coin': ['flip a coin with the face you predict and how much you want to bet for it',
                        '.gamble_coin heads 160; .bet_coin tails 320'],
        'gamble_wheel': ['spin a wheel of fortune for free every 12 hours! You can win prizes from :cookie:100-10000',
                         '.gamble_wheel; .wheel; .spin'],
        'gamble_black_jack': ['bet against any player that accepts the challenge by playing black_jack',
                              '.gamble_black_jack 160; .blackjack 320 @nibbles'],
        'transfer': ['give your money to someone else, but why would you do that if you could give them all to nibbles',
                     '.transfer @kit 160']
    }

    if command is None:
        for key in desc:
            embed_var.add_field(name=key, value=desc[key][0], inline=False)
        embed_var.set_footer(text="ask for more help and aliases on any command by using .help <command>")
        await ctx.channel.send(embed=embed_var)
    else:
        if desc.get(command, 'no such command') == 'no such command':
            await ctx.send("this command doesn't exist!")
        else:
            embed_var.add_field(name='Command name', value=command, inline=False)
            embed_var.add_field(name='Command description', value=desc[command][1], inline=False)
            embed_var.add_field(name='Command usage', value=desc[command][1], inline=False)
            await ctx.channel.send(embed=embed_var)


@descriptions.error
async def help_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await descriptions(ctx, None)


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        await message.channel.send("nom")
    else:
        await client.process_commands(message)


with open('bot_token', 'r') as f:
    client.run(f.read())
