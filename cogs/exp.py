import os

import discord
from discord.ext import commands
import random
from datetime import datetime

from discord.ext.commands import has_permissions

from util import udb
from util.pillow import Pillow


class Exp(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.vc = {}
        self.db = udb.UserDatabase(client)
        self.pillow = Pillow(self.client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Exp online')

    @commands.Cog.listener()
    async def on_message(self, message):
        now = datetime.now()
        _id = message.author.id
        record = self.db.find_user(db='users', user=str(_id))
        if record is None:
            if not message.author.bot:
                await self.db.insert(db='users', init_val=f"({str(_id)}, 0, 160, '{now.strftime('%H:%M:%S')}', '')")
        else:
            last = datetime.strptime(record[3], '%H:%M:%S')
            tdelta = now - last
            if message.content[:1] == '.' or tdelta.seconds < random.randrange(45, 60):
                return
            val = random.randrange(6, 8)

            if message.channel.id != 703247498508238938:
                await self.db.update(db='users', var='pts', amount='+' + str(val), user=str(_id))
            await self.db.update(db='users', var='bal', amount='+' + str(val), user=str(_id))
            await self.db.set_time(db='users', user=str(_id))

        moons = message.guild.get_role(706989660244541540)
        planets = message.guild.get_role(709910163879886917)
        stars = message.guild.get_role(698255109406326876)
        if moons in message.author.roles:
            old_role = message.guild.get_role(706989660244541540)
        elif planets in message.author.roles:
            old_role = message.guild.get_role(709910163879886917)
        else:
            old_role = message.guild.get_role(698255109406326876)
        temp = self.db.top_six('pts')
        temp = [temp[0][0], temp[1][0], temp[2][0], temp[3][0], temp[4][0], temp[5][0]]
        if record is None:
            return
        if record[1] <= 700 and old_role is not moons:
            await message.author.add_roles(moons)
            await message.author.remove_roles(old_role)
        elif _id in temp and old_role is not stars:
            await message.author.add_roles(stars)
            await message.author.remove_roles(old_role)
        elif record[1] >= 700 and old_role.id is not planets:
            await message.author.add_roles(planets)
            await message.author.remove_roles(old_role)

    @commands.command()
    @has_permissions(manage_guild=True)
    async def init_roles(self, ctx):
        # for member in ctx.guild.members:
        #     if not member.bot:
        #         await member.remove_roles(ctx.guild.get_role(698255109406326876))
        #         await member.remove_roles(ctx.guild.get_role(709910163879886917))
        #         await member.add_roles(ctx.guild.get_role(706989660244541540))
        await self.db.set('users', 'pts', '0', None)
        await ctx.send('done')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, prev, cur):
        if member.bot:
            return
        if prev.channel is None:
            self.vc[member.id] = datetime.now()
        elif cur.channel is None:
            tdelta = datetime.now() - self.vc.pop(member.id)
            val = int(tdelta.seconds / 30)
            await self.db.update(db='users', var='pts', amount='+' + str(val), user=str(member.id))
            await self.db.update(db='users', var='bal', amount='+' + str(val), user=str(member.id))

    # commands
    @commands.command()
    async def bal(self, ctx):
        if len(ctx.message.mentions) == 0:
            temp = self.db.find_user(db='users', user=str(ctx.author.id), var='bal')
            pronoun = 'Your'
        else:
            member = ctx.message.mentions[0]
            temp = self.db.find_user(db='users', user=str(member.id), var='bal')
            pronoun = member.display_name + "'s"

        if temp is None:
            await ctx.send("this person does not have a nom nom stash")
        else:
            await ctx.send(f"{pronoun} current balance is: {str(temp[0])} nom noms :cookie:")

    @commands.command(aliases=['lb', 'xp_lb', 'pts_lb'])
    async def leaderboard(self, ctx):
        await ctx.channel.send(embed=await self.db.lb('pts'))

    @commands.command()
    async def bal_lb(self, ctx):
        embed_var = await self.db.lb('bal')
        bal = self.db.find_user('users', str(ctx.author.id), var='bal')
        total = self.db.find('users', 'SUM(bal)')
        embed_var.add_field(name='You', value=f'own {str(format(bal[0] / total[0] * 100, ".2f"))}% '
                                              f'of the nom noms in the server!')
        await ctx.channel.send(embed=embed_var)

    @commands.command()
    async def profile(self, ctx):
        if len(ctx.message.mentions) > 0:
            user = ctx.guild.fetch_member(ctx.message.mentions[0].id)
        else:
            user = ctx.author

        if f'{user.id}.jpg' not in os.listdir('./img/pfp'):
            await user.avatar_url.save(f'./img/pfp/{user.id}.jpg')

        await ctx.send('Generating...', delete_after=3)
        self.pillow.generate_profile(user)

        await ctx.send(file=discord.File('./img/profile.png'))

    @commands.command(aliases=['setdesc', 'setdescription', 'set_description'])
    async def set_desc(self, ctx, *, param):
        if '"' in param:
            await ctx.send('Sorry, you cannot use quotation marks in your description ;-;')
            return
        if len(param) > 450:
            await ctx.send('Please limit your description to be under 450 characters')
            return
        await self.db.set('users', 'description', f'"{param}"', str(ctx.author.id))
        await ctx.send("Description updated <:nekocheer:804178590094327878>")


def setup(client):
    client.add_cog(Exp(client))
