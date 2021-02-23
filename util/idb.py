import math
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


class InventoryDatabase(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.char_lib = Characters(client)
        self.book_select = {}

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
        if 'primary' in inv:
            char_name = inv.get('chars')[inv.get('primary')-1][0]
            primary = 'Primary character: ' + char_name
        else:
            primary = 'No primary character'
        embed = discord.Embed(title=primary, color=color)

        embed.set_author(name=ctx.author.display_name if ctx.author.nick is None else ctx.author.nick)
        for index, char in enumerate(inv.get('chars')):
            rarity = self.char_lib.find_character(char[0], 'rarity')
            embed.add_field(name=f'{index + 1}. {char[0]}',
                            value=f'Rarity {rarity}:star:\nXP {char[1]}\n Const. {char[2]}',
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

    @commands.command(description='navigate to a detailed view of your character without using inventory!\n'
                                  '.character Ganyu')
    async def character(self, ctx, character_name):
        character_name = character_name[0].upper() + character_name[1:]
        arr = search(ctx.author.id)[0].get('chars')
        for index, character in enumerate(arr):
            if character[0] == character_name:
                await self.query_char(ctx.message, index + 1)

    async def query_char(self, message, index=0):
        embed = discord.Embed(title='your character', color=discord.Color(random.randint(0, 0xFFFFFF)))
        embed.set_author(name=message.author.display_name)
        with TinyDB('./data/inventory.json') as db:
            doc = db.search(Query().user == message.author.id)[0]
            characters = doc.get('chars')
            if message.content.isdigit():
                index = int(message.content)
            if 0 >= index > len(characters):
                await message.channel.send('invalid number')
                return
            char = characters[index - 1]
            char_info = self.char_lib.find_character(char_name=char[0])
            embed.add_field(name='Name', value=char[0])
            embed.add_field(name='Rarity', value=str(char_info[1]) + ':star:')
            embed.add_field(name='Affiliation', value=char_info[2])
            level = self.char_lib.level_calc(char[1])[0]
            embed.add_field(name='Attack', value=str(int(char_info[3] + char_info[5] * level)))
            embed.add_field(name='Health', value=str(int(char_info[4] + char_info[6] * level)))
            embed.add_field(name='Level', value=str(level))
            file = discord.File(f'./img/char_portrait/Character_{char[0]}_Portrait.png', filename="char.png")
            embed.set_image(url="attachment://char.png")
        content = f'||{message.author.id} {index}||'
        msg = await message.channel.send(content=content, file=file, embed=embed)
        await msg.add_reaction('⬆️')
        await msg.add_reaction('🌟')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.reference is not None:
            replied_msg = message.reference.cached_message
            if replied_msg is not None and replied_msg.author.bot and replied_msg.content == 'reply to this message with a number to check a specific character in your inventory!':
                await self.query_char(message)
        if isinstance(message.channel, discord.channel.DMChannel) and message.author.id in self.book_select:
            if message.content.isdigit():
                msg = self.book_select.get(message.author.id)
                amount = int(message.content)
                with TinyDB('./data/inventory.json') as db:
                    books = db.search(Query().user == message.author.id)[0].get('books')

                flag = True
                if str(msg.reactions[0].emoji) == '<:purple_book:808011829238169630>':
                    book = 'purple'
                    if books[0] < amount:
                        flag = False
                elif str(msg.reactions[0].emoji) == '<:blue_book:808011854558920744>':
                    book = 'blue'
                    if books[1] < amount:
                        flag = False
                else:
                    book = 'green'
                    if books[2] < amount:
                        flag = False
                if not flag:
                    await message.channel.send("you don't have that many books!")
                    return
                await message.channel.send(f'using {amount} {book} books to level up...')
                await message.channel.send('=' + '—-—'*10 + '=')
                char_id = int(msg.content.split('.')[0])
                self.level_up(message.author.id, char_id-1, book, amount)
                await self.level_viewer(message.author, char_id)
                self.book_select.pop(message.author.id)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if str(user.id) in reaction.message.content and reaction.message.author.bot and (not user.bot) \
                and reaction.emoji == '⬆️':
            char_id = int(reaction.message.content.split(' ')[-1][:-2])
            await self.level_viewer(user, char_id)
            return

        if str(user.id) in reaction.message.content and reaction.message.author.bot and (not user.bot) \
                and reaction.emoji == '🌟':
            char_id = int(reaction.message.content.split(' ')[-1][:-2])
            with TinyDB('./data/inventory.json') as db:
                db.update({'primary': char_id}, Query().user == user.id)
                await reaction.message.channel.send('You have set your primary character!')
            return

        purple = '<:purple_book:808011829238169630>'
        blue = '<:blue_book:808011854558920744>'
        green = '<:green_book:808011842328199188>'

        if str(reaction.emoji) in (purple, blue, green) and reaction.message.author.bot and (not user.bot) and \
                isinstance(reaction.message.channel, discord.channel.DMChannel):
            await reaction.message.remove_reaction(emoji=purple, member=self.client.user)
            await reaction.message.remove_reaction(emoji=blue, member=self.client.user)
            await reaction.message.remove_reaction(emoji=green, member=self.client.user)
            await reaction.message.channel.send('How many books would you like to use')
            self.book_select[user.id] = reaction.message

    @staticmethod
    def level_up(user_id, char_id, book_type, amount):
        with TinyDB('./data/inventory.json') as db:
            user_info = db.search(Query().user == user_id)[0]
            books_tuple = user_info.get('books')
            if book_type == 'purple':
                books = [books_tuple[0] - amount, books_tuple[1], books_tuple[2]]
                xp = amount * 20000
            elif book_type == 'blue':
                books = [books_tuple[0], books_tuple[1] - amount, books_tuple[2]]
                xp = amount * 5000
            else:
                books = [books_tuple[0], books_tuple[1], books_tuple[2] - amount]
                xp = amount * 1000
            db.update({'books': books}, Query().user == user_id)
            char_info = user_info.get('chars')
            # print(char_info)
            char_info[char_id][1] += xp
            db.update({'chars': char_info}, Query().user == user_id)

    async def level_viewer(self, user, char_id):
        purple = '<:purple_book:808011829238169630>'
        blue = '<:blue_book:808011854558920744>'
        green = '<:green_book:808011842328199188>'
        embed = discord.Embed(title='Levels')
        with TinyDB('./data/inventory.json') as db:
            doc = db.search(Query().user == user.id)[0]
        # print(doc)
        character = doc.get('chars')[char_id-1]
        xp = character[1]
        level = self.char_lib.level_calc(xp)
        next_ten = int(math.ceil((level[0]+1) / 10.0)) * 10
        embed.add_field(name='Current Level', value=str(level[0]), inline=False)
        # print(level)
        if level[2] != 'MAX':
            proportion = int((float(level[1]) / level[2]) * 10)
            output = '[' + proportion * '▰' + (10 - proportion) * '▱' + ']'
            output += f'\n{level[1]} - {level[2] - level[1]}/{level[2]} left'
            level_ten = self.char_lib.fetch_levels()[next_ten-1]
            proportion = int((float(xp) / level_ten[1]) * 10)
            ten_output = '[' + proportion * '▰' + (10 - proportion) * '▱' + ']'
            ten_output += f'\n{xp} - {level_ten[1] - xp}/{level_ten[1]} left'
        else:
            output = 'MAX LEVEL'
            ten_output = 'MAX LEVEL'
        embed.add_field(name='XP until next level', value=output, inline=False)

        embed.add_field(name='XP until level ' + str(next_ten), value=ten_output, inline=False)

        msg = await user.send(f'{char_id}. {character[0]}\nPurple - 20,000 Blue - 5,000 Green - 1,000', embed=embed)
        await msg.add_reaction(purple)
        await msg.add_reaction(blue)
        await msg.add_reaction(green)


def setup(client):
    client.add_cog(InventoryDatabase(client))
