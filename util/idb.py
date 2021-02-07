import random

import discord
from discord.ext import commands
from tinydb import TinyDB, Query

from util.characters import Characters


def create_user(user_id):
    with TinyDB('./inventory.json') as db:
        db.insert({'user': user_id, 'chars': [], 'books': [0, 0, 0]})


def search(user_id):
    with TinyDB('./inventory.json') as db:
        return db.search(Query().user == user_id)


def transfer_card(user_id, character):
    with TinyDB('./inventory.json') as db:
        user = db.search(Query().user == user_id)[0]
        characters = user.get('trading_cards')
        if character in characters:
            characters.remove(character)
            db.update({'trading_card': characters}, Query().user == user)
            return 'done'
        else:
            return 'fail'


def add_card(user_id, char):
    user_dict = search(user_id)[0]
    if 'trading_cards' in user_dict:
        cards = user_dict.get('trading_cards')
        cards.append(char)
    else:
        cards = [char]
    with TinyDB('./inventory.json') as db:
        db.update({'trading_cards': cards}, Query().user == user_id)


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
                add_card(user_id, char)
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
        self.char_lib = Characters(client)

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
        color = discord.Colour(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title="Your characters!", color=color)

        embed.set_author(name=ctx.author.display_name if ctx.author.nick is None else ctx.author.nick)
        for char in inv.get('chars'):
            rarity = self.char_lib.find_character(char[0], 'rarity')
            embed.add_field(name=char[0], value=f'Rarity {rarity}:star:\nLevel {char[1]}\n Const. {char[2]}',
                            inline=True)
        await ctx.send(embed=embed)

        embed = discord.Embed(title="And other stuff!", colour=color)
        # print(inv)
        books = inv.get('books')
        embed.add_field(name='Purple Books', value=str(books[0]))
        embed.add_field(name='Blue Books', value=str(books[1]))
        embed.add_field(name='Green Books', value=str(books[2]))
        trading = inv.get('trading_cards')
        if trading is not None:
            cards = trading[0]
            for item in trading[1:]:
                cards += ', ' + item
            embed.add_field(name='Transferable cards', value=cards)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(InventoryDatabase(client))
