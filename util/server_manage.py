import sqlite3

from discord.ext import commands
from discord.ext.commands import has_permissions


class ServerManage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('./data/servers.db')
        # multi-server support
        self.c = self.conn.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        print('Server Manage online')

    def all_primary_channel(self):
        self.c.execute(f'SELECT primary_channel FROM servers')
        return self.c.fetchall()

    def find_primary_channel(self, guild_id):
        self.c.execute(f"SELECT primary_channel FROM servers WHERE guild = {guild_id}")
        temp = self.c.fetchone()
        if len(temp) == 0:
            return None
        else:
            return temp[0]

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel_id):
        if self.find_primary_channel(ctx.guild.id) is None:
            self.c.execute(f"INSERT INTO servers VALUES ({ctx.guild.id}, {channel_id})")
        else:
            self.c.execute(f"UPDATE servers SET primary_channel = {channel_id} WHERE guild = {ctx.guild.id}")
        self.conn.commit()


def setup(client):
    client.add_cog(ServerManage(client))
