import sqlite3

from discord.ext import commands, tasks
from datetime import datetime


class UserDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('./data/user.db')
        # xp and economy
        # inventory
        self.c = self.conn.cursor()

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('User DataBase online')

    @commands.command()
    async def rank(self, ctx):
        if ctx.guild.id != 607298393370394625:
            await ctx.send('sowwy but leaderboard is only available in Project Void')
            return
        if len(ctx.message.mentions) == 0:
            user_id = ctx.author.id
        else:
            user_id = ctx.message.mentions[0].id
        self.c.execute("SELECT user_id, pts FROM users ORDER BY pts DESC")
        lb = self.c.fetchall()
        rank = -1
        pts = 0
        for i, entry in enumerate(lb):
            if entry[0] == user_id:
                rank = i+1
                pts = entry[1]
                break
        await ctx.send(f'Rank: {rank} <:KannaWow:843900425555410996>\nPoints: {pts} ⭐')

    async def set_time(self, db: str, user: str):
        self.c.execute(f"UPDATE {db} SET time = '{datetime.now().strftime('%H:%M:%S')}' WHERE user_id = {user}")
        self.conn.commit()

    def find_user(self, db: str, user: str, var: str = '*'):
        self.c.execute(f"SELECT {var} FROM {db} WHERE user_id = {user}")
        return self.c.fetchone()

    async def insert(self, db: str, init_val: str):
        # c.execute("INSERT INTO users VALUES (123456789, 0, 0)")
        self.c.execute(f"INSERT INTO {db} VALUES {init_val}")
        self.conn.commit()

    async def update(self, db: str, var: str, amount: str, user: str):
        # amount here must have + or -
        self.c.execute(f"UPDATE {db} SET {var} = {var}{amount} WHERE user_id = {user}")
        self.conn.commit()

    async def set(self, db: str, var: str, amount: str, user):
        if user is None:
            self.c.execute(f"UPDATE {db} SET {var} = {amount}")
        else:
            self.c.execute(f"UPDATE {db} SET {var} = {amount} WHERE user_id = {user}")
        self.conn.commit()
        # self.c.execute('SELECT * FROM users')
        # print(self.c.fetchall())

    def find(self, db: str, var: str):
        self.c.execute(f'SELECT {var} FROM {db}')
        return self.c.fetchone()

    def top_six(self, category):
        self.c.execute("SELECT user_id FROM users ORDER BY " + category + " DESC LIMIT 6")
        return self.c.fetchall()

    def lb(self, guild):
        self.c.execute("SELECT user_id, pts FROM users ORDER BY pts DESC")
        unit = 'pts'
        lb = self.c.fetchall()
        rank = ''
        name = ''
        val = ''
        count = 0
        for i, entry in enumerate(lb):
            member = guild.get_member(lb[i][0])
            if member is None:
                continue
            rank += str(i + 1) + '\n\n'
            # name += str(entry[0]) + '\n\n'
            name += member.display_name if member.nick is None else member.nick
            name += '\n\n'
            val += str(entry[1]) + ' ' + unit + '\n\n'
            count += 1
            if count == 10:
                break
        return rank, name, val



def setup(client):
    client.add_cog(UserDatabase(client))
