import discord
from discord.ext import commands


class Purge(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Purge online')

    # commands
    @commands.command()
    async def purge(self, ctx, amount):
        if ctx.message.author.permissions_in(ctx.message.channel).manage_messages:
            await ctx.channel.purge(limit=int(amount) + 1)


def setup(client):
    client.add_cog(Purge(client))
