import discord
from discord.ext import commands

class GetPfp(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('GetPfp online')

    # commands
    @commands.command(aliases=['getpfp'])
    async def get_pfp(self, ctx):
        if len(ctx.message.mentions) > 0:
            user_id = ctx.message.mentions[0].id
        else:
            user_id = ctx.author.id
        user = self.client.get_user(user_id)
        pfp = user.avatar_url
        user_name = user.display_name

        embed = discord.Embed(color=0x8109e9)
        embed.set_author(name=user_name + '\'s Pfp:')
        embed.set_image(url=pfp)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(GetPfp(client))