import discord
from discord.ext import commands
import random


class Choose(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Choose online')

    # commands
    @commands.command(description='Nibbles helps you choose because you\'re too indecisive\n'
                                  '.choose go to work, play video games, something else')
    async def choose(self, ctx, *, param):
        arr = param.split(', ')
        if len(arr) == 1:
            await ctx.send('stop making nibbles do your bidding, you meanie')
            await ctx.send('<:kangy:747848239759491135>')
            return
        choice = random.choice(arr)
        await ctx.send(choice)


def setup(client):
    client.add_cog(Choose(client))
