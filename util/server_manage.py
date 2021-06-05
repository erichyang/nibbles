import sqlite3

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions


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

    def set_anime_channel(self, guild_id, opt):
        self.c.execute(f'UPDATE servers SET anime = {opt} WHERE guild = {guild_id}')
        self.conn.commit()

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
            self.c.execute(f"INSERT INTO servers VALUES ({ctx.guild.id}, {channel_id}, 0)")
        else:
            self.c.execute(f"UPDATE servers SET primary_channel = {channel_id} WHERE guild = {ctx.guild.id}")
        self.conn.commit()
        await ctx.send('The primary channel is set!')

    def parse(self, item):
        if item == -1:
            return "Disabled"
        else:
            return self.client.get_channel(item).mention

    def settings_embed(self, guild_id):
        content = 'React the corresponding number for each setting to set to current channel.\n\n'
        content += 'If the current set channel is not this channel, a reaction will set it to the current channel.\n'
        content += 'If the current set channel is this channel, a reaction will remove the assigned channel.\n\n'
        embed = discord.Embed(title='Server Settings', description=content)
        self.c.execute("SELECT * FROM servers WHERE guild = ?", (guild_id,))
        channels = self.c.fetchone()
        embed.add_field(name='1️⃣ bi-daily new wheel available', value=self.parse(channels[1]))
        embed.add_field(name='2️⃣ daily year progress bar', value=self.parse(channels[2]))
        embed.add_field(name='3️⃣ daily genshin banner', value=self.parse(channels[3]))
        embed.add_field(name='4️⃣ server member birthday', value=self.parse(channels[4]))
        embed.add_field(name='5️⃣ anime character random appearance', value=self.parse(channels[5]))
        embed.add_field(name='6️⃣ welcome and leave messages', value=self.parse(channels[6]))
        return embed

    @commands.command(hidden=True, description='configure the Nibbles settings for this server\n.settings')
    @has_permissions(manage_guild=True)
    async def settings(self, ctx):
        self.c.execute("SELECT count(*) FROM servers WHERE guild = ?", (ctx.guild.id,))
        exists = self.c.fetchone()[0]
        if exists == 0:
            self.c.execute(f"INSERT INTO servers VALUES (?, -1, -1, -1, -1, -1, -1)", (ctx.guild.id,))
            self.conn.commit()

        msg = await ctx.send('Settings for this server!', embed=self.settings_embed(ctx.guild.id))
        nums = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
        for emote in nums:
            await msg.add_reaction(emote)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.content == 'Settings for this server' and reaction.message.author.bot \
                and user.permissions_in(reaction.message.channel).manage_guild:
            columns = ['wheel', 'year_progress', 'genshin_banner', 'birthday', 'anime', 'greetings']
            for i, emote in enumerate(['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']):
                if reaction.emoji == emote:
                    guild_id = user.guild.id
                    channel_id = reaction.message.channel.id
                    self.c.execute(f"SELECT {columns[i]} FROM servers WHERE guild = {guild_id}")
                    if self.c.fetchone()[0] != channel_id:
                        self.c.execute(f"UPDATE servers SET {columns[i]} = {channel_id} WHERE guild = {guild_id}")
                        await reaction.message.channel.send(f'Set {columns[i]} to the current channel!')
                    else:
                        self.c.execute(f"UPDATE servers SET {columns[i]} = -1 WHERE guild = {guild_id}")
                        await reaction.message.channel.send(f'Disabled {columns[i]}!')
                    self.conn.commit()
                    await reaction.message.edit(content='Settings for this server', embed=self.settings_embed(guild_id))
                    return

    @settings.error
    async def permission_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("you don't have permissions to do that! <:pout:734597385258270791>")
            await ctx.send(insufficient_permission(error))
        else:
            print(error)


def setup(client):
    client.add_cog(ServerManage(client))
