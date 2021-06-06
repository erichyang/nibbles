from discord.ext import commands


class Size(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Size online')

    # commands
    @commands.command(description='Find out how many members is in this server!\n.size')
    async def size(self, ctx):
        num = ctx.guild.member_count
        for member in ctx.guild.members:
            if member.bot:
                num-=1
        await ctx.send(f'The server currently has: {num} human members')


def setup(client):
    client.add_cog(Size(client))
