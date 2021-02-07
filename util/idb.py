import random

import discord
from discord.ext import commands
from tinydb import TinyDB, Query

from util.characters import Characters


def create_user(user_id):
    with TinyDB('./data/inventory.json') as db:
        db.insert({'user': user_id, 'chars': [], 'books': [0, 0, 0]})


def search(user_id):
    with TinyDB('./data/inventory.json') as db:
        return db.search(Query().user == user_id)


def transfer_card(user_id, character):
    with TinyDB('./data/inventory.json') as db:
        user = db.search(Query().user == user_id)[0]
        characters = user.get('trading_cards')
        if characters is not None and character in characters:
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
    with TinyDB('./data/inventory.json') as db:
        db.update({'trading_cards': cards}, Query().user == user_id)


def add_char(user_id, char):
    user_dict = search(user_id)
    temp_chars = user_dict[0]['chars']

    for characters in temp_chars:
        if characters[0] == char:
            if characters[2] < 6:
                characters[2] += 1
                with TinyDB('./data/inventory.json') as db:
                    db.update({'chars': temp_chars}, Query().user == user_id)
                return
            else:
                add_card(user_id, char)
                return

    temp_chars.append((char, 0, 0))
    with TinyDB('./data/inventory.json') as db:
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
    with TinyDB('./data/inventory.json') as db:
        db.update({'books': temp_books}, Query().user == user_id)


def print_all():
    with TinyDB('./data/inventory.json') as db:
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
        for index, char in enumerate(inv.get('chars')):
            rarity = self.char_lib.find_character(char[0], 'rarity')
            embed.add_field(name=f'{index+1}. {char[0]}', value=f'Rarity {rarity}:star:\nLevel {char[1]}\n Const. {char[2]}',
                            inline=True)
        await ctx.send(embed=embed)

        embed = discord.Embed(title="And other stuff!", colour=color)
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

        await ctx.send('reply to this message with a number to check a specific character in your inventory!')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.reference is not None:
            replied_msg = message.reference.cached_message
            if replied_msg is not None and replied_msg.author.bot and replied_msg.content == 'reply to this message with a number to check a specific character in your inventory!':
                embed = discord.Embed(title='your character', color=discord.Color(random.randint(0, 0xFFFFFF)))
                embed.set_author(name=message.author.display_name)
                with TinyDB('./data/inventory.json') as db:
                    doc = db.search(Query().user == message.author.id)[0]
                    characters = doc.get('chars')
                    if (not message.content.isdigit()) or 0 >= int(message.content) > len(characters):
                        await message.channel.send('invalid number')
                        return
                    char = characters[int(message.content)+1]
                    char_info = self.char_lib.find_character(char_name=char[0])
                    embed.add_field(name='Name', value=char[0])
                    embed.add_field(name='Rarity', value=str(char_info[1]) + ':star:')
                    embed.add_field(name='Affiliation', value=char_info[2])
                    level = 0
                    embed.add_field(name='Attack', value=str(int(char_info[3]+char_info[5] * level)))
                    embed.add_field(name='Health', value=str(int(char_info[4] + char_info[6] * level)))
                    file = discord.File(f'./img/char_portrait/Character_{char[0]}_Portrait.png', filename="char.png")
                    embed.set_image(url="attachment://char.png")
                await message.channel.send(file=file, embed=embed)


def setup(client):
    client.add_cog(InventoryDatabase(client))
