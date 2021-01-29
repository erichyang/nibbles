from discord.ext import commands


class Size(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Size online')

    # commands
    @commands.command()
    async def size(self, ctx):
        await ctx.send(f'The server currently has: {ctx.guild.member_count} members')


def setup(client):
    client.add_cog(Size(client))
