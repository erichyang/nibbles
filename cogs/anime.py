import asyncio
import math
import random
import time
from functools import lru_cache

import discord
from discord.ext.commands import CommandInvokeError, BadArgument
from jikanpy import Jikan, APIException

from tinydb import TinyDB, Query
from discord.ext import commands, tasks
from util import server_manage, udb
from util.idb import quick_sort


def anime_db(user_id, item):
    # item is either anime_list, wishlist, inventory
    with TinyDB('./data/anime.json') as db:
        doc = db.search(Query().user == user_id)
        if len(doc) > 0:
            return doc[0].get(item)
        else:
            return


def anime_inventory_add(user_id, character_id):
    # relation friendship - True, romance - False
    profile_exists(user_id)
    with TinyDB('./data/anime.json') as db:
        inventory = db.search(Query().user == user_id)[0]['inventory']
        inventory.append({'mal_id': character_id, 'affection': 0, 'relationship': None})
        db.update({'inventory': inventory}, Query().user == user_id)


def profile_exists(user_id):
    with TinyDB('./data/anime.json') as db:
        profile = db.search(Query().user == user_id)
        if len(profile) == 0:
            db.insert({'user': user_id, 'anime_list': [], 'wishlist': [], 'inventory': []})
            return False
        return True


def _parse_about(about, item):
    index = about.find(item)
    parse = about[index:].partition('\\n')[0]
    if len(parse) > 50:
        parse = about[index:].partition('\n')[0]
    return parse


def unarr(pings):
    if len(pings) == 0:
        return ''
    output = pings[0]
    for member in pings[1:]:
        output += f', {member}'
    return output


class Anime(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.udb = udb.UserDatabase(client)
        self.server = server_manage.ServerManage(client)
        self.cache = {}
        self.jikan = Jikan()
        self.interactions = []
        self.genshin_db = client.get_cog('Characters')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Anime online')
        self.anime_char_timer.start()

    @lru_cache(maxsize=256)
    def mal_character(self, mal_id):
        try:
            char = self.jikan.character(mal_id)
        except APIException:
            time.sleep(1)
            char = self.jikan.character(mal_id)
        time.sleep(0.5)
        return char

    @lru_cache(maxsize=256)
    def mal_anime(self, mal_id):
        try:
            anime = self.jikan.anime(mal_id)
        except APIException:
            time.sleep(1)
            anime = self.jikan.anime(mal_id)
        time.sleep(0.5)
        return anime

    @tasks.loop(minutes=45)
    async def anime_char_timer(self):
        for channel in await self.server.anime_channels():
            await self.anime_char_spawn(channel)
        self.interactions = []

    async def anime_char_spawn(self, channel):
        log = await self.client.fetch_channel(819271204468031508)
        await log.send('starting timer')
        await asyncio.sleep(random.randint(0, 900))
        await log.send('attempting anime character send to ' + channel.name)
        chatters = []
        async for message in channel.history(limit=100):
            if message.author.id not in chatters:
                chatters.append(message.author.id)
        animes = []
        for user_id in chatters:
            doc = anime_db(user_id, 'anime_list')
            if doc is None or len(doc) == 0:
                continue
            for anime_id in doc:
                if anime_id not in animes:
                    animes.append(anime_id)
        image = 'https://cdn.myanimelist.net/images/questionmark_23.gif?s=f7dcbc4a4603d18356d3dfef8abd655c'
        anime = {}
        char = {}
        c_id = -1

        # await asyncio.sleep(20)
        while 'questionmark_23' in image or 'apple-touch-icon' in image:
            try:
                if len(animes) < 10:
                    return
                anime = self.mal_anime(random.choice(animes))
                c_id = random.choice(self.jikan.anime(anime['mal_id'], extension='characters_staff')['characters'])[
                    'mal_id']
                char = self.mal_character(c_id)
            except APIException:
                await asyncio.sleep(60)
                anime = self.mal_anime(random.choice(animes))
                c_id = random.choice(self.jikan.anime(anime['mal_id'], extension='characters_staff')['characters'])[
                    'mal_id']
                char = self.mal_character(c_id)
            image = char['image_url']

        price = math.log2(anime['members'] + 1) * 50
        price += math.log2(char['member_favorites'] + 1) * 400
        price = int(price)
        desc = f"{anime['title']}\nAnime Members: {anime['members']}\nFavorite by {char['member_favorites']}\n" \
               f"React 🍪 to claim for {price} nom noms!"
        embed = discord.Embed(title=f"**{char['name']}**", description=desc)
        embed.set_image(url=image)
        embed.set_footer(text=str(c_id))
        pings = []
        with TinyDB('./data/anime.json') as db:
            docs = db.search(Query().wishlist.all([c_id]))
        for user in docs:
            user = self.client.get_user(user['user'])
            if user in channel.members:
                pings.append(user.mention)

        msg = await channel.send(content=f'Anime character appearance!\n{unarr(pings)}', embed=embed, delete_after=1800)
        await msg.add_reaction('🍪')
        await log.send(f'character sent to {channel.name}')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.author.bot and len(reaction.message.embeds) == 1:
            profile_exists(user_id=user.id)
            if reaction.emoji == '🍪':
                embed = reaction.message.embeds[0]
                channel = reaction.message.channel
                cost = int(embed.description.split(' ')[-3])
                if self.udb.find_user('users', str(user.id), 'bal')[0] < cost:
                    return
                try:
                    inventory = anime_db(user.id, 'inventory')
                except IndexError:
                    return
                mal_id = int(embed.footer.text)
                if inventory is not None and any(char['mal_id'] == mal_id for char in inventory):
                    flag = True
                    claimed = -1
                    reward = int(cost*0.5)
                    messages = await channel.history(limit=50).flatten()
                    for i, msg in reversed(list(enumerate(messages))):
                        if msg.author == self.client.user and msg.content == f'**{user.mention}** earned {reward} 🍪s!':
                            claimed = 50-i
                            break
                    if claimed != -1:
                        flag = False
                        for msg in messages[claimed+1:]:
                            if 'Anime character appearance!' in msg.content:
                                flag = True
                                break

                    if flag:
                        await self.udb.update('users', 'bal', f'+{reward}', user.id)
                        await channel.send(f'**{user.mention}** earned {reward} 🍪s!')
                    return

                await reaction.message.delete()
                await self.udb.update('users', 'bal', f'-{cost}', user.id)

                anime_inventory_add(user.id, mal_id)
                await channel.send(f'**{user.name}** claimed [{mal_id}] {reaction.message.embeds[0].title} '
                                   f'for {cost} nom noms!')
            elif reaction.emoji == '⬅' or reaction.emoji == '➡':
                footer = reaction.message.embeds[0].footer.text.split('-')
                sect = int(footer[0])
                user_id = int(footer[1])
                owner = self.client.get_user(user_id)
                if reaction.emoji == '⬅':
                    sect -= 1 if sect > 0 else 0
                else:
                    sect += 1
                await reaction.message.edit(embed=await self.main_inventory_view(owner, sect))
            elif reaction.emoji == '👋':
                c_id = int(reaction.message.embeds[0].footer.text)
                inventory = anime_db(user.id, 'inventory')
                if inventory is None:
                    return
                char = None
                index = -1
                for i, item in enumerate(inventory):
                    if item['mal_id'] == int(c_id):
                        char = item
                        index = i
                        break
                if user.id not in self.interactions and char is not None:
                    gain = random.randint(15, 100)
                    await reaction.message.channel.send(f'You gained {gain} affection!')
                    self.interactions.append(user.id)
                    with TinyDB('./data/anime.json') as db:
                        char['affection'] += gain
                        inventory[index] = char
                        db.update({'inventory': inventory}, Query().user == user.id)
            elif reaction.emoji == '🙌' or reaction.emoji == '💞':
                inventory = anime_db(user.id, 'inventory')
                if inventory is None:
                    return
                c_id = int(reaction.message.embeds[0].footer.text)
                char = None
                index = -1
                for i, item in enumerate(inventory):
                    if item['mal_id'] == int(c_id):
                        char = item
                        index = i
                        break

                if char is not None and char['relationship'] is None:
                    if reaction.emoji == '💞':
                        char['relationship'] = False
                    elif reaction.emoji == '🙌':
                        char['relationship'] = True
                    inventory[index] = char
                    with TinyDB('./data/anime.json') as db:
                        db.update({'inventory': inventory}, Query().user == user.id)
                    await reaction.message.channel.send('Successfully set!')

    @commands.command(description='your list of animes that you would like to appear\n.anime_list', aliases=['al'])
    async def anime_list(self, ctx):
        user = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        if not profile_exists(user.id):
            await ctx.send('Your anime list is currently empty!')
            return
        anime_ids = anime_db(user.id, 'anime_list')
        if anime_ids is None:
            return
        desc = 'When an anime character randomly appears, your list of animes will have a chance to appear!'
        embed = discord.Embed(title=f'My Animes {len(anime_ids)}/10', description=desc)
        al = []
        for item in anime_ids:
            al.append(self.mal_anime(item))

        for anime in al:
            value = f"[Title] {anime['title']}" \
                    f"\n[EN Title] {anime['title_english']}" \
                    f"\n[MyAnimeList]({anime['url']})"
            embed.add_field(name=anime['mal_id'], value=value)

        await ctx.send(embed=embed)

    @commands.command(description='add to your list of animes\n.anime_list_add 14813', aliases=['ala'])
    async def anime_list_add(self, ctx, anime_id: int):
        try:
            self.mal_anime(anime_id)
        except APIException:
            await ctx.send('This anime doesn\'t exist!')
            return
        profile_exists(ctx.author.id)
        current = anime_db(ctx.author.id, 'anime_list')
        if len(current) >= 10:
            await ctx.send('Your anime list is full!')
            return
        if anime_id in current:
            await ctx.send('You already have this anime in your list!')
            return
        with TinyDB('./data/anime.json') as db:
            current.append(anime_id)
            db.update({'anime_list': current}, Query().user == ctx.author.id)
        await ctx.send('Successfully added!')

    @commands.command(description='remove from your list of animes\n.anime_list_remove 11757', aliases=['alr'])
    async def anime_list_remove(self, ctx, anime_id: int):
        current = anime_db(ctx.author.id, 'anime_list')
        if current is None:
            await ctx.end("You do not have any animes in your list yet")
            return
        if anime_id in current:
            current.remove(anime_id)
            with TinyDB('./data/anime.json') as db:
                db.update({'anime_list': current}, Query().user == ctx.author.id)
            await ctx.send('Anime removed successfully')
        else:
            await ctx.send('This anime is not in your list')

    @commands.command(description='look up an anime either by name or ID\n.anime_search 14813; .as SNAFU',
                      aliases=['as'])
    async def anime_search(self, ctx, *, anime_search):
        if anime_search.isdigit():
            try:
                anime = self.mal_anime(anime_search)
            except APIException:
                await ctx.send('This anime doesn\'t exist!')
                return
            desc = f"\n[Title] {anime['title']}\n[EN Title] {anime['title_english']}\n[Score] {anime['score']}\n" \
                   f"[Members] {anime['members']}\n[Rank] {anime['rank']}\n[MyAnimeList]({anime['url']})\n" \
                   f"[List of Characters]({anime['url']}/characters)"
            embed = discord.Embed(title=anime_search, description=desc)
            if anime['url'] is not None:
                embed.set_image(url=anime['image_url'])
            await ctx.send(embed=embed)
        else:
            anime_results = self.jikan.search('anime', anime_search)
            content = "Anime Search Results - use .as <anime ID> for a more detailed view of each Anime!\n"
            count = 0
            for anime in anime_results['results']:
                count += 1
                if count == 11:
                    break
                content += f"\n[**{anime['mal_id']}**] {anime['title']}"
            await ctx.send(content)

    async def main_inventory_view(self, user, sect):
        if not profile_exists(user.id):
            return
        inventory = anime_db(user.id, 'inventory')
        quick_sort(inventory, 0, len(inventory) - 1,
                   lambda x, y: ((x['affection'] == y['affection']) and x['mal_id'] > y['mal_id']) or
                   x['affection'] < y['affection'])
        with TinyDB('./data/anime.json') as db:
            db.update({'inventory': inventory}, Query().user == user.id)
        if (len(inventory) / 15) < sect:
            sect -= 1
        cl = []
        start_index = 15 * sect
        end_index = 15 + 15 * sect
        if end_index >= len(inventory):
            end_index = len(inventory)
        for item in inventory[start_index:end_index]:
            character = self.mal_character(item['mal_id'])
            cl.append((character['mal_id'], character['name'], item['affection'], item['relationship']))
        desc = ""
        for tup in cl:
            desc += f"[{tup[0]}] {tup[1]} - {tup[2]}"
            if tup[3] is None:
                heart = '♥'
            elif tup[3]:
                heart = '💖'
            else:
                heart = '💕'

            desc += f"{heart}\n"

        embed = discord.Embed(title=f"{user.name}'s adventure party", description=desc)
        embed.set_footer(text=f'{sect}-{user.id}')
        return embed

    @commands.command(description='a list of all the anime characters you own!\n.anime_inventory', aliases=['ainv'])
    async def anime_inventory(self, ctx):
        if len(ctx.message.mentions) > 0:
            embed = await self.main_inventory_view(ctx.message.mentions[0], 0)
        else:
            embed = await self.main_inventory_view(ctx.author, 0)
        if embed is None:
            await ctx.send('This inventory is currently empty!')
        else:
            msg = await ctx.send(embed=embed)
            await msg.add_reaction('⬅')
            await msg.add_reaction('➡')

    @commands.command(aliases=['achar'], description='Look up an anime character by name or ID. '
                                                     'Quickly access the top of your inventory with A-E. '
                                                     'Name search term must be longer than three characters.\n'
                                                     'If a character is not found here, use the cast of characters '
                                                     'from the description of the anime using .al <ID> to find your '
                                                     'character. Sowwy for the inconvenience.\n'
                                                     '.anime_character Kanna Kamui; .achar 170466; .achar A')
    async def anime_character(self, ctx, *, character_id):
        if character_id in ['A', 'B', 'C', 'D', 'E']:
            inventory = anime_db(ctx.author.id, 'inventory')
            if inventory is None:
                return
            index = ord(character_id) - ord('A')
            if inventory[index] is not None:
                character_id = inventory[index]['mal_id']
        elif not character_id.isdigit():
            if len(character_id) <= 3:
                await ctx.send("Please search for a name that is longer than three letters")
                return
            try:
                anime_results = self.jikan.search('character', character_id)
            except APIException:
                await ctx.send('This query could not locate any results')
                return
            anime_results = anime_results['results']
            content = "Anime Character Search Results - use .achar <MAL ID> for a detailed view of this character!\n"
            count = 0
            for anime in anime_results:
                count += 1
                if count == 11:
                    break
                content += f"\n[**{anime['mal_id']}**] {anime['name']}"
            await ctx.send(content)
            return

        try:
            character = self.mal_character(character_id)
        except APIException:
            await ctx.send('Sorry, nibbles cannot find this character right now, pls try again later?')
            return
        about_var = []
        if 'Age: ' in character['about']:
            about_var.append(_parse_about(character['about'], 'Age: '))
        if 'Birthday: ' in character['about']:
            about_var.append(_parse_about(character['about'], 'Birthday: '))
        if 'Height: ' in character['about']:
            about_var.append(_parse_about(character['about'], 'Height: '))
        if 'Weight: ' in character['about']:
            about_var.append(_parse_about(character['about'], 'Weight: '))
        if 'Affiliation: ' in character['about']:
            about_var.append(_parse_about(character['about'], 'Affiliation: '))
        about = ''
        for var in about_var:
            about += var + '\n'
        desc = f"Favorite by {character['member_favorites']} members\n{about}\n[MyAnimeList profile]({character['url']})"
        embed = discord.Embed(title=f"**{character['name']}** {character['name_kanji']}", description=desc)
        inventory = anime_db(ctx.author.id, 'inventory')
        if inventory is None:
            return
        char = next((x for x in inventory if x['mal_id'] == int(character_id)), None)
        if char is not None:
            lvl = self.genshin_db.level_calc(char['affection'] * 1000)[0]
            relationship = 'strangers'

            if char['relationship'] is None or lvl < 60:
                if lvl >= 40:
                    relationship = 'casual friends'
                elif lvl >= 20:
                    relationship = 'acquaintances'
            elif char['relationship']:
                if lvl >= 70:
                    relationship = 'besties'
                else:
                    relationship = 'close friends'
            elif not char['relationship']:
                if lvl >= 90:
                    relationship = 'married'
                elif lvl >= 80:
                    relationship = 'engaged'
                elif lvl >= 70:
                    relationship = 'dating'
                else:
                    relationship = 'interested'
            title = 'Affection'
            if char['relationship'] is None:
                pass
            elif char['relationship']:
                title = 'Friendship'
            else:
                title = 'Romance'
            embed.add_field(name=f'{title} - {relationship}', value=f"{char['affection']}♥")
            if char['relationship'] is None:
                embed.add_field(name='React 🙌 or 💞', value='to choose between friendship or romance, respectively. '
                                                             'Choose wisely, you only get this choice once per character!')
            # multiplier of 1000 for converting between genshin and anime levels
            # 0 - strangers
            # 20 - acquaintances
            # 40 - casual friends
            # friendship
            # 60 - close friends
            # 70 - besties
            # romance
            # 60 - interested
            # 70 - dating
            # 80 - engaged
            # 90 - married
        embed.set_image(url=character['image_url'])
        embed.set_footer(text=character_id)
        msg = await ctx.send(embed=embed)
        if char is not None:
            await msg.add_reaction('👋')
            if char['relationship'] is None:
                await msg.add_reaction('🙌')
                await msg.add_reaction('💞')

    @commands.command(description='give an anime character you have claimed to someone else\n.give 118739 @bit',
                      aliases=['give'])
    async def anime_give(self, ctx, c_id: int):
        inventory = anime_db(ctx.author.id, 'inventory')
        if inventory is None:
            return
        char = None
        index = -1
        for i, item in enumerate(inventory):
            if item['mal_id'] == int(c_id):
                char = item
                index = i
                break
        recipient = ctx.message.mentions[0]
        recip_inv = anime_db(recipient.id, 'inventory')
        if char is not None and recip_inv is not None and recipient is not ctx.author and \
                not any(other['mal_id'] == c_id for other in recip_inv):
            inventory.pop(index)
            char['affection'] = 0
            char['relationship'] = None
            recip_inv.append(char)
            with TinyDB('./data/anime.json') as db:
                db.update({'inventory': inventory}, Query().user == ctx.author.id)
                db.update({'inventory': recip_inv}, Query().user == recipient.id)
            await ctx.send('Done!')
            return
        await ctx.send('The gift process failed.')

    @commands.command(description=
                      'kick an anime character from your adventure party, receive a portion of the initial cost back\n'
                      '.remove 169181', aliases=['akick'])
    async def anime_character_kick(self, ctx, c_id):
        inventory = anime_db(ctx.author.id, 'inventory')
        if inventory is None:
            return
        char = None
        index = -1
        refund = int(math.log2(self.mal_character(c_id)['member_favorites'] + 1) * 400)
        for i, item in enumerate(inventory):
            if item['mal_id'] == int(c_id):
                char = item
                index = i
                break
        if char is not None:
            inventory.pop(index)
            with TinyDB('./data/anime.json') as db:
                db.update({'inventory': inventory}, Query().user == ctx.author.id)

            await self.udb.update('users', 'bal', f'+{refund}', ctx.author.id)
            await ctx.send(f'Refunded {refund} nom noms')

    @anime_inventory.error
    @anime_list.error
    @anime_list_add.error
    @anime_search.error
    @anime_inventory.error
    @anime_character.error
    async def rate_limit_error(self, ctx, error):
        if isinstance(error, CommandInvokeError) and hasattr(error.original, 'error_json') and \
                error.original.error_json['type'] == 'RateLimitException':
            await ctx.send('Rate limited to not offend MAL, please try again in 30s <:KaiCry:778399319086596106>')
        elif isinstance(error, ValueError) or isinstance(error, BadArgument):
            await ctx.send('<:HuTaoRip:833535556759191572> did you gib nibbles an ID?')
        else:
            channel = await self.client.fetch_channel(819271204468031508)
            await channel.send(error)

    @commands.command(aliases=['wl'], description='Sometimes wishes do come true. (mentions you if a wish appears)')
    async def wish_list(self, ctx):
        user = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        if not profile_exists(user.id):
            await ctx.send('Your wish list is currently empty!')
            return
        anime_ids = anime_db(user.id, 'wishlist')
        if anime_ids is None:
            return
        desc = 'When your wished anime character randomly appears, you will be notified!'
        embed = discord.Embed(title=f'My Wishlist {len(anime_ids)}/4', description=desc)
        al = []
        for item in anime_ids:
            al.append(self.mal_character(item))

        inventory = anime_db(user.id, 'inventory')

        for anime in al:
            value = f"[Name] {anime['name']}" \
                    f"\n[Favorites] {anime['member_favorites']}" \
                    f"\n[MyAnimeList]({anime['url']})"
            owned = ''
            if any(char['mal_id'] == anime['mal_id'] for char in inventory):
                owned = ' ✅'
            embed.add_field(name=str(anime['mal_id']) + owned, value=value)

        await ctx.send(embed=embed)

    @commands.command(description='add to your wish list\n.wish_list_add 136728', aliases=['wla'])
    async def wish_list_add(self, ctx, c_id: int):
        try:
            self.mal_character(c_id)
        except APIException:
            await ctx.send('This anime character doesn\'t exist!')
            return
        profile_exists(ctx.author.id)
        current = anime_db(ctx.author.id, 'wishlist')
        if len(current) >= 4:
            await ctx.send('Your wish list is full!')
            return
        if c_id in current:
            await ctx.send('You already have this anime in your list!')
            return
        with TinyDB('./data/anime.json') as db:
            current.append(c_id)
            db.update({'wishlist': current}, Query().user == ctx.author.id)
        await ctx.send('Successfully added!')

    @commands.command(description='remove from your wish list\n.wish_list_remove 169181', aliases=['wlr'])
    async def wish_list_remove(self, ctx, anime_id: int):
        current = anime_db(ctx.author.id, 'wishlist')
        if current is None:
            await ctx.end("You do not have any wished characters in your list yet")
            return
        if anime_id in current:
            current.remove(anime_id)
            with TinyDB('./data/anime.json') as db:
                db.update({'wishlist': current}, Query().user == ctx.author.id)
            await ctx.send('Wished character removed successfully')
        else:
            await ctx.send('This character is not in your list')

    @commands.command(description='clear owned from your wish list\n.wish_list_clear', aliases=['wlc'])
    async def wish_list_clear(self, ctx):
        current = anime_db(ctx.author.id, 'wishlist')
        if current is None:
            await ctx.end("You do not have any wished characters in your list yet")
            return
        inventory = anime_db(ctx.author.id, 'inventory')
        count = 0
        for item in inventory:
            if any(item['mal_id'] == char_id for char_id in current):
                current.remove(item['mal_id'])
                count+=1

        with TinyDB('./data/anime.json') as db:
            db.update({'wishlist': current}, Query().user == ctx.author.id)
            await ctx.send(f'All owned characters ({count}) are cleared from your wishlist')


def setup(client):
    client.add_cog(Anime(client))
