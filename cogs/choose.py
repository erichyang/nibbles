import discord
from discord.ext import commands
import random


class Choose(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.name = "choose"
        self.desc = 'nibbles helps you choose because you\'re too indecisive'
        self.example = '.choose go to work, play video games, something else'

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Choose online')

    # commands
    @commands.command()
    async def choose(self, ctx, *, param):
        choice = random.choice(param.split(', '))
        await ctx.send(choice)


def setup(client):
    client.add_cog(Choose(client))
