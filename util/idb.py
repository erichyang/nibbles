import random

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
from tinydb import TinyDB, Query


class InventoryDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db = TinyDB('./inventory.json')

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Inventory Database online')

    def create_user(self, user_id):
        self.db.insert({'user': user_id, 'chars': [], 'books': [0, 0, 0]})

    def search(self, user_id):
        return self.db.search(Query().user == user_id)

    def add_char(self, user_id, char):
        user_dict = self.search(user_id)
        temp_chars = user_dict['chars']
        temp_chars.append(char)
        self.db.update({'chars': temp_chars}, Query().user == user_id)

    def add_book(self, user_id, color):
        user_dict = self.search(user_id)
        temp_books = user_dict['books']
        temp_books[color] += 1
        self.db.update({'books': temp_books}, Query().user == user_id)

    def print_all(self):
        print(self.db.all())

    @commands.command()
    @has_permissions(manage_guild=True)
    async def close_idb(self, ctx):
        self.db.close()
        await ctx.send('inventory db connection closed')


def setup(client):
    client.add_cog(InventoryDatabase(client))
