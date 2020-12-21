import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


class Purge(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Purge online')

    # commands
    @commands.command()
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount):
        await ctx.channel.purge(limit=int(amount) + 1)

    @purge.error
    async def purge_error(self, ctx, error):
        await ctx.send("hey you, kit told me you can't do that <:pout:734597385258270791>")
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'you need the **{}** permission(s) to do this'.format(fmt)
        await ctx.send(_message)


def setup(client):
    client.add_cog(Purge(client))
