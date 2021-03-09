import os

import discord
from discord.ext import commands
import random
from datetime import datetime

from discord.ext.commands import has_permissions
from tinydb import TinyDB, Query

from util import udb, idb
from util.pillow import Pillow

import re


class Exp(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.vc = {}
        self.db = udb.UserDatabase(client)
        self.idb = idb.InventoryDatabase(client)
        self.pillow = Pillow(self.client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Exp online')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        now = datetime.now()
        _id = message.author.id
        record = self.db.find_user(db='users', user=str(_id))
        if record is None:
            if not message.author.bot:
                await self.db.insert(db='users', init_val=f"({str(_id)}, 0, 160, '{now.strftime('%H:%M:%S')}', '')")
        else:
            if len(message.content) < 2:
                return
            last = datetime.strptime(record[3], '%H:%M:%S')
            tdelta = now - last
            if message.content[0] == '.' or tdelta.seconds < random.randrange(45, 60):
                return
            val = random.randrange(6, 8)

            if message.channel.id != 703247498508238938 and message.guild.id == 607298393370394625:
                await self.db.update(db='users', var='pts', amount='+' + str(val), user=str(_id))
            await self.db.update(db='users', var='bal', amount='+' + str(val), user=str(_id))
            await self.db.set_time(db='users', user=str(_id))
            await self.idb.chat_primary_xp(message)

        if record is not None and not isinstance(message.author, discord.User):
            temp = self.db.top_six('pts')
            top_six = []
            for person in temp:
                top_six.append(person[0])
            temp = self.db.top_eighteen()
            top_et = []
            for person in temp:
                top_et.append(person[0])
            await self.manage_exp_roles(message, record[1], top_six, top_et)

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def reset_pts(self, ctx):
        if ctx.guild.id != 607298393370394625:
            return
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
            _id = member.id
            record = self.db.find_user(db='users', user=str(_id))
            now = datetime.now()
            if record is None:
                if not member.bot:
                    await self.db.insert(db='users', init_val=f"({str(_id)}, 0, 160, '{now.strftime('%H:%M:%S')}', '')")

            await self.db.update(db='users', var='pts', amount='+' + str(val), user=str(member.id))
            await self.db.update(db='users', var='bal', amount='+' + str(val), user=str(member.id))

    # commands
    @commands.command(description='count the nom noms in your stash, ooo so many <:wow:788914745008586763>\n.bal')
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

    @commands.command(aliases=['lb', 'xp_lb', 'pts_lb'], description='check the top ten people with the highest points!'
                                                                     '\n.leaderboard; .lb; .xp_lb; .pts_lb')
    async def leaderboard(self, ctx):
        if ctx.guild.id != 607298393370394625:
            await ctx.send('sowwy but leaderboard is only available in Project Void')
            return
        await ctx.send(embed=await self.db.lb('pts', ctx.guild))

    @commands.command(description='check your profile that has your exp and nom noms!\n.profile; .profile @nibbles')
    async def profile(self, ctx):
        if len(ctx.message.mentions) > 0:
            user = await ctx.guild.fetch_member(ctx.message.mentions[0].id)
        else:
            user = ctx.author

        await ctx.send('Generating...', delete_after=3)
        with TinyDB('./data/birthday.json') as bd:
            birthday_doc = bd.search(Query().user == user.id)
            birthday = 'N/A' if len(birthday_doc) == 0 else birthday_doc[0].get('birthday')
        with TinyDB('./data/inventory.json') as bd:
            character_doc = bd.search(Query().user == user.id)
            if len(character_doc) == 0 or character_doc[0].get('primary') is None:
                prim_char = None
            else:
                prim_char = character_doc[0].get('chars')[character_doc[0].get('primary') - 1]
        await self.pillow.generate_profile(ctx, user, birthday=birthday, prim_char=prim_char)

    @commands.command(aliases=['setdesc', 'setdescription', 'set_description'],
                      description='set your beautiful message to be seen on your profile :D\n.setdesc <message>')
    async def set_desc(self, ctx, *, param):
        if '"' in param:
            await ctx.send('Sorry, you cannot use quotation marks in your description ;-;')
            return
        if len(param) > 450:
            await ctx.send('Please limit your description to be under 450 characters')
            return
        await self.db.set('users', 'description', f'"{param}"', str(ctx.author.id))
        await ctx.send("Description updated <:nekocheer:804178590094327878>")

    @commands.command(aliases=['setbd'],
                      description='set your birthday to be announced on the day and for your profile!\n'
                                  '.set_birthday mm/dd; .setbd 02/14')
    async def set_birthday(self, ctx, birthday):
        pattern = re.compile("^[0-9]{2}/[0-9]{2}$")
        if not pattern.match(birthday):
            await ctx.send('that is not the correct date time format')
            return
        with TinyDB('./data/birthday.json') as bd:
            if bd.search(Query().user == ctx.author.id):
                await ctx.send('you already set your birthday! If you have made an error, contact an admin')
                return
            bd.insert({'user': ctx.author.id, 'birthday': birthday})
        await ctx.send('your birthday is now set as ' + birthday)

    @staticmethod
    async def manage_exp_roles(message, xp, t6, t18):
        if message.guild.id != 607298393370394625:
            return
        moons = message.guild.get_role(706989660244541540)
        planets = message.guild.get_role(709910163879886917)
        stars = message.guild.get_role(698255109406326876)

        if xp >= 1000 and message.author.id in t6:
            await message.author.add_roles(stars)
            if planets in message.author.roles:
                await message.author.remove_roles(planets)
            if moons in message.author.roles:
                await message.author.remove_roles(moons)
        elif xp >= 500 and message.author.id in t18:
            await message.author.add_roles(planets)
            if stars in message.author.roles:
                await message.author.remove_roles(stars)
            if moons in message.author.roles:
                await message.author.remove_roles(moons)
        else:
            await message.author.add_roles(moons)
            if stars in message.author.roles:
                await message.author.remove_roles(stars)
            if planets in message.author.roles:
                await message.author.remove_roles(planets)


def setup(client):
    client.add_cog(Exp(client))
