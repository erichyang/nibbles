import asyncio
from threading import Thread

import discord

import time
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import has_permissions, cooldown, BucketType, CommandOnCooldown
import random

from util import udb, idb


def _bj_total(hand):
    val = 0
    num_ace = 0
    for card in hand:
        if card[0] == 1:
            num_ace += 1
            val += 1
        elif card[0] == 11 or card[0] == 12 or card[0] == 13:
            val += 10
        else:
            val += card[0]
    dist = 21 - val

    while dist > num_ace*10 and num_ace > 0:
        val += 10
        num_ace -= 1
        dist = 21-val
    return val


def _bj_display(hand, opp_hand):
    output = ''
    for card in hand:
        if card[0] == 1:
            output += 'A'
        elif card[0] == 11:
            output += 'J'
        elif card[0] == 12:
            output += 'Q'
        elif card[0] == 13:
            output += 'K'
        else:
            output += str(card[0])
        output += ':' + card[1] + ': '

    if opp_hand[0][0] == 1:
        o_output = 'A'
    elif opp_hand[0][0] == 11:
        o_output = 'J'
    elif opp_hand[0][0] == 12:
        o_output = 'Q'
    elif opp_hand[0][0] == 13:
        o_output = 'K'
    else:
        o_output = str(opp_hand[0][0])
    return output, o_output + ':' + opp_hand[0][1] + ': ' + str(len(opp_hand) - 1) + 'x:flower_playing_cards:'


class Gamble(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.bj = {}
        self.wheel = []
        self.db = udb.UserDatabase(client)
        self.idb = idb.InventoryDatabase(client)
        self.servers = client.get_cog('ServerManage')

    async def announce_wheel(self, channels):
        for channel in channels:
            await channel.send('Your free wheel of fortune is now available!')
        self.wheel = []

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def give_bal(self, ctx, user, amount):
        if self.db.find_user(db='users', user=user) is None:
            await ctx.send("Sowwy, this person does not have a nom noms stash")
            return

        await self.db.update(db='users', var='bal', amount='+' + str(amount), user=str(user))
        await ctx.send('given ' + str(amount))

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def give_exp(self, ctx, user, amount):
        if self.db.find_user(db='users', user=user) is None:
            await ctx.send("Sowwy, this person does not have a nom noms stash")
            return

        await self.db.update(db='users', var='pts', amount='+' + str(amount), user=str(user))
        await ctx.send('given ' + str(amount))

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Gamble online')

    # commands
    @commands.command(aliases=['cf', 'bet_flip', 'bet_coin'],
                      description='flip a coin with the face you predict and how much you want to bet for it\n'
                                  '.gamble_coin heads 160; .bet_coin tails 320')
    @cooldown(20, 30, BucketType.user)
    async def gamble_coin(self, ctx, face='heads', bet='0'):
        _id = ctx.author.id

        if bet == 'all':
            bet = self.db.find_user(db='users', user=str(_id), var='bal')
            bet = bet[0]
        else:
            bet = int(bet)

        if bet > 1600:
            await ctx.send("Please don't gamble more than 1600, nibbles can't count all these nom noms")
            return
        if bet <= 0:
            await ctx.send('The coin showed ' + random.choice(['heads!', 'tails!']))
            return
        bal = self.db.find_user(db='users', user=str(_id), var='bal')
        if bal[0] < bet:
            await ctx.send("You don't have enough nom noms to be gambling, you current balance is " + str(bal))
            return
        if face not in ['heads', 'tails']:
            await ctx.send("That is not heads or tails! ")
            return
        result = random.choice(['heads', 'tails'])
        bet = str(bet)
        if face == result:
            await ctx.send('You won! The coin showed ' + result)
            await ctx.send('You gain ' + bet + ' nom noms')
            await self.db.update(db='users', var='bal', amount='+' + str(bet), user=str(_id))
        else:
            await ctx.send('You lost! The coin showed ' + result)
            await ctx.send('You lost ' + bet + ' nom noms')
            await self.db.update(db='users', var='bal', amount='-' + str(bet), user=str(_id))

    @gamble_coin.error
    async def gamble_coin_error(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.send(f'please wait {error.retry_after:,.2f} seconds before using coin flip again')
            await ctx.send('do you want to reconsider your bet?')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild is not None and msg.guild.id == 819061920652591105:
            return
        if msg.author.id not in self.wheel and not msg.author.bot and msg.guild is not None:
            if len(msg.content) > 0 and msg.content[0] != '.':
                await self.gamble_wheel(msg.author, msg.channel)

    async def gamble_wheel(self, author, channel):
        # if ctx.channel.id == 681149093858508834:
        #     await ctx.send(f'the wheel of fortune belongs in {self.client.get_channel(752676890413629471).mention}!')
        #     await ctx.send('<:angy:789977140200341515>')
        #     return
        bal = self.db.find_user(db='users', var='bal', user=str(author.id))

        self.wheel.append(author.id)

        embed = discord.Embed(title="**SPINNING**", colour=discord.Colour(random.randint(0, 0xFFFFFF)))
        embed.set_image(url="https://cdn.discordapp.com/attachments/703247498508238938/800820068426317854/wheel.gif")
        embed.set_thumbnail(url=author.avatar_url)
        embed.set_author(name=str(author))
        embed.set_footer(text="best of luck!", icon_url="https://cdn.discordapp.com/emojis/747848187192148048.png?v=1")

        msg = await channel.send(content="Spinning the Wheel of Fortune", embed=embed, delete_after=75)

        result = random.randint(1, 100)
        prize = 150
        if result <= 1:
            prize = 10000
        elif 2 <= result <= 3:
            prize = 5000
        elif 90 < result <= 100:
            prize = 400
        elif 80 < result <= 90:
            prize = 320
        elif 70 < result <= 80:
            prize = 240
        elif 50 <= result <= 60:
            prize = 160
        elif 40 <= result <= 50:
            prize = 80

        embed = discord.Embed(title="**REWARDS**", colour=discord.Colour(random.randint(0, 0xFFFFFF)))
        embed.set_thumbnail(url=author.avatar_url)
        embed.set_author(name=str(author))
        embed.add_field(name="Prize", value=str(prize) + " nom noms", inline=False)
        embed.add_field(name="Current Balance", value=str(bal[0] + prize), inline=False)

        await asyncio.sleep(4)
        await self.db.update(db='users', var='bal', amount='+' + (str(prize)), user=str(author.id))
        await msg.edit(content='Wheel of Fortune Results', embed=embed)

    @commands.command(description='give your money to someone else, but why would you do that if you could give them '
                                  'all to nibbles\n.transfer @kit 160')
    async def transfer(self, ctx, amount):
        receiver_id = ctx.message.mentions[0].id
        sender_id = ctx.author.id
        if isinstance(amount, str) and amount[:1] == '<':
            item = ctx.message.content.split(' ')[2]
            await self.transfer(ctx, item)
            return
        if amount.isdigit():
            amount = int(amount)
        # hard code hu tao name
        if amount == "Hu":
            amount = "Hu Tao"
        if isinstance(amount, str):
            if len(idb.search(receiver_id)) == 0:
                await ctx.send("The receiver has not created an inventory yet! Please start by summoning. ")
                return
            if idb.transfer_card(sender_id, amount) == 'done':
                idb.add_char(receiver_id, amount)
                await ctx.send("sent " + amount + " to " + ctx.message.mentions[0].display_name)
            else:
                await ctx.send("You do not have this card transferable")
            return
        else:
            amount = int(amount)

        if int(amount) <= 0:
            await ctx.send("hey you can't do that")
            return

        sender_bal = self.db.find_user(db='users', user=str(sender_id), var='bal')

        sender_bal = sender_bal[0]
        if sender_bal < int(amount):
            await ctx.send('You do not have enough nom noms to give!')
            return
        if self.db.find_user(db='users', user=str(receiver_id)) is None:
            await ctx.send("Sowwy, this person does not have a nom noms stash")
            return

        await self.db.update(db='users', var='bal', amount='-' + str(amount), user=str(sender_id))
        await self.db.update(db='users', var='bal', amount='+' + str(amount), user=str(receiver_id))
        await ctx.send("Done!")

    @commands.command(hidden=True)
    @has_permissions(manage_guild=True)
    async def reset_blackjack(self, ctx):
        self.bj = {}
        await ctx.send('black jack has been reset')

    @commands.command(aliases=['gamble_blackjack', 'blackjack', 'bj'],
                      description='bet against any player that accepts the challenge by playing black_jack\n'
                                  '.gamble_black_jack 160; .blackjack 320 @nibbles')
    async def gamble_black_jack(self, ctx, amount):
        if 'msg' in self.bj:
            await ctx.send('there is already a black jack game going on!')
            return

        if int(amount) < 0:
            await ctx.send('No you will not get money from losing')
            return
        temp = self.db.find_user(db='users', user=str(ctx.author.id), var='bal')
        if temp[0] < int(amount):
            await ctx.send('Hey you don\'t have that much nom noms!')
            return

        self.bj = {}
        msg = await ctx.send("click the reaction to accept the black jack challenge", delete_after=300)
        await msg.add_reaction('<:hi:813575402512580670>')
        self.bj['init'] = ctx.author
        self.bj['bet'] = int(amount)
        self.bj['msg'] = msg

        if len(ctx.message.mentions) > 0 and ctx.message.mentions[0] != ctx.author:
            self.bj['challenged'] = ctx.message.mentions[0]

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if 'msg' in self.bj and message.author.id == 736013645045301301:
            msg = self.bj['msg']
            if msg.id == message.id:
                self.bj.pop('msg', None)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if 'chal' not in self.bj and not user.bot and 'init' in self.bj and user.id != self.bj['init'].id \
                and 'msg' in self.bj and reaction.message == self.bj['msg']:
            if 'challenged' in self.bj and user != self.bj['challenged']:
                return

            user_bal = self.db.find_user(db='users', user=str(user.id), var='bal')
            user_bal = user_bal[0]
            if user_bal < self.bj['bet']:
                await reaction.message.channel.send("Hey " + user.display_name + ", you don't have that much nom noms!")
                return

            await reaction.message.clear_reactions()
            await reaction.message.edit(content='Black Jack battle between ' + self.bj['init'].display_name + ' and ' +
                                                user.display_name + ' for :cookie: ' + str(self.bj['bet']))
            self.bj['chal'] = user
            self._bj_deck()

            temp1 = ''
            temp2 = ''
            for i in range(2):
                temp1 += self._bj_hit('init')
                temp2 += self._bj_hit('chal')

            if 'stay' in temp1:
                await self._bj_end('init')
            if 'stay' in temp2:
                await self._bj_end('chal')

            await self._bj_send_dm('init')
            await self._bj_send_dm('chal')
        if not user.bot and 'init_msg' in self.bj and reaction.message == self.bj['init_msg']:
            if 'init_end' in self.bj:
                return
            if reaction.emoji == '👊':
                if self._bj_hit('init') == 'stay':
                    await self._bj_end('init')
                await self._bj_send_dm('init')
            elif reaction.emoji == '✋':
                await self._bj_end('init')
        if not user.bot and 'chal_msg' in self.bj and reaction.message == self.bj['chal_msg']:
            if 'chal_end' in self.bj:
                return
            if reaction.emoji == '👊':
                if self._bj_hit('chal') == 'stay':
                    await self._bj_end('chal')
                await self._bj_send_dm('chal')
            elif reaction.emoji == '✋':
                await self._bj_end('chal')

    async def _bj_send_dm(self, user: str):
        if user == 'init':
            embed = discord.Embed(title='Black Jack Battle',
                                  colour=discord.Colour(0xFF0000),
                                  description="Use the two reactions to either hit or stay\nonce both players stayed "
                                              "or busted, \nthe game ends\n:punch: for hit and :raised_hand: for stay",
                                  timestamp=datetime.now())
            embed.set_thumbnail(url=self.bj['chal'].avatar_url)
            embed.set_author(name=self.bj['chal'].display_name,
                             icon_url="https://cdn.discordapp.com/emojis/765130388032192552.png?v=1")

            output = _bj_display(self.bj['init_hand'], self.bj['chal_hand'])
            embed.add_field(name="Your Hand", value=output[0], inline=True)
            embed.add_field(name="Their Hand", value=output[1], inline=True)
            self.bj['init_msg'] = await self.bj['init'].send(content="Defeat your opponent!", embed=embed)
            await self.bj['init_msg'].add_reaction('👊')
            await self.bj['init_msg'].add_reaction('✋')

        if user == 'chal':
            embed = discord.Embed(title='Black Jack Battle',
                                  colour=discord.Colour(0x0000FF),
                                  description="Use the two reactions to either hit or stay\nonce both players stayed "
                                              "or busted, \nthe game ends\n:punch: for hit and :raised_hand: for stay",
                                  timestamp=datetime.now())
            embed.set_thumbnail(url=self.bj['init'].avatar_url)
            embed.set_author(name=self.bj['init'].display_name,
                             icon_url="https://cdn.discordapp.com/emojis/765130388032192552.png?v=1")
            output = _bj_display(self.bj['chal_hand'], self.bj['init_hand'])
            embed.add_field(name="Your Hand", value=output[0], inline=True)
            embed.add_field(name="Their Hand", value=output[1], inline=True)
            self.bj['chal_msg'] = await self.bj['chal'].send(content="Best of luck, Challenger!", embed=embed)
            await self.bj['chal_msg'].add_reaction('👊')
            await self.bj['chal_msg'].add_reaction('✋')

    def _bj_deck(self):
        deck = []
        for suit in ['spades', 'hearts', 'clubs', 'diamonds']:
            for i in range(1, 14):
                deck.append((i, suit))
        random.shuffle(deck)
        self.bj['deck'] = deck

    def _bj_hit(self, user: str):
        if user + '_hand' not in self.bj:
            self.bj[user + '_hand'] = []
        self.bj[user + '_hand'].append(self.bj['deck'].pop())
        if _bj_total(self.bj[user + '_hand']) >= 21:
            return 'stay'
        return ''

    async def _bj_end(self, user):
        self.bj[user + '_end'] = _bj_total(self.bj[user + '_hand'])
        other = 'init' if user != 'init' else 'chal'
        if other + '_end' not in self.bj:
            return
        chnl = self.bj['msg'].channel
        embed = discord.Embed(colour=discord.Colour(random.randint(0, 0xFFFFFF)),
                              description="The results of the game",
                              timestamp=datetime.now())
        embed.set_author(name="Black Jack Battle",
                         icon_url="https://cdn.discordapp.com/emojis/765130388032192552.png?v=1")
        output1, trash = _bj_display(self.bj['init_hand'], [(0, 'placeholder')])
        output2, trash = _bj_display(self.bj['chal_hand'], [(0, 'placeholder')])

        init = self.bj['init_end']
        chal = self.bj['chal_end']
        embed.add_field(name=self.bj['init'].display_name + "'s Hand", value=output1 + "\nTotal score: " + str(init),
                        inline=True)
        embed.add_field(name=self.bj['chal'].display_name + "'s Hand", value=output2 + "\nTotal score: " + str(chal),
                        inline=True)
        if 'final' in self.bj:
            return

        await chnl.send(f'{self.bj[user].mention} {str(self.bj[other].mention)} Both players have finished!')

        if init == chal or (init > 21 and chal > 21) or (init == 21 and chal == 21):
            self.bj['final'] = await chnl.send(content="The two players tied!", embed=embed)
        elif init <= 21 and (init == 21 or chal > 21 or init > chal):
            self.bj['final'] = await chnl.send(content=self.bj['init'].display_name + ' has won the bet!', embed=embed)
            await self.db.update(db='users', var='bal', amount='+' + str(self.bj['bet']), user=str(self.bj['init'].id))
            await self.db.update(db='users', var='bal', amount='-' + str(self.bj['bet']), user=str(self.bj['chal'].id))
        else:
            self.bj['final'] = await chnl.send(content=self.bj['chal'].display_name + ' has won the bet!', embed=embed)
            await self.db.update(db='users', var='bal', amount='+' + str(self.bj['bet']), user=str(self.bj['chal'].id))
            await self.db.update(db='users', var='bal', amount='-' + str(self.bj['bet']), user=str(self.bj['init'].id))

        self.bj.pop('msg', None)


def setup(client):
    client.add_cog(Gamble(client))
