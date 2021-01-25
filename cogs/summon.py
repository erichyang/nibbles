from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

from cogs import db


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db = self.client.get_cog('DataBase')

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Summon online')

    @tasks.loop(hours=24)
    async def banner(self):
        channel = await self.client.fetch_channel(681149093858508834)
        embed = discord.Embed()
        await channel.send(content='There is a new banner available!', embed=embed)

    def init_banner_rotation(self):
        self.banner.start()

    @commands.command()
    @has_permissions(manage_guild=True)
    async def stop_banner(self, ctx):
        await ctx.send('The banner rotation stopped')
        self.announce.stop()

    # commands
    @commands.command()
    async def intertwined_wish(self, ctx, amount):
        user = await self.db.find_user(db='users', user=str(ctx.author.id), var='bal')
        if user[0] <= amount * 160:
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return

    @commands.command()
    async def acquaint_wish(self, ctx, amount):
        user = await self.db.find_user(db='users', user=str(ctx.author.id), var='bal')
        if user[0] <= amount * 160:
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return


def setup(client):
    client.add_cog(Summon(client))
