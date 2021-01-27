from datetime import datetime

import discord
from discord.ext import commands, tasks

from cogs import udb, gdb


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.udb = udb.UserDatabase(client)
        self.gdb = gdb.GachaDatabase(client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Summon online')

    # repeat every 24 hours
    @tasks.loop(hours=24)
    async def banner(self):
        channel = await self.client.fetch_channel(681149093858508834)
        five, four = self.client.get_cog('GachaDatabase').new_banner()
        desc = '5:star: ' + five + f'\n4:star: {four[0]}, {four[1]}, {four[2]}'

        embed = discord.Embed(colour=discord.Colour(0xff7cff),
                              description=desc,
                              timestamp=datetime.now())

        embed.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png")

        await channel.send(content='There is a new banner available!', embed=embed)

    # commands
    @commands.command()
    async def intertwined_wish(self, ctx, amount):
        user = await self.udb.find_user(db='users', user=str(ctx.author.id), var='bal')
        if user[0] <= amount * 160:
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return

    @commands.command()
    async def acquaint_wish(self, ctx, amount):
        user = await self.udb.find_user(db='users', user=str(ctx.author.id), var='bal')
        if user[0] <= amount * 160:
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return


def setup(client):
    client.add_cog(Summon(client))
