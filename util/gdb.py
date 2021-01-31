import sqlite3
import random

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

from util.pillow import Pillow


class GachaDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('gacha.db')
        # pity, banner, rates
        self.c = self.conn.cursor()
        self.fives = ['Albedo', 'Ayaka', 'Diluc', 'Ganyu', 'Jean', 'Keqing', 'Klee', 'Mona', 'Qiqi', 'Tartaglia',
                      'Venti', 'Xiao', 'Zhongli']
        self.fours = ['Amber', 'Barbara', 'Bennett', 'Chongyun', 'Diona', 'Fischl', 'Kaeya', 'Lisa', 'Ningguang',
                      'Noelle', 'Razor', 'Sucrose', 'Xiangling', 'Xingqiu', 'Xinyan']
        with open('banner_info', 'r') as f:
            self.cur5 = f.readline()[:-1]
            self.cur4 = []
            for _ in range(3):
                self.cur4.append(f.readline()[:-1])
        pillow = Pillow(client)
        pillow.generate_banner(self.cur5, self.cur4)

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Gacha Database online')

    def new_banner(self):
        five_star = random.choice(self.fives)
        self.cur5 = five_star
        random.shuffle(self.fours)
        four_star = self.fours[0:3]
        output = five_star + '\n'
        with open('banner_info', 'w') as f:
            for char in four_star:
                output += f"{char}\n"
            f.write(output)
        self.cur4 = four_star
        return five_star, four_star

    def find_user(self, db: str, user: str, var: str = '*'):
        self.c.execute(f"SELECT {var} FROM {db} WHERE user_id = {user}")
        if var != '*':
            return self.c.fetchone()[0]
        else:
            return self.c.fetchone()

    async def set(self, db: str, var: str, amount: str, user: str):
        self.c.execute(f"UPDATE {db} SET {var} = {amount} WHERE user_id = {user}")
        self.conn.commit()

    @tasks.loop(hours=12)
    async def vacuum(self):
        self.c.execute("VACUUM")
        self.conn.commit()

    @commands.command()
    @has_permissions(manage_guild=True)
    async def close_gdb(self, ctx):
        self.conn.close()
        await ctx.send('gacha db connection closed')


def setup(client):
    client.add_cog(GachaDatabase(client))
