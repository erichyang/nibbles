import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from util import server_manage


class Purge(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Purge online')

    # commands
    @commands.command(hidden=True)
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount):
        await ctx.channel.purge(limit=int(amount) + 1)

    # error
    @purge.error
    async def purge_error(self, ctx, error):
        await ctx.send("hey you, kit told me you can't do that <:pout:734597385258270791>")
        await ctx.send(server_manage.insufficient_permission(error))


def setup(client):
    client.add_cog(Purge(client))
