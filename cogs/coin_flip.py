import discord
from discord.ext import commands
import random


class CoinFlip(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.name = "coin_flip"
        self.desc = 'Flips a coin!'
        self.example = '.coin_flip'

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Coin flip online')

    # commands
    @commands.command()
    async def coin_flip(self, ctx):
        await ctx.send(random.choice(['heads!', 'tails!']))


def setup(client):
    client.add_cog(CoinFlip(client))
