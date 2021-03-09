import sqlite3

from discord.ext import commands
from discord.ext.commands import has_permissions


class Characters(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect('./data/characters.db')
        # character information library
        self.c = self.conn.cursor()
        self.level_calc(0)

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Characters online')

    def find_character(self, char_name: str, var: str = '*'):
        self.c.execute(
            f"SELECT {var} FROM characters WHERE name = '{char_name}'")
        if var != '*':
            return self.c.fetchone()[0]
        else:
            return self.c.fetchone()

    # @commands.command(hidden=True)
    # @has_permissions(manage_guild=True)
    # async def insert_character(self, *, param):
    #     # c.execute("INSERT INTO users VALUES (123456789, 0, 0)")
    #     self.c.execute(f"INSERT INTO characters VALUES ({param})")
    #     self.conn.commit()

    def find(self, var: str):
        self.c.execute(f'SELECT {var} FROM characters')
        return self.c.fetchall()

    def level_calc(self, xp: int):
        xp += 1
        self.c.execute('SELECT level, total FROM xp')
        level = 1
        for total_req in self.c.fetchall():
            if isinstance(total_req[1], int) and xp > total_req[1]:
                level = total_req[0]
        self.c.execute(f'SELECT total, next_lvl FROM xp WHERE level = {level}')
        temp = self.c.fetchone()
        xp -= 1
        if temp[0] == '':
            cur_xp = xp
        else:
            cur_xp = xp - temp[0]
        next_lvl = temp[1]
        if next_lvl == '':
            next_lvl = 'MAX'
        # current level, current level xp, next level xp
        output = (level, cur_xp, next_lvl)
        # print(output)
        return output

    def fetch_levels(self):
        self.c.execute(f'SELECT level, total FROM xp')
        return self.c.fetchall()


def setup(client):
    client.add_cog(Characters(client))
