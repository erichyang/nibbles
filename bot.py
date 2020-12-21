import discord
import os
import random
from discord.ext import commands, tasks
from itertools import cycle

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True))
status = cycle(['cookie nomming', 'sleeping', 'tail chasing', 'grooming'])

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.event
async def on_ready():
    change_status.start()
    print("Nibbles is awake!")


@tasks.loop(minutes=random.randrange(10, 45))
async def change_status():
    await client.change_presence(activity=discord.Streaming(name=next(status), url='https://twitch.tv/bitnoms'))


@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')


@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')


@client.event
async def on_member_join(member: discord.Member):
    print("someone joined")


@client.event
async def on_member_remove(member: discord.Member):
    print("someone left")


client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.lFN86LS_ZVA1aeQ_4gtL4irUp0U')
