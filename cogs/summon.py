import time
from datetime import datetime
import random

import discord
from discord.ext import commands, tasks

from util import udb, gdb, idb, pillow


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.udb = udb.UserDatabase(client)
        self.gdb = gdb.GachaDatabase(client)
        self.idb = idb.InventoryDatabase(client)
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
        embed = discord.Embed(colour=discord.Colour(0xff7cff),
                              description=desc,
                              timestamp=datetime.now())

        img = discord.File('./img/banner.png', 'banner.png')
        temp_channel = await self.client.fetch_channel(752676890413629471)
        msg = await temp_channel.send('', file=img)
        img_url = msg.attachments[0].url
        embed.set_image(url=img_url)

        await channel.send(content='There is a new banner available!', embed=embed)

    @commands.command()
    async def banner(self, ctx):
        await ctx.send(content="Today's banner", file=discord.File('./img/banner.png', 'banner.png'))

    # commands
    @commands.command(aliases=['wish_event', 'summon_event'])
    async def event_wish(self, ctx, amount):
        await self._wish_qual(ctx, int(amount))

        categories = await self._wish_rarity_calc(ctx.author.id, 'event', amount)
        if categories[0] > 0 or categories[1] > 0 and amount == 10:
            await ctx.send(file=discord.File('./img/wish_gifs/purple_ten.gif'), delete_after=5)
        elif categories[0] > 0 or categories[1] > 0 and amount == 1:
            await ctx.send(file=discord.File('./img/wish_gifs/gold.gif'), delete_after=5)
        elif categories[2] > 0 and amount == 10:
            await ctx.send(file=discord.File('./img/wish_gifs/purple_ten.gif'), delete_after=5)
        elif categories[2] > 0 and amount == 1:
            await ctx.send(file=discord.File('./img/wish_gifs/purple.gif'), delete_after=5)
        else:
            await ctx.send(file=discord.File('./img/wish_gifs/blue.gif'), delete_after=5)

        results = self._wish_event_results(categories)
        self.pillow.generate_wishes(results)
        time.sleep(5)
        await ctx.send(file=discord.File('./img/results.png'))

        for item in results:
            if 'book' in item:
                self.idb.add_book(ctx.author.id, item)
            else:
                self.idb.add_char(ctx.author.id, item)

    @commands.command(aliases=['wish_reg', 'summon_reg'])
    async def reg_wish(self, ctx, amount):
        await self._wish_qual(ctx, int(amount))

        categories = await self._wish_rarity_calc(ctx.author.id, 'reg', amount)
        if categories[0] > 0 and amount == 10:
            await ctx.send(file=discord.File('./img/wish_gifs/purple_ten.gif'), delete_after=5)
        elif categories[0] > 0 and amount == 1:
            await ctx.send(file=discord.File('./img/wish_gifs/gold.gif'), delete_after=5)
        elif categories[1] > 0 and amount == 10:
            await ctx.send(file=discord.File('./img/wish_gifs/purple_ten.gif'), delete_after=5)
        elif categories[1] > 0 and amount == 1:
            await ctx.send(file=discord.File('./img/wish_gifs/purple.gif'), delete_after=5)
        else:
            await ctx.send(file=discord.File('./img/wish_gifs/blue.gif'), delete_after=5)

        results = self._wish_reg_results(categories)
        self.pillow.generate_wishes(results)
        time.sleep(5)
        await ctx.send(file=discord.File('./img/results.png'))

        for item in results:
            if 'book' in item:
                self.idb.add_book(ctx.author.id, item)
            else:
                self.idb.add_char(ctx.author.id, item)

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
                random.choice(self.gdb.cur4)
            else:
                options = self.gdb.fours[:]
                options.remove(self.gdb.cur4)
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

    async def _wish_check_bal(self, user_id: int, amount: int):
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
        event_guarantee = self.gdb.find_user('users', str(user_id), 'event_guarantee')[0]
        pity5 = self.gdb.find_user('users', str(user_id), var=banner + '_pity5')
        pity4 = self.gdb.find_user('users', str(user_id), var=banner + '_pity4')

        for i in range(num):
            val = random.random()

            five_chance = 0.0006 if pity5 < 75 else 0.324

            if val <= five_chance or pity5 >= 90:
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
            if val <= 0.0255 or four_stars >= 10:
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

    async def _wish_qual(self, ctx, amount):
        if amount != 1 or amount != 10:
            await ctx.send('please only do 1 or 10 pulls.')
            return
        if not await self._wish_check_bal(ctx.author.id, amount):
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return
        if self.idb.search(ctx.author.id) is None:
            await self.idb.create_user(ctx.author.id)
            await self.gdb.insert('users', f'({ctx.author.id}, 0, 0, 0, 0, 0)')


def setup(client):
    client.add_cog(Summon(client))
