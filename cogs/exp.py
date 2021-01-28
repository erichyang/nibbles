import discord
from discord.ext import commands
import random
from datetime import datetime
from cogs import udb


class Exp(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.vc = {}
        self.db = udb.UserDatabase(client)

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
        embed_var.add_field(name='You', value=f'own {str(format(bal[0]/total[0]*100, ".2f"))}% '
                                              f'of the nom noms in the server!')
        await ctx.channel.send(embed=embed_var)

    @commands.command()
    async def profile(self, ctx):
        if len(ctx.message.mentions) > 0:
            user_id = ctx.message.mentions[0].id
        else:
            user_id = ctx.author.id
        user = self.client.get_user(user_id)
        pfp = user.avatar_url

        user_info = self.db.find_user(db='users', user=str(user_id))

        if user_info[4] == '' or user_info[4] is None:
            desc = 'This user has not set a description yet.'
        else:
            desc = user_info[4]

        embed = discord.Embed(colour=discord.Colour(0xff9cd0), description=desc,
                              timestamp=datetime.utcfromtimestamp(1611799584))

        embed.set_thumbnail(url=pfp)
        embed.set_author(name=f"{user.display_name}'s Profile")

        embed.add_field(name="EXP:", value=user_info[1], inline=True)
        embed.add_field(name="Nom Noms:", value=user_info[2], inline=True)

        await ctx.send(embed=embed)

    @commands.command(aliases=['setdesc', 'setdescription', 'set_description'])
    async def set_desc(self, ctx, *, param):
        await self.db.set('users', 'description', f"'{param}'", str(ctx.author.id))
        await ctx.send('Description updated <:nekocheer:804178590094327878>')


def setup(client):
    client.add_cog(Exp(client))
