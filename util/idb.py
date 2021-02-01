import random

import discord
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

    @commands.command(description='check your inventory full of goodies!\n.inventory')
    async def inventory(self, ctx, _id=0):
        _id = ctx.author.id if _id == 0 else _id
        inv = self.search(_id)[0]
        embed = discord.Embed(title="Your inventory!", colour=discord.Colour(0x7ce010))

        embed.set_author(name=ctx.author.display_name if ctx.author.nick is None else ctx.author.nick)

        for char in inv.get('chars'):
            embed.add_field(name=char[0], value=f'Level {char[1]}\n Const. {char[2]}', inline=True)
        embed.add_field(name='Experience Books', value=':blue_book::closed_book::green_book:', inline=False)
        books = inv.get('books')
        embed.add_field(name='Purple Books', value=str(books[0]))
        embed.add_field(name='Blue Books', value=str(books[1]))
        embed.add_field(name='Green Books', value=str(books[2]))

        await ctx.send(embed=embed)

    def create_user(self, user_id):
        self.db.insert({'user': user_id, 'chars': [], 'books': [0, 0, 0]})

    def search(self, user_id):
        return self.db.search(Query().user == user_id)

    def add_char(self, user_id, char):
        user_dict = self.search(user_id)
        temp_chars = user_dict[0]['chars']

        for characters in temp_chars:
            if characters[0] == char:
                if characters[2] < 6:
                    characters[2] += 1
                    self.db.update({'chars': temp_chars}, Query().user == user_id)
                    return
                else:
                    return

        temp_chars.append((char, 0, 0))
        self.db.update({'chars': temp_chars}, Query().user == user_id)

    def add_book(self, user_id, color):
        user_dict = self.search(user_id)
        temp_books = user_dict[0]['books']

        if color == 'green_book':
            temp_books[0] += 1
        elif color == 'blue_book':
            temp_books[1] += 1
        else:
            temp_books[2] += 1

        self.db.update({'books': temp_books}, Query().user == user_id)

    def print_all(self):
        print(self.db.all())

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def close_idb(self, ctx):
        self.db.close()
        await ctx.send('inventory db connection closed')


def setup(client):
    client.add_cog(InventoryDatabase(client))
