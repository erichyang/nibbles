import sqlite3
import random
from discord.ext import commands


class GachaDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('gacha.db')
        # pity, banner, rates
        self.c = self.conn.cursor()
        self.fives = ['Klee', 'Ganyu', 'Qiqi']
        self.fours = ['Bennet', 'Razor', 'Chongyun', 'Ningguang']

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Gacha Database online')

    def new_banner(self):
        five_star = random.choice(self.fives)
        random.shuffle(self.fours)
        four_star = self.fours[0:3]
        output = five_star
        with open('banner_info', 'w') as f:
            for char in four_star:
                output += f"\n{char}"
            f.write(output)
        return five_star, four_star

def setup(client):
    client.add_cog(GachaDatabase(client))
