import random

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions


class InventoryDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Inventory Database online')


    @commands.command()
    @has_permissions(manage_guild=True)
    async def close_idb(self, ctx):
        self.conn.close()
        await ctx.send('gacha db connection closed')


def setup(client):
    client.add_cog(InventoryDatabase(client))
