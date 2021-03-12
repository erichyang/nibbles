import sqlite3

from discord.ext import commands
from discord.ext.commands import has_permissions


def insufficient_permission(error):
    missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
    if len(missing) > 2:
        fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
    else:
        fmt = ' and '.join(missing)
    return 'you need the **{}** permission(s) to do this'.format(fmt)


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
        self.c.execute(f'SELECT * FROM servers')
        arr = self.c.fetchall()
        return [temp for temp in arr if self._determine(temp[0])]

    def _determine(self, guild_id):
        for guild in self.client.guilds:
            if guild_id == guild.id:
                return True
        return False

    def find_primary_channel(self, guild_id):
        self.c.execute(f"SELECT primary_channel FROM servers WHERE guild = {guild_id}")
        temp = self.c.fetchone()
        if temp is None:
            return None
        else:
            return temp[0]

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel_id):
        if self.find_primary_channel(ctx.guild.id) is None:
            self.c.execute(f"INSERT INTO servers VALUES ({ctx.guild.id}, {channel_id}, FALSE)")
        else:
            self.c.execute(f"UPDATE servers SET primary_channel = {channel_id} WHERE guild = {ctx.guild.id}")
        self.conn.commit()
        await ctx.send('The primary channel is set!')

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def opt_in_banner(self, ctx):
        if self.find_primary_channel(ctx.guild.id) is None:
            return
        else:
            self.c.execute(f"UPDATE servers SET banner = TRUE WHERE guild = {ctx.guild.id}")
        self.conn.commit()
        await ctx.send('Opted in to gacha banner announcement!')

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def opt_out_banner(self, ctx):
        if self.find_primary_channel(ctx.guild.id) is None:
            return
        else:
            self.c.execute(f"UPDATE servers SET banner = FALSE WHERE guild = {ctx.guild.id}")
        self.conn.commit()
        await ctx.send('Opted out of gacha banner announcement!')

    @opt_in_banner.error
    @opt_out_banner.error
    @set_channel.error
    async def permission_error(self, ctx, error):
        await ctx.send("you don't have permissions to do that! <:pout:734597385258270791>")
        await ctx.send(insufficient_permission(error))


def setup(client):
    client.add_cog(ServerManage(client))
