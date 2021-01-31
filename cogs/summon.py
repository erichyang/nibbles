from datetime import datetime
import random

import discord
from discord.ext import commands, tasks

from util import udb, gdb, pillow


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
    @commands.command(aliases=['wish_event'])
    async def event_char_wish(self, ctx, amount):
        amount = int(amount)
        if not await self._wish_check_bal(ctx.author.id, amount):
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return

        categories = await self.rarity_calc(ctx.author.id, 'event', amount)
        await ctx.send(self._wish_results(categories))

    @commands.command(aliases=['wish_reg'])
    async def reg_wish(self, ctx, amount):
        if not self._wish_check_bal(ctx.author.id, amount):
            await ctx.send(f'you cannot afford {amount} summon{"" if amount == 1 else "s"}!')
            return

    def _wish_results(self, categories):
        results = []
        for _ in range(categories[0]):
            if random.random() >= 0.5:
                results.append(self.gdb.cur5)
            else:
                options = self.gdb.fives[:]
                options.remove(self.gdb.cur5)
                results.append(random.choice(options))
        for _ in range(categories[1]):
            if random.random() >= 0.5:
                random.choice(self.gdb.cur4)
            else:
                options = self.gdb.fours[:]
                options.remove(self.gdb.cur4)
                results.append(random.choice(options))
        for _ in range(categories[2]):
            results.append('xp_book')
        return results

    async def _wish_check_bal(self, user_id: int, amount: int):
        user = self.udb.find_user(db='users', user=str(user_id), var='bal')
        if int(user[0]) <= amount * 160:
            return False
        else:
            return True

    async def rarity_calc(self, user_id, banner, num: int):
        five_stars = 0
        four_stars = 0
        xp_books = 0

        pity5 = self.gdb.find_user('users', str(user_id), var=banner + '_pity5')
        pity4 = self.gdb.find_user('users', str(user_id), var=banner + '_pity4')

        for i in range(num):
            val = random.random()

            if banner == 'char' or 'reg':
                five_chance = 0.0006 if pity5 <= 75 else 0.324
            else:
                five_chance = 0.006 if pity5 <= 65 else 0.324

            if val <= five_chance or pity5 >= 90:
                five_stars += 1
                pity5 = 0
                pity4 += 1
                continue
            val = random.random()
            if val <= 0.051 or four_stars >= 10:
                four_stars += 1
                pity4 = 0
                pity5 += 1
            else:
                xp_books += 1
                pity4 += 1
                pity5 += 1

        await self.gdb.set('users', f'{banner}_pity5', str(pity5), str(user_id))
        await self.gdb.set('users', f'{banner}_pity4', str(pity4), str(user_id))
        return [five_stars, four_stars, xp_books]


def setup(client):
    client.add_cog(Summon(client))
