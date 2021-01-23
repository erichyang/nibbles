import discord
from discord.ext import commands
import random
from datetime import datetime
from cogs import db


class Exp(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.vc = {}
        self.db = db.DataBase(client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Exp online')

    @commands.Cog.listener()
    async def on_message(self, message):
        now = datetime.now()
        _id = message.author.id
        record = await self.db.find_user(db='users', user=str(_id))
        if record is None:
            if not message.author.bot:
                await self.db.insert(db='users', init_val='({0}, 0, 160, {1})'.format(str(_id),
                                                                                      now.strftime('%H:%M:%S')))
        else:
            last = datetime.strptime(record[3], '%H:%M:%S')
            tdelta = now - last
            if message.content[:1] == '.' or tdelta.seconds < random.randrange(45, 60):
                return
            val = random.randrange(6, 8)

            await self.db.update(db='users', var='pts', amount='+' + str(val), user=str(_id))
            await self.db.update(db='users', var='bal', amount='+' + str(val), user=str(_id))
            await self.db.set_time(db='users', user=str(_id))

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
        member = ctx.message.mentions[0]
        if member is None:
            temp = await self.db.find_user(db='users', user=str(ctx.author.id), var='bal')
            pronoun = 'Your'
        else:
            temp = await self.db.find_user(db='users', user=str(member.id), var='bal')
            pronoun = member.display_name + "'s"

        if temp is None:
            await ctx.send("this person does not have a nom nom stash")
        else:
            await ctx.send("{} current balance is: {} nom noms :cookie:".format(pronoun, str(temp[0])))

    @commands.command()
    async def leaderboard(self, ctx):
        await ctx.channel.send(embed=await self.db.lb('pts'))

    @commands.command()
    async def bal_lb(self, ctx):
        await ctx.channel.send(embed=await self.db.lb('bal'))


def setup(client):
    client.add_cog(Exp(client))
