import random

import discord
from discord.ext import commands
from tinydb import TinyDB, Query


def create_user(user_id):
    with TinyDB('./inventory.json') as db:
        db.insert({'user': user_id, 'chars': [], 'books': [0, 0, 0]})


def search(user_id):
    with TinyDB('./inventory.json') as db:
        return db.search(Query().user == user_id)


def add_char(user_id, char):
    user_dict = search(user_id)
    temp_chars = user_dict[0]['chars']

    for characters in temp_chars:
        if characters[0] == char:
            if characters[2] < 6:
                characters[2] += 1
                with TinyDB('./inventory.json') as db:
                    db.update({'chars': temp_chars}, Query().user == user_id)
                return
            else:
                return

    temp_chars.append((char, 0, 0))
    with TinyDB('./inventory.json') as db:
        db.update({'chars': temp_chars}, Query().user == user_id)


def add_book(user_id, color):
    user_dict = search(user_id)
    temp_books = user_dict[0]['books']

    if color == 'green_book':
        temp_books[0] += 1
    elif color == 'blue_book':
        temp_books[1] += 1
    else:
        temp_books[2] += 1
    with TinyDB('./inventory.json') as db:
        db.update({'books': temp_books}, Query().user == user_id)


def print_all():
    with TinyDB('./inventory.json') as db:
        print(db.all())


class InventoryDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client

    # add cog to main system
    @commands.Cog.listener()
    async def on_ready(self):
        print('Inventory Database online')

    @commands.command(description='check your inventory full of goodies!\n.inventory')
    async def inventory(self, ctx, _id=0):
        _id = ctx.author.id if _id == 0 else _id
        if len(search(_id)) == 0:
            await ctx.send("you haven't summoned yet!")
            return
        inv = search(_id)[0]
        embed = discord.Embed(title="Your inventory!", colour=discord.Colour(0x7ce010))

        embed.set_author(name=ctx.author.display_name if ctx.author.nick is None else ctx.author.nick)

        for char in inv.get('chars'):
            embed.add_field(name=char[0], value=f'Level {char[1]}\n Const. {char[2]}', inline=True)
        embed.add_field(name='Experience Books', value=':notebook: :arrow_down: ', inline=False)
        books = inv.get('books')
        embed.add_field(name='Purple Books', value=str(books[0]))
        embed.add_field(name='Blue Books', value=str(books[1]))
        embed.add_field(name='Green Books', value=str(books[2]))

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(InventoryDatabase(client))
