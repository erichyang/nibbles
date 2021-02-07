import time
from datetime import datetime
import random

import discord
from discord.ext import commands, tasks
from tinydb import TinyDB, Query

from util import udb, gdb, idb, pillow


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.udb = udb.UserDatabase(client)
        self.gdb = gdb.GachaDatabase(client)
        self.pillow = pillow.Pillow(client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Summon online')

    # repeat every 24 hours
    @tasks.loop(hours=24)
    async def new_banner_rotation(self):
        channel = await self.client.fetch_channel(681149093858508834)
        five, four = self.client.get_cog('GachaDatabase').new_banner()
        desc = '5:star: ' + five + f'\n4:star: {four[0]}, {four[1]}, {four[2]}'
        self.pillow.generate_banner(five, four)
        embed = discord.Embed(colour=discord.Colour(random.randint(0, 0xFFFFFF)),
                              description=desc,
                              timestamp=datetime.now())

        img = discord.File('./img/banner.png', 'banner.png')
        temp_channel = await self.client.fetch_channel(752676890413629471)
        msg = await temp_channel.send('', file=img)
        img_url = msg.attachments[0].url
        embed.set_image(url=img_url)

        await channel.send(embed=embed)

        today = datetime.now().strftime("%m/%d")
        with TinyDB('./data/birthday.json') as _db:
            for people in _db.search(Query().birthday == today):
                await channel.send(f"It is {channel.guild.get_member(people['user']).mention}'s birthday today!")
                await channel.send(f"You received 14400 nom noms!")
                await self.udb.update('users', 'bal', '+14400', str(people['user']))

    @commands.command(description='Find out the banner for today!\n.banner')
    async def banner(self, ctx):
        await ctx.send(content="Today's banner", file=discord.File('./img/banner.png', 'banner.png'))

    # commands
    @commands.command(aliases=['wish_event', 'summon_event'],
                      description='wish for new characters and levels on the rotating event banner at a price of 160 '
                                  'nom noms each\nwish_event 1; .event_wish 10; .summon_event 10')
    async def event_wish(self, ctx, amount):
        amount = int(amount)
        if len(idb.search(ctx.author.id)) == 0:
            idb.create_user(ctx.author.id)
        if self.gdb.find_user('users', str(ctx.author.id)) is None:
            await self.gdb.insert('users', f'({ctx.author.id}, 0, 0, 0, 0, 0)')
        if not (0 <= amount <= 10):
            await ctx.send('please only do 1-10 pulls.')
            return
        if not self._wish_check_bal(ctx.author.id, amount):
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return
        embed = discord.Embed()
        categories = await self._wish_rarity_calc(ctx.author.id, 'event', amount)
        if categories[0] > 0 or categories[1] > 0 and amount >= 5:
            embed.set_image(url="https://media.giphy.com/media/4Q38sALn5Gl48s7Jv3/giphy.gif")
        elif categories[0] > 0 or categories[1] > 0 and amount < 5:
            embed.set_image(url="https://media.giphy.com/media/X1oxDDQYMNx3RBYXkc/giphy.gif")
        elif categories[2] > 0 and amount >= 5:
            embed.set_image(url="https://media.giphy.com/media/U04NUo8yZy20GohN4U/giphy.gif")
        elif categories[2] > 0 and amount < 5:
            embed.set_image(url="https://media.giphy.com/media/2mSCyZFXmHS2RQT4LF/giphy.gif")
        else:
            embed.set_image(url="https://media.giphy.com/media/Cj6L4uLFEfsV2iJjq3/giphy.gif")

        await ctx.send(embed=embed, delete_after=5)
        results = self._wish_event_results(categories)
        self.pillow.generate_wishes(results)
        time.sleep(3)
        await ctx.send(file=discord.File('./img/results.png'))

        await self.udb.update('users', 'bal', '-'+str(160*amount), str(ctx.author.id))
        for item in results:
            if 'book' in item:
                idb.add_book(ctx.author.id, item)
            else:
                idb.add_char(ctx.author.id, item)

    @commands.command(aliases=['wish_reg', 'summon_reg'],
                      description='wish for new characters and levels on the rotating event banner at a price of 160 '
                                  'nom noms each\nwish_reg 1; .summon_reg 10')
    async def reg_wish(self, ctx, amount):
        amount = int(amount)
        if len(idb.search(ctx.author.id)) == 0:
            idb.create_user(ctx.author.id)
        if self.gdb.find_user('users', str(ctx.author.id)) is None:
            await self.gdb.insert('users', f'({ctx.author.id}, 0, 0, 0, 0, 0)')
        if not (amount == 1 or 10):
            await ctx.send('please only do 1 or 10 pulls.')
            return
        if not self._wish_check_bal(ctx.author.id, amount):
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return

        categories = await self._wish_rarity_calc(ctx.author.id, 'reg', amount)
        embed = discord.Embed()

        if categories[0] > 0 and amount >= 5:
            embed.set_image(url="https://media.giphy.com/media/4Q38sALn5Gl48s7Jv3/giphy.gif")
        elif categories[0] > 0 and amount < 5:
            embed.set_image(url="https://media.giphy.com/media/X1oxDDQYMNx3RBYXkc/giphy.gif")
        elif categories[1] > 0 and amount >= 5:
            embed.set_image(url="https://media.giphy.com/media/U04NUo8yZy20GohN4U/giphy.gif")
        elif categories[1] > 0 and amount < 5:
            embed.set_image(url="https://media.giphy.com/media/2mSCyZFXmHS2RQT4LF/giphy.gif")
        else:
            embed.set_image(url="https://media.giphy.com/media/Cj6L4uLFEfsV2iJjq3/giphy.gif")

        await ctx.send(embed=embed, delete_after=5)
        results = self._wish_reg_results(categories)
        self.pillow.generate_wishes(results)
        time.sleep(3)
        await ctx.send(file=discord.File('./img/results.png'))

        await self.udb.update('users', 'bal', '-' + str(160 * amount), str(ctx.author.id))

        for item in results:
            if 'book' in item:
                idb.add_book(ctx.author.id, item)
            else:
                idb.add_char(ctx.author.id, item)

    def _wish_event_results(self, categories):
        results = []
        for _ in range(categories[0]):
            results.append(self.gdb.cur5)
        for _ in range(categories[1]):
            options = self.gdb.fives[:]
            options.remove(self.gdb.cur5)
            results.append(random.choice(options))
        for _ in range(categories[2]):
            if random.random() >= 0.5:
                results.append(random.choice(self.gdb.cur4))
            else:
                options = self.gdb.fours[:]
                for option in self.gdb.cur4:
                    options.remove(option)
                results.append(random.choice(options))
        for _ in range(categories[3]):
            results.append(random.choice(['green_book', 'blue_book', 'purple_book']))
        return results

    def _wish_reg_results(self, categories):
        results = []
        for _ in range(categories[0]):
            options = self.gdb.fives[:]
            results.append(random.choice(options))
        for _ in range(categories[1]):
            options = self.gdb.fours[:]
            results.append(random.choice(options))
        for _ in range(categories[2]):
            results.append(random.choice(['green_book', 'blue_book', 'purple_book']))
        return results

    def _wish_check_bal(self, user_id: int, amount: int):
        user = self.udb.find_user(db='users', user=str(user_id), var='bal')
        if int(user[0]) <= amount * 160:
            return False
        else:
            return True

    async def _wish_rarity_calc(self, user_id, banner, num: int):
        five_event = 0
        five_nonevent = 0
        four_stars = 0
        xp_books = 0
        event_guarantee = self.gdb.find_user('users', str(user_id), 'event_guarantee')
        if event_guarantee is None:
            event_guarantee = 0

        pity5 = self.gdb.find_user('users', str(user_id), var=banner + '_pity5')
        pity5 = 0 if pity5 is None else pity5

        pity4 = self.gdb.find_user('users', str(user_id), var=banner + '_pity4')
        pity4 = 0 if pity4 is None else pity4

        event_guarantee = False if event_guarantee == 0 else True

        for i in range(num):
            val = random.random()

            five_chance = 0.0006 if pity5 < 74 else 0.324

            if val <= five_chance or pity5 >= 89:
                if banner == 'event':
                    if event_guarantee or random.random() >= 0.5:
                        five_event += 1
                        event_guarantee = False
                    else:
                        five_nonevent += 1
                        event_guarantee = True
                else:
                    five_event += 1
                pity5 = 0
                pity4 += 1
                continue
            val = random.random()
            if val <= 0.0255 or pity4 >= 9:
                four_stars += 1
                pity4 = 0
                pity5 += 1
            else:
                xp_books += 1
                pity4 += 1
                pity5 += 1

        await self.gdb.set('users', f'{banner}_pity5', str(pity5), str(user_id))
        await self.gdb.set('users', f'{banner}_pity4', str(pity4), str(user_id))
        if banner == 'event':
            await self.gdb.set('users', 'event_guarantee', '1' if event_guarantee else '0', str(user_id))
            return [five_event, five_nonevent, four_stars, xp_books]
        else:
            return [five_event, four_stars, xp_books]

    @commands.command(description='Check the amount of pity you have on each banner\n.pity')
    async def pity(self, ctx):
        info = self.gdb.find_user('users', str(ctx.author.id))
        if info is None:
            await ctx.send("you haven't summoned yet!")
            return
        embed = discord.Embed(title="Your pity for banner wishes!", colour=discord.Colour(random.randint(0, 0xFFFFFF)))

        embed.set_author(name=ctx.author.display_name if ctx.author.nick is None else ctx.author.nick)
        temp_eg = 'You are not guaranteed the event character for your next five star' if info[1] == 0 \
            else 'You are guaranteed the next five star as event character!'
        embed.add_field(name="Event Five :star: Guarantee", value=temp_eg, inline=False)
        embed.add_field(name="Event Five :star: Pity", value=str(info[2]), inline=True)
        embed.add_field(name="Event Four :star: Pity", value=str(info[4]), inline=True)
        embed.add_field(name="Regular Five :star: Pity", value=str(info[3]), inline=True)
        embed.add_field(name="Regular Four :star: Pity", value=str(info[1]), inline=True)

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Summon(client))
