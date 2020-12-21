import discord
import random
from discord.ext import commands

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True))


@client.event
async def on_ready():
    print("Nibbles is awake!")




client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.lFN86LS_ZVA1aeQ_4gtL4irUp0U')
