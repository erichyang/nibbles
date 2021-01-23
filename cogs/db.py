import sqlite3
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from datetime import datetime


class DataBase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('user.db')
        self.c = self.conn.cursor()

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('DataBase online')

    # database utility functions
    async def lb(self, category: str):
        self.c.execute("SELECT * FROM users ORDER BY " + category + " DESC LIMIT 10")
        title = 'most active!' if category == 'pts' else 'richest!'
        unit = category if category == 'pts' else ':cookie:'
        embed_var = discord.Embed(title="People who are the " + title, color=0x8109e9)
        lb = self.c.fetchall()
        rank = ''
        name = ''
        val = ''
        for i in range(0, len(lb)):
            rank += str(i + 1) + '\n'
            name += self.client.get_user(lb[i][0]).display_name + '\n'
            val += str(lb[i][1]) + unit + '\n'
        embed_var.add_field(name='Rank', value=rank, inline=True)
        embed_var.add_field(name='Name', value=name, inline=True)
        embed_var.add_field(name='Points' if category == 'pts' else 'Balance', value=val, inline=True)
        return embed_var

    async def set_time(self, db: str, user: str):
        self.c.execute("UPDATE ? SET time = '?' WHERE user_id = ?", (db, datetime.now().strftime('%H:%M:%S'), user))
        self.conn.commit()

    async def find_user(self, db: str, user: str, var: str = '*'):
        self.c.execute("SELECT ? FROM ? WHERE user_id = ?", (var, db, user))
        return self.c.fetchone()

    async def insert(self, db: str, init_val: str):
        self.c.execute("INSERT INTO ? VALUES ?", (db, init_val))
        self.conn.commit()

    async def update(self, db: str, var: str, amount: str, user: str):
        # amount here must have + or -
        self.c.execute("UPDATE ? SET ? = ?? WHERE user_id = ?", (db, var, var, amount, user))
        self.conn.commit()

    async def set(self, db: str, var: str, amount: str, user: str):
        self.c.execute("UPDATE ? SET ? = ? WHERE user_id = ?", (db, var, amount, user))
        self.conn.commit()

    async def vacuum(self):
        self.c.execute("VACUUM")
        self.conn.commit()

    @commands.command()
    @has_permissions(manage_guild=True)
    async def close_table(self, ctx):
        self.conn.close()
        await ctx.send('db connection safely closed')


def setup(client):
    client.add_cog(DataBase(client))
