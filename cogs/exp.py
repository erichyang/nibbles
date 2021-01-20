import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import random
from datetime import datetime
import sqlite3


class Exp(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('user.db')
        self.c = self.conn.cursor()
        self.vc = {}
#        self.c.execute("UPDATE users SET bal = 99999")
#        self.conn.commit()

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Exp online')

    @commands.Cog.listener()
    async def on_message(self, message):
        now = datetime.now()
        _id = message.author.id
        self.c.execute("SELECT * FROM users WHERE user_id = " + str(_id))
        record = self.c.fetchone()
        if record is None:
            if not message.author.bot:
                self.c.execute("INSERT INTO users VALUES (" + str(_id) +
                               ", 0, 320, '" + now.strftime('%H:%M:%S') + "')")
        else:
            last = datetime.strptime(record[3], '%H:%M:%S')
            tdelta = now - last
            if message.content[:1] == '.' or tdelta.seconds < random.randrange(45, 60):
                return
            val = random.randrange(6, 8)
            self.c.execute("SELECT bal FROM users WHERE user_id = " + str(_id))
            temp_bal = self.c.fetchone()[0]

            self.c.execute("UPDATE users SET pts = pts+" + str(val) + " WHERE user_id = " + str(_id))
            self.c.execute("UPDATE users SET bal = bal+" + str(val) + " WHERE user_id = " + str(_id))
            self.c.execute("UPDATE users SET time = '" + now.strftime('%H:%M:%S') + "' WHERE user_id = " + str(_id))

        self.conn.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, prev, cur):
        if member.bot:
            return
        if prev.channel is None:
            self.vc[member.id] = datetime.now()
        elif cur.channel is None:
            tdelta = datetime.now() - self.vc.pop(member.id)
            val = int(tdelta.seconds / 30)
            self.c.execute("UPDATE users SET pts = pts+" + str(val) + " WHERE user_id = " + str(member.id))
            self.c.execute("UPDATE users SET bal = bal+" + str(val) + " WHERE user_id = " + str(member.id))

        self.conn.commit()

    # commands
    @commands.command()
    async def bal(self, ctx, param):
        self.c.execute("SELECT * FROM users")
        self.c.execute("SELECT * FROM users WHERE user_id = " + param[3:-1])
        temp = self.c.fetchone()
        if temp is not None:
            await ctx.send(str(self.client.get_user(temp[0]).display_name) + "'s current balance is: " + str(temp[2]) +
                           ' nom noms :cookie:')

    @bal.error
    async def bal_error(self, ctx, error):
        self.c.execute("SELECT * FROM users")
        self.c.execute("SELECT * FROM users WHERE user_id = " + str(ctx.author.id))
        temp = self.c.fetchone()
        if temp is not None:
            await ctx.send('Your current balance is: ' + str(temp[2]) + ' nom noms :cookie:')

    @commands.command()
    async def leaderboard(self, ctx):
        self.c.execute("SELECT * FROM users ORDER BY pts DESC LIMIT 10")
        embed_var = discord.Embed(title="People who are the most active! ", color=0x8109e9)
        lb = self.c.fetchall()
        rank = ''
        name = ''
        points = ''
        for i in range(0, len(lb)):
            rank += str(i + 1) + '\n'
            name += self.client.get_user(lb[i][0]).display_name + '\n'
            points += str(lb[i][1]) + ' pts\n'
        embed_var.add_field(name='Rank', value=rank, inline=True)
        embed_var.add_field(name='Name', value=name, inline=True)
        embed_var.add_field(name='Points', value=points, inline=True)
        await ctx.channel.send(embed=embed_var)

    @commands.command()
    @has_permissions(manage_guild=True)
    async def close_table(self, ctx):
        self.conn.close()


def setup(client):
    client.add_cog(Exp(client))
