import discord
from discord.ext import commands


class Poll(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Poll online')

    # commands
    @commands.command()
    async def poll(self, ctx, *, question):
        message = await ctx.send(f'**{ctx.author.name}** asks {question}')
        await message.add_reaction('\N{THUMBS UP SIGN}')
        await message.add_reaction('\N{THUMBS DOWN SIGN}')

def setup(client):
    client.add_cog(Poll(client))
